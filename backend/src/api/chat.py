import json
from typing import Literal, Optional
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, desc, select

from src.api.auth import get_current_user
from src.core.db import get_session
from src.models.chat import ChatDataResult, ChatMessage, ChatSession
from src.models.user import User
from src.nl2sql.rag import rag_service

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


def process_nl2sql_message(message: str, user_id: UUID) -> ChatResponse:
    """
    Process nl2sql message with RAG context from knowledge base.
    This integrates RAG functionality while keeping nl2sql logic for future implementation.
    """
    try:
        # Get relevant context from knowledge base using RAG
        context = rag_service.get_context_for_query(message, user_id)

        # Build enhanced message with context
        enhanced_message = message
        if context:
            enhanced_message = f"""
Context from knowledge base:
{context}

User question: {message}

Please provide a helpful response based on the context above and the user's question.
"""

        # For now, return a text response with context
        # TODO: Implement actual nl2sql logic here
        if context:
            response_content = f"""Based on your knowledge base, here's what I found relevant to your question:

{context}

This context has been retrieved from your uploaded documents. The actual NL2SQL functionality will be implemented next to provide structured queries and data analysis.

Your question: {message}"""
        else:
            response_content = f"""I couldn't find relevant information in your knowledge base for this query: "{message}"

Please make sure you have uploaded relevant documents to your knowledge base, or try rephrasing your question.

The actual NL2SQL functionality will be implemented next to provide structured queries and data analysis."""

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


@chat_router.post("/message")
def send_message(
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

    # Add user message
    user_message = ChatMessage(
        chat_session_id=chat_session.id, role="user", content=payload.message
    )
    session.add(user_message)

    # Process message through nl2sql pipeline with RAG
    result = process_nl2sql_message(payload.message, current_user.id)

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

    # Store data if it's table or chart type
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

    # Get messages
    messages = []
    for message in chat_session.messages:
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
def continue_chat(
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

    # Add user message
    user_message = ChatMessage(
        chat_session_id=chat_session.id, role="user", content=payload.message
    )
    session.add(user_message)

    # Process message through nl2sql pipeline with RAG
    result = process_nl2sql_message(payload.message, current_user.id)

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

    # Store data if needed
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


@chat_router.get("/data/{chat_id}")
def get_chat_data(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get the data associated with a chat for download purposes"""
    try:
        chat_uuid = UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat ID format")

    # Get the latest assistant message with data
    statement = (
        select(ChatMessage)
        .join(ChatSession)
        .join(ChatDataResult)
        .where(ChatSession.id == chat_uuid)
        .where(ChatSession.user_id == current_user.id)
        .where(ChatMessage.role == "assistant")
        .order_by(desc(ChatMessage.created_at))
    )
    message = session.exec(statement).first()

    if not message or not message.data_result:
        raise HTTPException(status_code=404, detail="Chat data not found")

    data_result = message.data_result

    return {
        "chat_id": chat_id,
        "data": json.loads(data_result.data_json),
        "columns": json.loads(data_result.columns),
        "shape": [data_result.shape_rows, data_result.shape_cols],
    }
