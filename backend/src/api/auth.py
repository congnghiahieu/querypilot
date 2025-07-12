from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from src.api.deps import get_current_user
from src.core.db import get_session
from src.core.security import create_access_token, hash_password, verify_password
from src.models.user import User

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserCreate(BaseModel):
    username: str
    password: str
    email: str = ""
    full_name: str = ""


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    created_at: datetime
    role: str = "user"


@auth_router.post("/register", response_model=UserResponse)
def register(user: UserCreate, session: Session = Depends(get_session)):
    """Register new user"""
    # Check if user already exists
    existing_user = session.exec(select(User).where(User.username == user.username)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered"
        )

    # Create new user with hashed password
    hashed_password = hash_password(user.password)
    new_user = User(
        username=user.username,
        hashed_password=hashed_password,
        email=user.email,
        full_name=user.full_name,
        role="user",
        is_active=True,
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return UserResponse(
        id=str(new_user.id),
        username=new_user.username,
        email=new_user.email or "",
        full_name=new_user.full_name or "",
        created_at=new_user.created_at,
        role=new_user.role,
    )


@auth_router.post("/login")
def login(user: UserLogin, session: Session = Depends(get_session)):
    """Login user"""
    # Find user by username
    db_user = session.exec(select(User).where(User.username == user.username)).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is disabled"
        )

    # Create access token
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": db_user.username, "user_id": str(db_user.id)},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": access_token_expires.total_seconds(),
        "user": UserResponse(
            id=str(db_user.id),
            username=db_user.username,
            email=db_user.email or "",
            full_name=db_user.full_name or "",
            created_at=db_user.created_at,
            role=db_user.role,
        ),
    }


@auth_router.post("/logout")
def logout():
    """Logout user (client-side token removal)"""
    return {"message": "Successfully logged out. Please remove token from client."}


@auth_router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email or "",
        full_name=current_user.full_name or "",
        created_at=current_user.created_at,
        role=current_user.role,
    )
