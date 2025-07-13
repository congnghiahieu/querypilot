from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(unique=True, index=True)  # Primary authentication field
    hashed_password: str  # For authentication

    # Additional user information (optional)
    email: Optional[str] = Field(default="")
    full_name: Optional[str] = Field(default="")

    role: str = Field(default="user")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Add cognito_user_id for AWS Cognito integration
    cognito_user_id: Optional[str] = Field(default=None, index=True)

    # Add relationships - use string names to avoid forward reference issues
    chat_sessions: list["ChatSession"] = Relationship(back_populates="user")
    knowledge_bases: list["KnowledgeBase"] = Relationship(back_populates="user")
    user_settings: Optional["UserSettings"] = Relationship(back_populates="user")


class UserSettings(SQLModel, table=True):
    __tablename__ = "user_settings"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    vai_tro: str = Field(default="Nhân viên")
    chi_nhanh: str = Field(default="Hà Nội")
    pham_vi: str = Field(default="Cá nhân")
    du_lieu: str = Field(default="Dữ liệu cơ bản")
    datasource_permissions: str = Field(default="[]")  # JSON string of list
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Add relationship
    user: "User" = Relationship(back_populates="user_settings")
