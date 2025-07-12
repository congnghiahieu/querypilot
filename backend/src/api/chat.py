import json
from io import BytesIO
from typing import Literal, Optional
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, desc, select

from src.api.auth import get_current_user
from src.core.db import get_session
from src.core.rag import rag_service
from src.core.sql_execution import get_sql_execution_service
from src.models.chat import ChatDataResult, ChatMessage, ChatSession
from src.models.user import User

chat_router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    type: Literal["text", "table", "chart"]
    content: str
    sql_query: str = ""
    execution_time: float = 0.0
    rows_count: int = 0


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sql_query: Optional[str] = None
    response_type: Optional[str] = None
    execution_time: Optional[float] = None
    rows_count: Optional[int] = None
    created_at: str
    has_data: bool = False  # Indicates if this message has downloadable data


async def process_nl2sql_message(message: str, user_id: UUID) -> ChatResponse:
    """
    Process nl2sql message with RAG context from knowledge base.
    Returns either text response or data response with JSON.
    """
    try:
        # Get relevant context from knowledge base using RAG
        context = rag_service.get_context_for_query(message, user_id)

        # Check if we're in AWS environment and can use SQL execution service
        sql_service = get_sql_execution_service()

        if sql_service:
            try:
                # Get database schema for better SQL generation
                schema_info = sql_service.get_database_schema()

                # TODO: Implement actual NL2SQL conversion with schema
                # For now, we'll use a placeholder SQL generation
                # In the real implementation, you would use your NL2SQL model here
                # sql_query = convert_nl2sql(message, data, prompt, schema_info=schema_info)

                # Placeholder SQL generation based on message content
                sql_query = generate_placeholder_sql(message, schema_info)

                if sql_query:
                    # Validate query against schema
                    is_valid, validation_message = sql_service.validate_query_against_schema(
                        sql_query
                    )

                    if not is_valid:
                        return ChatResponse(
                            type="text",
                            content=f"Generated SQL query is invalid: {validation_message}\n\nSQL: {sql_query}",
                            sql_query=sql_query,
                            execution_time=0.0,
                            rows_count=0,
                        )

                    # Execute SQL query
                    result = await sql_service.execute_query(sql_query)

                    if result["status"] == "success":
                        return ChatResponse(
                            type="table",
                            content=json.dumps(result["data"]),
                            sql_query=sql_query,
                            execution_time=result["execution_time"],
                            rows_count=result["row_count"],
                        )
                    else:
                        return ChatResponse(
                            type="text",
                            content=f"Error executing SQL query: {result['error']}\n\nSQL: {sql_query}",
                            sql_query=sql_query,
                            execution_time=result["execution_time"],
                            rows_count=0,
                        )

            except Exception as e:
                return ChatResponse(
                    type="text",
                    content=f"Error processing query with SQL execution service: {str(e)}",
                    sql_query="",
                    execution_time=0.0,
                    rows_count=0,
                )

        # Fallback to context-based response if SQL execution service is not available
        if context:
            response_content = f"""Based on your knowledge base, here's what I found relevant to your question:

{context}

Note: SQL execution service is not configured. To execute SQL queries on your data lake, please configure AWS Athena settings.

Your question: {message}"""
        else:
            response_content = f"""I couldn't find relevant information in your knowledge base for this query: "{message}"

Please make sure you have uploaded relevant documents to your knowledge base, or configure AWS Athena to query your data lake.

The SQL execution functionality requires AWS configuration to execute queries on your data sources."""

        return ChatResponse(
            type="text",
            content=response_content,
            sql_query="",
            execution_time=0.0,
            rows_count=0,
        )

    except Exception as e:
        return ChatResponse(
            type="text",
            content=f"Error processing your message: {str(e)}. Please try again.",
            sql_query="",
            execution_time=0.0,
            rows_count=0,
        )


