import os
import sqlite3
import time
from typing import Any, Optional

from src.core.settings import APP_SETTINGS
from src.nl2sql.dail_sql.utils.utils import get_tables_from_db


def get_backend_directory() -> str:
    """Get the absolute path to the backend directory"""
    # This file is in src/core/, so go up 2 levels to get to backend/
    current_file = os.path.abspath(__file__)
    return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))


class SQLiteService:
    """Service for executing SQL queries on SQLite databases"""

    def __init__(self, db_name: str = "chinook"):
        self.db_name = db_name
        self.db_path = self._get_db_path(db_name)
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"SQLite database not found: {self.db_path}")

    def _get_db_path(self, db_name: str) -> str:
        """Get the full path to a SQLite database"""
        if db_name in APP_SETTINGS.SQLITE_DATABASES:
            db_path = APP_SETTINGS.SQLITE_DATABASES[db_name]
        else:
            db_path = db_name if db_name.endswith('.sqlite') or db_name.endswith('.db') else f"{db_name}.sqlite"
        
        # If path is relative, make it relative to backend directory
        if not os.path.isabs(db_path):
            backend_dir = get_backend_directory()
            db_path = os.path.join(backend_dir, db_path)
        
        return db_path

    def execute_query(self, sql_query: str) -> dict[str, Any]:
        """
        Execute SQL query on SQLite database and return results
        
        Args:
            sql_query (str): SQL query to execute
            
        Returns:
            Dict containing query results, metadata, and execution info
        """
        start_time = time.time()
        
        try:
            # Clean the SQL query
            cleaned_sql = sql_query.strip()
            
            # Connect to SQLite database
            connection = sqlite3.connect(self.db_path)
            connection.row_factory = sqlite3.Row  # Enable column access by name
            cursor = connection.cursor()
            
            # Execute query
            cursor.execute(cleaned_sql)
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Convert rows to list of dictionaries
            data = []
            for row in rows:
                row_dict = {}
                for i, col_name in enumerate(columns):
                    row_dict[col_name] = row[i]
                data.append(row_dict)
            
            cursor.close()
            connection.close()
            
            execution_time = time.time() - start_time
            
            return {
                "status": "success",
                "execution_time": execution_time,
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "column_count": len(columns),
                "sql_query": cleaned_sql,
                "database": self.db_name,
                "database_path": self.db_path
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "status": "error",
                "execution_time": execution_time,
                "error": str(e),
                "sql_query": sql_query,
                "database": self.db_name,
                "database_path": self.db_path
            }

    def get_database_schema(self) -> dict[str, Any]:
        """Get database schema information"""
        try:
            tables = get_tables_from_db(self.db_path)
            
            schema_info = {
                "database": self.db_name,
                "database_path": self.db_path,
                "tables": {}
            }
            
            for table in tables:
                schema_info["tables"][table.name] = {
                    "columns": table.schema,
                    "sample_data": table.data if table.data else []
                }
            
            return schema_info
            
        except Exception as e:
            return {
                "database": self.db_name,
                "error": str(e),
                "tables": {}
            }

    def list_tables(self) -> list[str]:
        """Get list of table names in the database"""
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            return tables
            
        except Exception as e:
            print(f"Error listing tables: {e}")
            return []

    def get_table_info(self, table_name: str) -> dict[str, Any]:
        """Get detailed information about a specific table"""
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            
            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = cursor.fetchall()
            
            # Get sample data (first 5 rows)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
            sample_data = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return {
                "table_name": table_name,
                "columns": [
                    {
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "primary_key": bool(col[5])
                    }
                    for col in columns_info
                ],
                "sample_data": [list(row) for row in sample_data]
            }
            
        except Exception as e:
            return {
                "table_name": table_name,
                "error": str(e)
            }

    @staticmethod
    def list_available_databases() -> dict[str, str]:
        """List all available SQLite databases"""
        return APP_SETTINGS.SQLITE_DATABASES


def get_sqlite_service(db_name: str = "chinook") -> Optional[SQLiteService]:
    """Get SQLite service instance"""
    try:
        return SQLiteService(db_name)
    except Exception as e:
        print(f"Failed to initialize SQLite service for {db_name}: {e}")
        return None 