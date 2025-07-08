from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core import security

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

fake_user_db = {
    "admin": {"username": "admin", "hashed_password": security.hash_password("admin123")}
}


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


@auth_router.post("/register")
def register(payload: RegisterRequest):
    if payload.username in fake_user_db:
        raise HTTPException(status_code=400, detail="User already exists")
    fake_user_db[payload.username] = {
        "username": payload.username,
        "hashed_password": security.hash_password(payload.password),
    }
    return {"msg": "User registered"}


@auth_router.post("/login")
def login(payload: LoginRequest):
    user = fake_user_db.get(payload.username)
    if not user or not security.verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = security.create_access_token({"sub": payload.username})
    return {"access_token": token, "token_type": "bearer"}


@auth_router.post("/logout")
def logout():
    return {"msg": "Stateless logout – delete token on client side"}


@auth_router.get("/me")
def me(username: str = "anonymous"):
    return {"username": username}
