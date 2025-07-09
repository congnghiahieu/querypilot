from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


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
