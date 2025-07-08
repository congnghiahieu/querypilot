from fastapi import APIRouter

user_router = APIRouter(prefix="/user", tags=["User"])

user_router = APIRouter()


@user_router.get("/settings")
def get_settings():
    pass


@user_router.post("/settings")
def update_settings():
    pass
