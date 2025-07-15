import json
import time
from io import BytesIO
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, desc, select

from src.api.auth import get_current_user
from src.core.db import get_session
from src.core.rag import rag_service
from src.core.settings import APP_SETTINGS
from src.core.sql_execution import get_sql_execution_service
from src.models.chat import ChatDataResult, ChatMessage, ChatSession
from src.models.user import User

chat_router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    type: Literal["text", "table", "chart"]
    content: str  # Human-readable message to user
    sql_query: Optional[str] = None  # SQL query if generated
    data: Optional[List[Dict[str, Any]]] = None  # Query results if available
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


async def process_nl2sql_message(message: str, db_id: str, user_id: UUID) -> ChatResponse:
    """
    Process nl2sql message with RAG context from knowledge base.
    Returns structured response with content, SQL, and results.
    """

    start = time.time()
    print(f"[TIME] Starting process_nl2sql_message")

    try:
        # Get relevant context from knowledge base using RAG
        context = rag_service.get_context_for_query(message, user_id)
        print(f"[TIME] Context retrieval: {time.time() - start}")

        # Check if we're in AWS environment and can use SQL execution service
        sql_service = get_sql_execution_service()
        print(f"[TIME] SQL execution service: {time.time() - start}")

        if sql_service:
            try:
                # Get database schema for better SQL generation
                # For local environment, use vpbank SQLite database
                database_name = "vpbank" if not APP_SETTINGS.is_aws else None
                #schema_info = sql_service.get_database_schema(database_name)

                # Import and use nl2sql function to generate SQL query based on message content and context
                from src.nl2sql.dail_sql.nl2sql import nl2sql
                print(f"[DEBUG] Calling nl2sql with message: {message}, context: {context}, db_id: {db_id}")
                sql_query = nl2sql(message, context, db_id)
                print(f"[DEBUG] nl2sql returned: {sql_query}")

                if sql_query:
                    # Execute SQL query
                    time_execute = time.time()
                    result = await sql_service.execute_query(sql_query, database_name)
                    print(f"[TIME] SQL execution time: {time.time() - time_execute}")

                    if result["status"] == "success":
                        # Prepare user-friendly content message
                        content_message = f"I found {result['row_count']} results for your query about customer segments. Here's the data:"
                        
                        return ChatResponse(
                            type="table",
                            content=content_message,
                            sql_query=sql_query,
                            data=result["data"],
                            execution_time=result["execution_time"],
                            rows_count=result["row_count"],
                        )
                    else:
                        # SQL execution failed
                        error_message = f"I generated this SQL query but encountered an error during execution: {result['error']}"
                        
                        return ChatResponse(
                            type="text",
                            content=error_message,
                            sql_query=sql_query,
                            data=None,
                            execution_time=result.get("execution_time", 0.0),
                            rows_count=0,
                        )
                else:
                    # Could not generate SQL
                    return ChatResponse(
                        type="text",
                        content=f"I couldn't generate a SQL query for your request: '{message}'. Please try rephrasing your question or be more specific about what data you want to see.",
                        sql_query=None,
                        data=None,
                        execution_time=0.0,
                        rows_count=0,
                    )

            except Exception as e:
                return ChatResponse(
                    type="text",
                    content=f"I encountered an error while processing your query: {str(e)}. Please try again or rephrase your question.",
                    sql_query=None,
                    data=None,
                    execution_time=0.0,
                    rows_count=0,
                )
        else:
            return ChatResponse(
                type="text",
                content="SQL execution service is not available. Please check your configuration and try again.",
                sql_query=None,
                data=None,
                execution_time=0.0,
                rows_count=0,
            )
    except Exception as e:
        return ChatResponse(
            type="text",
            content=f"I encountered an error processing your message: {str(e)}. Please try again.",
            sql_query=None,
            data=None,
            execution_time=0.0,
            rows_count=0,
        )

@chat_router.post("/new")
async def new_chat(
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
    result = await process_nl2sql_message(payload.message, "vpbank", current_user.id)

    # Store data as JSON in content field for database compatibility
    content_for_db = result.content
    if result.data:
        # For table/chart responses, store the data as JSON in content field for database
        content_for_db = json.dumps(result.data)

    # Add assistant message
    assistant_message = ChatMessage(
        chat_session_id=chat_session.id,
        role="assistant",
        content=content_for_db,
        sql_query=result.sql_query,
        response_type=result.type,
        execution_time=result.execution_time,
        rows_count=result.rows_count,
    )
    session.add(assistant_message)
    session.commit()
    session.refresh(assistant_message)

    # Store data if it's table or chart type (only for assistant messages with data)
    if result.type in ["table", "chart"] and result.data:
        try:
            # Create data result for download functionality
            data_result = ChatDataResult(
                message_id=assistant_message.id,
                data_json=json.dumps(result.data),
                columns=json.dumps(list(result.data[0].keys()) if result.data else []),
                shape_rows=len(result.data),
                shape_cols=len(result.data[0].keys()) if result.data else 0,
            )
            session.add(data_result)
            session.commit()
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error storing data result: {e}")

    return {
        "chat_id": str(chat_session.id),
        "title": chat_session.title,
        "message_id": str(assistant_message.id),
        "created_at": chat_session.created_at.isoformat(),
        "updated_at": chat_session.updated_at.isoformat(),
        "response": result.model_dump(),
    }


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
    result = await process_nl2sql_message(payload.message, "vpbank", current_user.id)

    # Store data as JSON in content field for database compatibility
    content_for_db = result.content
    if result.data:
        # For table/chart responses, store the data as JSON in content field for database
        content_for_db = json.dumps(result.data)

    # Add assistant message
    assistant_message = ChatMessage(
        chat_session_id=chat_session.id,
        role="assistant",
        content=content_for_db,
        sql_query=result.sql_query,
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

    # Store data if it's table or chart type (only for assistant messages with data)
    if result.type in ["table", "chart"] and result.data:
        try:
            # Create data result for download functionality
            data_result = ChatDataResult(
                message_id=assistant_message.id,
                data_json=json.dumps(result.data),
                columns=json.dumps(list(result.data[0].keys()) if result.data else []),
                shape_rows=len(result.data),
                shape_cols=len(result.data[0].keys()) if result.data else 0,
            )
            session.add(data_result)
            session.commit()
        except Exception as e:
            print(f"Error storing data result: {e}")

    return {
        "chat_id": str(chat_session.id),
        "title": chat_session.title,
        "message_id": str(assistant_message.id),
        "created_at": chat_session.created_at.isoformat(),
        "updated_at": chat_session.updated_at.isoformat(),
        "response": result.model_dump(),
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
