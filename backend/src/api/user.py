from fastapi import APIRouter, Depends

from src.core.deps import get_current_user

user_router = APIRouter(prefix="/user", tags=["User"], dependencies=[Depends[get_current_user]])

user_router = APIRouter()


@user_router.get("/settings")
def get_settings():
    pass


@user_router.post("/settings")
def update_settings():
    pass
