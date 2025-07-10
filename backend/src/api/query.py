from io import BytesIO
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from src.api.auth import get_current_user
from src.core.db import get_session
from src.models.chat import ChatDataResult, ChatMessage, ChatSession
from src.models.user import User

query_router = APIRouter(prefix="/query", tags=["Query"])


@query_router.get("/download/{chat_id}")
def download_chat_data(
    chat_id: str,
    format: str = Query(..., enum=["csv", "excel", "pdf"]),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Download chat data in specified format"""
    try:
        chat_uuid = UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat ID format")

    # Get the latest assistant message with data for this chat
    statement = (
        select(ChatMessage)
        .join(ChatSession)
        .join(ChatDataResult)
        .where(ChatSession.id == chat_uuid)
        .where(ChatSession.user_id == current_user.id)
        .where(ChatMessage.role == "assistant")
        .order_by(ChatMessage.created_at.desc())
    )
    message = session.exec(statement).first()

    if not message or not message.data_result:
        raise HTTPException(status_code=404, detail="Chat data not found")

    # Load data from database
    data_result = message.data_result
    df = pd.read_json(data_result.data_json)

    if df.empty:
        raise HTTPException(status_code=400, detail="No data to download")

    filename = f"chat_{current_user.username}_{chat_id[:8]}_results.{format}"

    if format == "csv":
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return StreamingResponse(
            BytesIO(output.read()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    elif format == "excel":
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    elif format == "pdf":
        # For PDF, create a simple CSV for now (placeholder implementation)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


@query_router.get("/download")
def download_sample():
    """Download sample data (for testing)"""
    df = pd.DataFrame([{"user": "Alice", "amount": 100}, {"user": "Bob", "amount": 150}])

    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return StreamingResponse(
        BytesIO(output.read()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_data.csv"},
    )


@query_router.get("/validate")
def validate_query(sql_query: str):
    """Validate SQL query syntax"""
    # TODO: Implement proper SQL validation logic
    # This is a placeholder implementation
    try:
        # Basic validation - check for dangerous keywords
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
        sql_upper = sql_query.upper()

        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return {
                    "is_valid": False,
                    "message": f"Query contains potentially dangerous keyword: {keyword}",
                    "query": sql_query,
                }

        # Basic syntax check - must contain SELECT
        if "SELECT" not in sql_upper:
            return {
                "is_valid": False,
                "message": "Query must contain SELECT statement",
                "query": sql_query,
            }

        return {"is_valid": True, "message": "Query appears to be valid", "query": sql_query}

    except Exception as e:
        return {
            "is_valid": False,
            "message": f"Error validating query: {str(e)}",
            "query": sql_query,
        }
