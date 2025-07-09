from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.core.db import get_db_conn
from src.core.security import create_access_token, hash_password, verify_password

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

fake_user_db = {"admin": {"username": "admin", "hashed_password": hash_password("admin123")}}


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


@auth_router.post("/register")
def register(payload: RegisterRequest):
    conn = get_db_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
            (payload.username, hash_password(payload.password)),
        )
        conn.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()
    return {"msg": "User registered"}


@auth_router.post("/login")
def login(payload: LoginRequest):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT hashed_password FROM users WHERE username = ?", (payload.username,))
    row = cursor.fetchone()
    conn.close()

    if not row or not verify_password(payload.password, row[0]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": payload.username})
    return {"access_token": token, "token_type": "bearer"}


@auth_router.post("/logout")
def logout():
    return {"msg": "Stateless logout – client must delete token"}


@auth_router.get("/me")
def get_me():
    return {"msg": "user info"}
