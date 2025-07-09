from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.api.auth import get_current_user
from src.models.user import User

query_router = APIRouter(prefix="/query", tags=["Query"])

# Import chat_data from chat module
from src.api.chat import chat_data, chat_history


@query_router.get("/download/{chat_id}")
def download_chat_data(
    chat_id: str,
    format: str = Query(..., enum=["csv", "excel", "pdf"]),
    current_user: User = Depends(get_current_user),
):
    """Download chat data in specified format"""
    if chat_id not in chat_data:
        raise HTTPException(status_code=404, detail="Chat data not found")

    # Check if user owns this chat
    chat = chat_history.get(chat_id)
    if chat and chat.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    df = chat_data[chat_id]

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
        # For PDF, we'll create a simple HTML table and convert to PDF
        # For now, return as CSV with PDF extension (placeholder)
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
    from src.nl2sql.sql_utils import get_sqlite_connection, validate_sql_query

    try:
        with get_sqlite_connection("./BIRD_dataset/databases/financial/financial.sqlite") as conn:
            is_valid, message = validate_sql_query(conn, sql_query)
            return {"is_valid": is_valid, "message": message, "query": sql_query}
    except Exception as e:
        return {
            "is_valid": False,
            "message": f"Error validating query: {str(e)}",
            "query": sql_query,
        }
