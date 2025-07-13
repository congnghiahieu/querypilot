from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlmodel import Column, Field, Relationship, SQLModel, Text


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=255)
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True))
    )
    is_active: bool = Field(default=True)

    # Relationships - use string names to avoid circular imports
    user: "User" = Relationship(back_populates="chat_sessions")
    messages: list["ChatMessage"] = Relationship(back_populates="chat_session", cascade_delete=True)


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    chat_session_id: UUID = Field(foreign_key="chat_sessions.id", index=True)
    role: str = Field(max_length=20)  # 'user' or 'assistant'
    content: str = Field(sa_column=Column(Text))
    sql_query: Optional[str] = Field(default=None, sa_column=Column(Text))
    response_type: Optional[str] = Field(default=None, max_length=20)  # 'text', 'table', 'chart'
    execution_time: Optional[float] = Field(default=None)
    rows_count: Optional[int] = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True))
    )

    # Relationships
    chat_session: "ChatSession" = Relationship(back_populates="messages")
    data_result: Optional["ChatDataResult"] = Relationship(back_populates="message")


class ChatDataResult(SQLModel, table=True):
    __tablename__ = "chat_data_results"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    message_id: UUID = Field(foreign_key="chat_messages.id", unique=True, index=True)
    data_json: str = Field(sa_column=Column(Text))  # Store DataFrame as JSON
    columns: str = Field(sa_column=Column(Text))  # Store column names as JSON array
    shape_rows: int = Field(default=0)
    shape_cols: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True))
    )

    # Relationships
    message: "ChatMessage" = Relationship(back_populates="data_result")
