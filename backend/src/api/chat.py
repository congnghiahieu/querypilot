from fastapi import APIRouter, Depends

from src.core.deps import get_current_user

chat_router = APIRouter(prefix="/chat", tags=["Chat"], dependencies=[Depends[get_current_user]])


@chat_router.post("/message")
def send_message():
    pass


@chat_router.get("/history")
def get_chat_history():
    pass


@chat_router.get("/history/{id}")
def get_chat_by_id(id: str):
    pass


@chat_router.delete("/history/{id}")
def delete_chat_by_id(id: str):
    pass