def generate_placeholder_sql(message: str, schema_info: dict) -> str:
    """
    Generate placeholder SQL based on message content and schema.
    This is a temporary implementation until the full NL2SQL pipeline is integrated.
    """
    if not schema_info or not schema_info.get("tables"):
        return ""

    # Get first table for demo
    first_table = schema_info["tables"][0]
    table_name = first_table["name"]
    columns = [col["name"] for col in first_table["columns"]]

    # Simple keyword-based SQL generation for demo
    if any(keyword in message.lower() for keyword in ["count", "total", "number"]):
        return f"SELECT COUNT(*) as total_count FROM {table_name}"
    elif any(keyword in message.lower() for keyword in ["all", "show", "list"]):
        column_list = ", ".join(columns[:5])  # Limit to first 5 columns
        return f"SELECT {column_list} FROM {table_name} LIMIT 10"
    elif "average" in message.lower() or "avg" in message.lower():
        # Find numeric columns
        numeric_cols = [
            col["name"]
            for col in first_table["columns"]
            if col["type"].lower() in ["int", "bigint", "double", "float", "decimal"]
        ]
        if numeric_cols:
            return f"SELECT AVG({numeric_cols[0]}) as average FROM {table_name}"

    # Default query
    column_list = ", ".join(columns[:3])  # Limit to first 3 columns
    return f"SELECT {column_list} FROM {table_name} LIMIT 5"


@chat_router.post("/message")
async def send_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Send a message and get response from text2sql pipeline"""

    # Create new chat session if this is a new conversation
    chat_session = ChatSession(
        user_id=current_user.id,
        title=payload.message[:50] + "..." if len(payload.message) > 50 else payload.message,
    )
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)

    # Add user message (users only send text)
    user_message = ChatMessage(
        chat_session_id=chat_session.id, role="user", content=payload.message, response_type="text"
    )
    session.add(user_message)

    # Process message through nl2sql pipeline with RAG and SQL execution service
    result = await process_nl2sql_message(payload.message, current_user.id)

    # Add assistant message
    assistant_message = ChatMessage(
        chat_session_id=chat_session.id,
        role="assistant",
        content=result.content,
        sql_query=result.sql_query if result.sql_query else None,
        response_type=result.type,
        execution_time=result.execution_time,
        rows_count=result.rows_count,
    )
    session.add(assistant_message)
    session.commit()
    session.refresh(assistant_message)

    # Store data if it's table or chart type (only for assistant messages with JSON data)
    if result.type in ["table", "chart"] and result.content:
        try:
            # Parse JSON data for storage
            data_df = pd.read_json(result.content)
            data_result = ChatDataResult(
                message_id=assistant_message.id,
                data_json=result.content,
                columns=json.dumps(data_df.columns.tolist()),
                shape_rows=len(data_df),
                shape_cols=len(data_df.columns),
            )
            session.add(data_result)
            session.commit()
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error storing data result: {e}")

    return {
        "chat_id": str(chat_session.id),
        "message_id": str(assistant_message.id),
        "response": result.dict(),
    }


@chat_router.get("/history")
def get_chat_history(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    """Get chat history for current user"""
    statement = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .where(ChatSession.is_active == True)
        .order_by(desc(ChatSession.updated_at))
    )
    chat_sessions = session.exec(statement).all()

    result = []
    for chat_session in chat_sessions:
        # Count messages
        message_count = len(chat_session.messages)

        result.append(
            ChatSessionResponse(
                id=str(chat_session.id),
                title=chat_session.title,
                created_at=chat_session.created_at.isoformat(),
                updated_at=chat_session.updated_at.isoformat(),
                message_count=message_count,
            )
        )

    return result


@chat_router.get("/history/{chat_id}")
def get_chat_by_id(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get specific chat by ID for current user"""
    try:
        chat_uuid = UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat ID format")

    statement = (
        select(ChatSession)
        .where(ChatSession.id == chat_uuid)
        .where(ChatSession.user_id == current_user.id)
    )
    chat_session = session.exec(statement).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Get messages with data result info
    messages = []
    for message in chat_session.messages:
        has_data = message.data_result is not None
        messages.append(
            ChatMessageResponse(
                id=str(message.id),
                role=message.role,
                content=message.content,
                sql_query=message.sql_query,
                response_type=message.response_type,
                execution_time=message.execution_time,
                rows_count=message.rows_count,
                created_at=message.created_at.isoformat(),
                has_data=has_data,
            )
        )

    return {
        "id": str(chat_session.id),
        "title": chat_session.title,
        "created_at": chat_session.created_at.isoformat(),
        "updated_at": chat_session.updated_at.isoformat(),
        "messages": messages,
    }


