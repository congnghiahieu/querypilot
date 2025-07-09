from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from src.core.db import get_session
from src.core.security import create_access_token, hash_password, verify_password
from src.models.user import User

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


@auth_router.post("/register")
def register(payload: RegisterRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == payload.username)).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = User(username=payload.username, hashed_password=hash_password(payload.password))
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"msg": "User registered"}


@auth_router.post("/login")
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == payload.username)).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": payload.username})
    return {"access_token": token, "token_type": "bearer"}


@auth_router.post("/logout")
def logout():
    return {"msg": "Stateless logout – client must delete token"}


@auth_router.get("/me")
def get_me():
    return {"msg": "user info"}
