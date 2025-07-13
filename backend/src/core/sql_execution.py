import asyncio
import time
from typing import Any, Optional, Tuple

import boto3
from botocore.exceptions import NoCredentialsError

from src.core.iam_service import get_iam_service
from src.core.settings import APP_SETTINGS


class SQLExecutionService:
    """Service for executing SQL queries on various platforms"""

    def __init__(self, user_context: Optional[dict[str, Any]] = None):
        self.database = APP_SETTINGS.AWS_ATHENA_DATABASE
        self.workgroup = APP_SETTINGS.AWS_ATHENA_WORKGROUP
        self.output_location = APP_SETTINGS.AWS_ATHENA_OUTPUT_LOCATION
        self.timeout = APP_SETTINGS.AWS_ATHENA_TIMEOUT
        self.user_context = user_context or {}

        if APP_SETTINGS.is_aws:
            self._initialize_aws_clients()

    def _initialize_aws_clients(self):
        """Initialize AWS clients for Athena and related services"""
        if not self.output_location:
            raise ValueError("AWS_ATHENA_OUTPUT_LOCATION must be configured")

        try:
            self.athena_client = boto3.client(
                "athena",
                aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
                region_name=APP_SETTINGS.AWS_REGION,
            )

            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
                region_name=APP_SETTINGS.AWS_REGION,
            )

            self.glue_client = boto3.client(
                "glue",
                aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
                region_name=APP_SETTINGS.AWS_REGION,
            )

            # If user context is provided, try to use user's IAM role
            if self.user_context and "cognito_user_id" in self.user_context:
                self._initialize_user_role_clients()

        except NoCredentialsError:
            raise Exception("AWS credentials not found")

    def _initialize_user_role_clients(self):
        """Initialize AWS clients using user's IAM role"""
        try:
            # Get user's IAM role ARN
            iam_service = get_iam_service()
            if iam_service:
                user_id = self.user_context["cognito_user_id"]
                username = self.user_context["username"]

                role_info = iam_service.get_user_role_info(user_id, username)

                if role_info["success"]:
                    # Assume the user's role for better security
                    sts_client = boto3.client(
                        "sts",
                        aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
                        region_name=APP_SETTINGS.AWS_REGION,
                    )

                    assumed_role = sts_client.assume_role(
                        RoleArn=role_info["role_arn"],
                        RoleSessionName=f"QueryPilot-{username}",
                        ExternalId=user_id,
                    )

                    credentials = assumed_role["Credentials"]

                    # Override clients with user role credentials
                    self.athena_client = boto3.client(
                        "athena",
                        aws_access_key_id=credentials["AccessKeyId"],
                        aws_secret_access_key=credentials["SecretAccessKey"],
                        aws_session_token=credentials["SessionToken"],
                        region_name=APP_SETTINGS.AWS_REGION,
                    )

                    self.s3_client = boto3.client(
                        "s3",
                        aws_access_key_id=credentials["AccessKeyId"],
                        aws_secret_access_key=credentials["SecretAccessKey"],
                        aws_session_token=credentials["SessionToken"],
                        region_name=APP_SETTINGS.AWS_REGION,
                    )

                    self.glue_client = boto3.client(
                        "glue",
                        aws_access_key_id=credentials["AccessKeyId"],
                        aws_secret_access_key=credentials["SecretAccessKey"],
                        aws_session_token=credentials["SessionToken"],
                        region_name=APP_SETTINGS.AWS_REGION,
                    )

                    print(f"Using user role: {role_info['role_arn']}")

        except Exception as e:
            print(f"Warning: Could not assume user role, using default credentials: {e}")

    async def execute_query(self, sql_query: str) -> dict[str, Any]:
        """
        Execute SQL query and return results

        Args:
            sql_query (str): SQL query to execute

        Returns:
            Dict containing query results, metadata, and execution info
        """
        if not APP_SETTINGS.is_aws:
            raise ValueError("SQL execution service requires AWS environment")

        return await self._execute_athena_query(sql_query)

    async def _execute_athena_query(self, sql_query: str) -> dict[str, Any]:
        """Execute SQL query on AWS Athena"""
        start_time = time.time()

        try:
            # Clean and validate SQL query
            cleaned_sql = self._clean_sql_query(sql_query)

            # Start query execution
            response = self.athena_client.start_query_execution(
                QueryString=cleaned_sql,
                QueryExecutionContext={"Database": self.database},
                ResultConfiguration={"OutputLocation": self.output_location},
                WorkGroup=self.workgroup,
            )

            query_execution_id = response["QueryExecutionId"]

            # Wait for query completion
            execution_result = await self._wait_for_query_completion(query_execution_id)

            if execution_result["QueryExecution"]["Status"]["State"] == "SUCCEEDED":
                # Get query results
                results = await self._get_query_results(query_execution_id)

                execution_time = time.time() - start_time

                return {
                    "status": "success",
                    "execution_id": query_execution_id,
                    "execution_time": execution_time,
                    "data": results["data"],
                    "columns": results["columns"],
                    "row_count": len(results["data"]),
                    "column_count": len(results["columns"]),
                    "sql_query": cleaned_sql,
                    "data_scanned_bytes": execution_result["QueryExecution"]["Statistics"].get(
                        "DataScannedInBytes", 0
                    ),
                    "engine_execution_time": execution_result["QueryExecution"]["Statistics"].get(
                        "EngineExecutionTimeInMillis", 0
                    ),
                }
            else:
                error_reason = execution_result["QueryExecution"]["Status"].get(
                    "StateChangeReason", "Unknown error"
                )
                return {
                    "status": "error",
                    "execution_id": query_execution_id,
                    "execution_time": time.time() - start_time,
                    "error": error_reason,
                    "sql_query": cleaned_sql,
                }

        except Exception as e:
            return {
                "status": "error",
                "execution_time": time.time() - start_time,
                "error": str(e),
                "sql_query": sql_query,
            }

    async def _wait_for_query_completion(self, query_execution_id: str) -> dict[str, Any]:
        """Wait for Athena query to complete"""
        max_wait_time = self.timeout
        wait_time = 0

        while wait_time < max_wait_time:
            response = self.athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            status = response["QueryExecution"]["Status"]["State"]

            if status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
                return response

            # Wait before next check
            await asyncio.sleep(1)
            wait_time += 1

        raise TimeoutError(f"Query execution timed out after {max_wait_time} seconds")

    async def _get_query_results(self, query_execution_id: str) -> dict[str, Any]:
        """Get query results from Athena"""
        try:
            response = self.athena_client.get_query_results(QueryExecutionId=query_execution_id)

            result_set = response["ResultSet"]

            # Extract column names
            columns = []
            if "ColumnInfos" in result_set["ResultSetMetadata"]:
                columns = [col["Name"] for col in result_set["ResultSetMetadata"]["ColumnInfos"]]

            # Extract data rows
            data = []
            rows = result_set["Rows"]

            # Skip header row if present
            data_rows = rows[1:] if len(rows) > 1 else []

            for row in data_rows:
                row_data = {}
                for i, col_name in enumerate(columns):
                    if i < len(row["Data"]):
                        value = row["Data"][i].get("VarCharValue", "")
                        # Try to convert to appropriate type
                        row_data[col_name] = self._convert_value(value)
                    else:
                        row_data[col_name] = None
                data.append(row_data)

            return {"columns": columns, "data": data}

        except Exception as e:
            raise Exception(f"Error retrieving query results: {str(e)}")

    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type"""
        if value == "" or value is None:
            return None

        # Try to convert to number
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Try to convert to boolean
        if value.lower() in ["true", "false"]:
            return value.lower() == "true"

        # Return as string
        return value

    def _clean_sql_query(self, sql_query: str) -> str:
        """Clean and validate SQL query"""
        # Remove common formatting issues
        sql_query = sql_query.strip()

        # Remove trailing semicolon if present
        if sql_query.endswith(";"):
            sql_query = sql_query[:-1]

        # Basic validation - ensure it's a SELECT statement
        if not sql_query.upper().strip().startswith("SELECT"):
            raise ValueError("Only SELECT statements are allowed")

        return sql_query

    def get_database_schema(self) -> dict[str, Any]:
        """Get database schema from Glue Catalog"""
        if not APP_SETTINGS.is_aws:
            raise ValueError("Schema retrieval requires AWS environment")

        try:
            # Get all tables in the database
            response = self.glue_client.get_tables(DatabaseName=self.database)

            schema = {"database": self.database, "tables": []}

            for table in response["TableList"]:
                table_info = {"name": table["Name"], "columns": []}

                for column in table["StorageDescriptor"]["Columns"]:
                    table_info["columns"].append(
                        {
                            "name": column["Name"],
                            "type": column["Type"],
                            "comment": column.get("Comment", ""),
                        }
                    )

                schema["tables"].append(table_info)

            return schema

        except Exception as e:
            raise Exception(f"Error retrieving database schema: {str(e)}")

    def validate_query_against_schema(self, sql_query: str) -> Tuple[bool, str]:
        """Validate SQL query against the database schema"""
        if not APP_SETTINGS.is_aws:
            return False, "Schema validation requires AWS environment"

        try:
            # Get schema
            schema = self.get_database_schema()

            # Extract table names from schema
            available_tables = {table["name"].lower() for table in schema["tables"]}

            # Basic validation - check if referenced tables exist
            sql_upper = sql_query.upper()

            # Simple table name extraction (can be improved)
            words = sql_upper.split()
            from_index = -1

            for i, word in enumerate(words):
                if word == "FROM":
                    from_index = i
                    break

            if from_index != -1 and from_index + 1 < len(words):
                table_name = words[from_index + 1].lower().strip(",")
                if table_name not in available_tables:
                    return False, f"Table '{table_name}' not found in database"

            return True, "Query validation passed"

        except Exception as e:
            return False, f"Error validating query: {str(e)}"

    def check_service_health(self) -> dict[str, Any]:
        """Check the health of SQL execution service"""
        if not APP_SETTINGS.is_aws:
            return {
                "status": "not_configured",
                "message": "SQL execution service requires AWS environment",
            }

        try:
            # Test basic connectivity
            self.glue_client.get_databases()

            # Get schema info for health check
            schema = self.get_database_schema()

            return {
                "status": "healthy",
                "database": self.database,
                "workgroup": self.workgroup,
                "tables_count": len(schema.get("tables", [])),
                "tables": [table["name"] for table in schema.get("tables", [])],
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global SQL execution service instance
sql_execution_service = None


def get_sql_execution_service(
    user_context: Optional[dict[str, Any]] = None,
) -> Optional[SQLExecutionService]:
    """Get SQL execution service instance with user context"""
    # Always create a new instance with user context for security
    if APP_SETTINGS.is_aws:
        try:
            return SQLExecutionService(user_context=user_context)
        except Exception as e:
            print(f"Failed to initialize SQL execution service: {e}")
            return None
    else:
        # For local environment, use global instance
        global sql_execution_service
        if sql_execution_service is None:
            try:
                sql_execution_service = SQLExecutionService()
            except Exception as e:
                print(f"Failed to initialize SQL execution service: {e}")
                return None
        return sql_execution_service