@chat_router.delete("/history/{chat_id}")
def delete_chat_by_id(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete specific chat by ID for current user"""
    try:
        chat_uuid = UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat ID format")

    statement = (
        select(ChatSession)
        .where(ChatSession.id == chat_uuid)
        .where(ChatSession.user_id == current_user.id)
    )
    chat_session = session.exec(statement).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Soft delete
    chat_session.is_active = False
    session.commit()

    return {"message": "Chat deleted successfully"}


@chat_router.post("/continue/{chat_id}")
async def continue_chat(
    chat_id: str,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Continue an existing chat conversation"""
    try:
        chat_uuid = UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat ID format")

    statement = (
        select(ChatSession)
        .where(ChatSession.id == chat_uuid)
        .where(ChatSession.user_id == current_user.id)
        .where(ChatSession.is_active == True)
    )
    chat_session = session.exec(statement).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Add user message (users only send text)
    user_message = ChatMessage(
        chat_session_id=chat_session.id, role="user", content=payload.message, response_type="text"
    )
    session.add(user_message)

    # Process message through nl2sql pipeline with RAG and SQL execution service
    result = await process_nl2sql_message(payload.message, current_user.id)

    # Add assistant message
    assistant_message = ChatMessage(
        chat_session_id=chat_session.id,
        role="assistant",
        content=result.content,
        sql_query=result.sql_query if result.sql_query else None,
        response_type=result.type,
        execution_time=result.execution_time,
        rows_count=result.rows_count,
    )
    session.add(assistant_message)

    # Update chat session timestamp
    from datetime import datetime

    chat_session.updated_at = datetime.utcnow()

    session.commit()
    session.refresh(assistant_message)

    # Store data if needed (only for assistant messages with JSON data)
    if result.type in ["table", "chart"] and result.content:
        try:
            data_df = pd.read_json(result.content)
            data_result = ChatDataResult(
                message_id=assistant_message.id,
                data_json=result.content,
                columns=json.dumps(data_df.columns.tolist()),
                shape_rows=len(data_df),
                shape_cols=len(data_df.columns),
            )
            session.add(data_result)
            session.commit()
        except Exception as e:
            print(f"Error storing data result: {e}")

    return {
        "chat_id": str(chat_session.id),
        "message_id": str(assistant_message.id),
        "response": result.dict(),
    }


@chat_router.get("/data/{message_id}")
def get_message_data(
    message_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get the data associated with a specific message for preview purposes"""
    try:
        message_uuid = UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID format")

    # Get the message with data result and verify ownership
    statement = (
        select(ChatMessage)
        .join(ChatSession)
        .join(ChatDataResult)
        .where(ChatMessage.id == message_uuid)
        .where(ChatSession.user_id == current_user.id)
        .where(ChatMessage.role == "assistant")
    )
    message = session.exec(statement).first()

    if not message or not message.data_result:
        raise HTTPException(status_code=404, detail="Message data not found")

    data_result = message.data_result

    return {
        "message_id": message_id,
        "data": json.loads(data_result.data_json),
        "columns": json.loads(data_result.columns),
        "shape": [data_result.shape_rows, data_result.shape_cols],
        "sql_query": message.sql_query,
        "response_type": message.response_type,
    }


@chat_router.get("/download/{message_id}")
def download_message_data(
    message_id: str,
    format: str = Query(..., enum=["json", "csv", "excel", "pdf"]),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Download message data in specified format"""
    try:
        message_uuid = UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID format")

    # Get the message with data result and verify ownership
    statement = (
        select(ChatMessage)
        .join(ChatSession)
        .join(ChatDataResult)
        .where(ChatMessage.id == message_uuid)
        .where(ChatSession.user_id == current_user.id)
        .where(ChatMessage.role == "assistant")
    )
    message = session.exec(statement).first()

    if not message or not message.data_result:
        raise HTTPException(status_code=404, detail="Message data not found")

    # Load data from database
    data_result = message.data_result

    filename = f"message_{current_user.username}_{message_id[:8]}_data.{format}"

    if format == "json":
        return StreamingResponse(
            BytesIO(data_result.data_json.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # For other formats, convert to DataFrame first
    df = pd.read_json(data_result.data_json)

    if df.empty:
        raise HTTPException(status_code=400, detail="No data to download")

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
