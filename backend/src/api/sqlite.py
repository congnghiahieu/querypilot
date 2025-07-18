from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from src.api.auth import get_current_user
from src.core.db import get_session
from src.core.sqlite_service import SQLiteService, get_sqlite_service
from src.core.sql_execution import get_sql_execution_service
from src.models.user import User

sqlite_router = APIRouter(prefix="/sqlite", tags=["SQLite"])


class SQLiteQueryRequest(BaseModel):
    query: str
    database: Optional[str] = "chinook"


class SQLiteQueryResponse(BaseModel):
    status: str
    execution_time: float
    data: List[dict]
    columns: List[str]
    row_count: int
    column_count: int
    sql_query: str
    database: str
    database_path: Optional[str] = None
    error: Optional[str] = None


class DatabaseInfo(BaseModel):
    name: str
    path: str
    tables: List[str]


class TableInfo(BaseModel):
    table_name: str
    columns: List[dict]
    sample_data: List[List]
    error: Optional[str] = None


@sqlite_router.get("/databases", response_model=dict)
async def list_databases(
    current_user: User = Depends(get_current_user),
):
    """List all available SQLite databases"""
    try:
        databases = SQLiteService.list_available_databases()
        result = {}
        
        for db_name, db_path in databases.items():
            sqlite_service = get_sqlite_service(db_name)
            if sqlite_service:
                tables = sqlite_service.list_tables()
                result[db_name] = {
                    "name": db_name,
                    "path": db_path,
                    "tables": tables,
                    "table_count": len(tables)
                }
            else:
                result[db_name] = {
                    "name": db_name,
                    "path": db_path,
                    "error": "Failed to connect to database"
                }
        
        return {"databases": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@sqlite_router.get("/databases/{database_name}/schema")
async def get_database_schema(
    database_name: str,
    current_user: User = Depends(get_current_user),
):
    """Get schema information for a specific SQLite database"""
    try:
        sqlite_service = get_sqlite_service(database_name)
        if not sqlite_service:
            raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")
        
        schema = sqlite_service.get_database_schema()
        return schema
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@sqlite_router.get("/databases/{database_name}/tables")
async def list_tables(
    database_name: str,
    current_user: User = Depends(get_current_user),
):
    """List all tables in a specific SQLite database"""
    try:
        sqlite_service = get_sqlite_service(database_name)
        if not sqlite_service:
            raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")
        
        tables = sqlite_service.list_tables()
        return {"database": database_name, "tables": tables}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@sqlite_router.get("/databases/{database_name}/tables/{table_name}")
async def get_table_info(
    database_name: str,
    table_name: str,
    current_user: User = Depends(get_current_user),
):
    """Get detailed information about a specific table"""
    try:
        sqlite_service = get_sqlite_service(database_name)
        if not sqlite_service:
            raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")
        
        table_info = sqlite_service.get_table_info(table_name)
        return table_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@sqlite_router.post("/query", response_model=SQLiteQueryResponse)
async def execute_query(
    request: SQLiteQueryRequest,
    current_user: User = Depends(get_current_user),
):
    """Execute a SQL query on a SQLite database"""
    try:
        # Use the SQL execution service which now supports SQLite
        sql_service = get_sql_execution_service()
        if not sql_service:
            raise HTTPException(status_code=500, detail="SQL execution service not available")
        
        # Execute query with specified database
        result = await sql_service.execute_query(request.query, request.database)
        
        return SQLiteQueryResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@sqlite_router.get("/health")
async def health_check():
    """Health check for SQLite service"""
    try:
        # Try to connect to the default database
        sqlite_service = get_sqlite_service("vpbank")
        if sqlite_service:
            tables = sqlite_service.list_tables()
            return {
                "status": "healthy",
                "default_database": "vpbank",
                "tables_count": len(tables)
            }
        else:
            return {
                "status": "unhealthy",
                "error": "Failed to connect to default database"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        } 