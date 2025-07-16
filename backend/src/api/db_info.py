from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Dict, Any, List, Optional

from src.api.deps import get_current_user
from src.core.sql_execution import get_sql_execution_service
from src.core.sqlite_service import SQLiteService
from src.core.settings import APP_SETTINGS

router = APIRouter(prefix="/db-info", tags=["Database Info"])

@router.get("/databases")
async def list_databases(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """List all available databases"""
    try:
        if APP_SETTINGS.use_aws_data:
            # Get available Athena databases
            available_dbs = APP_SETTINGS.get_available_athena_databases()
            return {
                "status": "success",
                "databases": available_dbs
            }
        else:
            # Get available SQLite databases
            available_dbs = SQLiteService.list_available_databases()
            return {
                "status": "success",
                "databases": available_dbs
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list databases: {str(e)}")

@router.get("/schema/{db_name}")
async def get_database_schema(
    db_name: str = Path(..., description="Database name or type (for Athena: 'raw', 'agg', 'default')"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get schema information for a specific database"""
    try:
        # Get SQL execution service with user context
        sql_service = get_sql_execution_service(user_context=current_user)
        if not sql_service:
            raise HTTPException(status_code=500, detail="Failed to initialize SQL service")
        
        # Get database schema
        schema = sql_service.get_database_schema(database=db_name)
        
        if "error" in schema:
            raise HTTPException(status_code=500, detail=schema["error"])
        
        # Transform schema to match the expected frontend format
        if APP_SETTINGS.use_aws_data:
            # For Athena, transform the schema format
            transformed_schema = {
                "database": schema.get("database", db_name),
                "database_path": f"athena://{schema.get('database', db_name)}",
                "tables": {}
            }
            
            for table in schema.get("tables", []):
                table_name = table["name"]
                transformed_schema["tables"][table_name] = {
                    "columns": [
                        {
                            "name": col["name"],
                            "type": col["type"],
                            "primary_key": False,  # Athena doesn't have traditional primary keys
                            "not_null": False,     # Athena schema doesn't specify NOT NULL
                            "comment": col.get("comment", "")
                        }
                        for col in table.get("columns", [])
                    ],
                    "sample_data": []  # Sample data not available from Glue Catalog
                }
        else:
            # For SQLite, the schema is already in the correct format
            transformed_schema = schema
        
        return {
            "status": "success",
            "schema": transformed_schema
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database schema: {str(e)}")

@router.get("/tables/{db_name}")
async def list_tables(
    db_name: str = Path(..., description="Database name or type"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """List tables in a specific database"""
    try:
        if APP_SETTINGS.use_aws_data:
            # For Athena, get schema and extract table names
            sql_service = get_sql_execution_service(user_context=current_user)
            if not sql_service:
                raise HTTPException(status_code=500, detail="Failed to initialize SQL service")
            
            schema = sql_service.get_database_schema(database=db_name)
            if "error" in schema:
                raise HTTPException(status_code=500, detail=schema["error"])
            
            table_names = [table["name"] for table in schema.get("tables", [])]
            
            return {
                "status": "success",
                "database": schema.get("database", db_name),
                "tables": table_names
            }
        else:
            # For SQLite, use SQLiteService
            sqlite_service = SQLiteService(db_name)
            tables = sqlite_service.list_tables()
            
            return {
                "status": "success",
                "database": db_name,
                "tables": tables
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tables: {str(e)}")

@router.get("/table/{db_name}/{table_name}")
async def get_table_info(
    db_name: str = Path(..., description="Database name or type"),
    table_name: str = Path(..., description="Table name"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed information about a specific table"""
    try:
        if APP_SETTINGS.use_aws_data:
            # For Athena, get schema and find the specific table
            sql_service = get_sql_execution_service(user_context=current_user)
            if not sql_service:
                raise HTTPException(status_code=500, detail="Failed to initialize SQL service")
            
            schema = sql_service.get_database_schema(database=db_name)
            if "error" in schema:
                raise HTTPException(status_code=500, detail=schema["error"])
            
            # Find the specific table
            table_info = None
            for table in schema.get("tables", []):
                if table["name"] == table_name:
                    table_info = {
                        "columns": [
                            {
                                "name": col["name"],
                                "type": col["type"],
                                "primary_key": False,  # Athena doesn't have traditional primary keys
                                "not_null": False,     # Athena schema doesn't specify NOT NULL
                                "comment": col.get("comment", "")
                            }
                            for col in table.get("columns", [])
                        ],
                        "sample_data": []  # Sample data not available from Glue Catalog
                    }
                    break
            
            if not table_info:
                raise HTTPException(status_code=404, detail=f"Table {table_name} not found in database {db_name}")
            
            return {
                "status": "success",
                "table_info": table_info
            }
        else:
            # For SQLite, use SQLiteService
            sqlite_service = SQLiteService(db_name)
            table_info = sqlite_service.get_table_info(table_name)
            
            return {
                "status": "success",
                "table_info": table_info
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table information: {str(e)}")
