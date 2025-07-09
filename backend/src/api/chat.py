from typing import Literal
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

chat_router = APIRouter(prefix="/chat", tags=["Chat"])

chat_history = {}


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    type: Literal["text", "table", "chart"]
    content: str


def text2sql_stub(prompt: str) -> ChatResponse:
    if "top" in prompt:
        return ChatResponse(type="table", content="SELECT * FROM top_users LIMIT 10")
    return ChatResponse(type="text", content="SELECT COUNT(*) FROM customers")


@chat_router.post("/message")
def send_message(payload: ChatRequest):
    chat_id = str(uuid4())
    result = text2sql_stub(payload.message)
    chat_history[chat_id] = {"question": payload.message, "response": result.dict()}
    return {"chat_id": chat_id, **chat_history[chat_id]}


@chat_router.get("/history")
def get_chat_history():
    return list(chat_history.values())


@chat_router.get("/history/{id}")
def get_chat_by_id(id: str):
    return chat_history.get(id, {})


@chat_router.delete("/history/{id}")
def delete_chat_by_id(id: str):
    chat_history.pop(id, None)
    return {"msg": "deleted"}
