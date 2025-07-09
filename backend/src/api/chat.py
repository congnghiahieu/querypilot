from typing import Literal
from uuid import uuid4

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth import get_current_user
from src.models.user import User
from src.nl2sql.components.task_tracker import TaskTracker
from src.nl2sql.nl2sql.nl2sql import convert_nl2sql
from src.nl2sql.nl2sql.prompt.prompt_builder import prompt_factory
from src.nl2sql.nl2sql.utils.data_builder import load_data
from src.nl2sql.nl2sql.utils.enums import EXAMPLE_TYPE, REPR_TYPE, SELECTOR_TYPE
from src.nl2sql.sql_utils import execute_sql_select, get_sqlite_connection

chat_router = APIRouter(prefix="/chat", tags=["Chat"])

# Global storage for chat history (in production, use database)
chat_history = {}
chat_data = {}  # Store actual data for downloads

# Initialize nl2sql components
PATH_DATA = "BIRD_dataset/"
DATABASE_PATH = "./BIRD_dataset/databases/financial/financial.sqlite"
data_instance = None
prompt_instance = None


def initialize_nl2sql():
    """Initialize the nl2sql components"""
    global data_instance, prompt_instance
    if data_instance is None:
        data_instance = load_data("bird", PATH_DATA, None)
        prompt_instance = prompt_factory(
            REPR_TYPE.CODE_REPRESENTATION,
            7,
            EXAMPLE_TYPE.QA,
            SELECTOR_TYPE.EUC_DISTANCE_QUESTION_MASK,
        )(data=data_instance, tokenizer="None")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    type: Literal["text", "table", "chart"]
    content: str
    sql_query: str = ""
    execution_time: float = 0.0
    rows_count: int = 0


def text2sql_pipeline(prompt: str) -> ChatResponse:
    """
    Enhanced text2sql pipeline using the existing nl2sql components
    """
    initialize_nl2sql()

    # Create task tracker for performance monitoring
    task_tracker = TaskTracker()
    task_id = task_tracker.start_task(prompt)

    try:
        # Stage 1: Convert natural language to SQL
        sql_query = convert_nl2sql(prompt, data_instance, prompt_instance, task_tracker)

        # Stage 2: Execute SQL query
        with get_sqlite_connection(DATABASE_PATH) as conn:
            # Add limit to prevent large result sets
            if "LIMIT" not in sql_query.upper():
                sql_query = f"{sql_query} LIMIT 1000"

            result_df = execute_sql_select(conn, sql_query, task_tracker)

            # Get task summary for performance metrics
            task_summary = task_tracker.get_task_summary()

            # Determine response type based on query and results
            response_type = determine_response_type(sql_query, result_df)

            # Format content based on type
            if response_type == "table":
                content = result_df.to_json(orient="records", indent=2)
            elif response_type == "chart":
                # For chart, we still return the data but mark it as chart type
                content = result_df.to_json(orient="records", indent=2)
            else:
                # Text response with summary
                content = f"Query executed successfully. Found {len(result_df)} rows."
                if len(result_df) > 0:
                    content += f"\n\nSample data:\n{result_df.head().to_string()}"

            return ChatResponse(
                type=response_type,
                content=content,
                sql_query=sql_query,
                execution_time=task_summary.get("total_duration_s", 0),
                rows_count=len(result_df),
            )

    except Exception as e:
        task_tracker.record_error(str(e))
        return ChatResponse(
            type="text",
            content=f"Error processing query: {str(e)}",
            sql_query=sql_query if "sql_query" in locals() else "",
            execution_time=0.0,
            rows_count=0,
        )


def determine_response_type(sql_query: str, result_df: pd.DataFrame) -> str:
    """
    Determine the appropriate response type based on query and results
    """
    sql_lower = sql_query.lower()

    # Check for chart indicators
    if any(keyword in sql_lower for keyword in ["sum", "count", "avg", "max", "min", "group by"]):
        if len(result_df.columns) >= 2 and len(result_df) > 1:
            return "chart"

    # Check for table indicators
    if "select *" in sql_lower or len(result_df.columns) > 3:
        return "table"

    # Default to text for simple queries
    return "text"


@chat_router.post("/message")
def send_message(payload: ChatRequest, current_user: User = Depends(get_current_user)):
    """Send a message and get response from text2sql pipeline"""
    chat_id = str(uuid4())

    # Process the message through text2sql pipeline
    result = text2sql_pipeline(payload.message)

    # Store chat history with user association
    chat_history[chat_id] = {
        "user_id": current_user.id,
        "username": current_user.username,
        "question": payload.message,
        "response": result.dict(),
        "timestamp": pd.Timestamp.now().isoformat(),
    }

    # Store data for potential download
    if result.content and result.type in ["table", "chart"]:
        try:
            chat_data[chat_id] = pd.read_json(result.content)
        except:
            chat_data[chat_id] = pd.DataFrame()

    return {"chat_id": chat_id, **chat_history[chat_id]}


@chat_router.get("/history")
def get_chat_history(current_user: User = Depends(get_current_user)):
    """Get chat history for current user"""
    user_chats = [chat for chat in chat_history.values() if chat.get("user_id") == current_user.id]
    return user_chats


@chat_router.get("/history/{id}")
def get_chat_by_id(id: str, current_user: User = Depends(get_current_user)):
    """Get specific chat by ID for current user"""
    chat = chat_history.get(id, {})
    if chat and chat.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return chat


@chat_router.delete("/history/{id}")
def delete_chat_by_id(id: str, current_user: User = Depends(get_current_user)):
    """Delete specific chat by ID for current user"""
    chat = chat_history.get(id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if chat.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    chat_history.pop(id, None)
    chat_data.pop(id, None)
    return {"msg": "deleted"}


@chat_router.post("/continue/{chat_id}")
def continue_chat(
    chat_id: str, payload: ChatRequest, current_user: User = Depends(get_current_user)
):
    """Continue an existing chat conversation"""
    if chat_id not in chat_history:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat = chat_history[chat_id]
    if chat.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Process the new message
    result = text2sql_pipeline(payload.message)

    # Update chat history
    chat_history[chat_id]["response"] = result.dict()
    chat_history[chat_id]["question"] = payload.message
    chat_history[chat_id]["timestamp"] = pd.Timestamp.now().isoformat()

    # Update data for download
    if result.content and result.type in ["table", "chart"]:
        try:
            chat_data[chat_id] = pd.read_json(result.content)
        except:
            chat_data[chat_id] = pd.DataFrame()

    return {"chat_id": chat_id, **chat_history[chat_id]}


@chat_router.get("/data/{chat_id}")
def get_chat_data(chat_id: str, current_user: User = Depends(get_current_user)):
    """Get the data associated with a chat for download purposes"""
    if chat_id not in chat_data:
        raise HTTPException(status_code=404, detail="Chat data not found")

    chat = chat_history.get(chat_id)
    if chat and chat.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    df = chat_data[chat_id]
    return {
        "chat_id": chat_id,
        "data": df.to_dict(orient="records"),
        "columns": df.columns.tolist(),
        "shape": df.shape,
    }
