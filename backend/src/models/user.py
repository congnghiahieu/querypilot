from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from src.models.chat import ChatSession
from src.models.knowledge_base import KnowledgeBase


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)  # Primary authentication field
    hashed_password: str  # For authentication

    # Additional user information (optional)
    email: Optional[str] = Field(default="")
    full_name: Optional[str] = Field(default="")

    role: str = Field(default="user")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Add relationships
    chat_sessions: list[ChatSession] = Relationship(back_populates="user")
    knowledge_bases: list[KnowledgeBase] = Relationship(back_populates="user")
    user_settings: Optional["UserSettings"] = Relationship(back_populates="user")


class UserSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    vai_tro: str = Field(default="Nhân viên")
    chi_nhanh: str = Field(default="Hà Nội")
    pham_vi: str = Field(default="Cá nhân")
    du_lieu: str = Field(default="Dữ liệu cơ bản")
    datasource_permissions: str = Field(default="[]")  # JSON string of list
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Add relationship
    user: User = Relationship(back_populates="user_settings")
