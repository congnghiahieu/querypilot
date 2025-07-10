from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlmodel import Column, Field, Relationship, SQLModel, Text


class KnowledgeBase(SQLModel, table=True):
    __tablename__ = "knowledge_bases"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=512)
    file_type: str = Field(max_length=10)
    file_size: int = Field(default=0)
    upload_date: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True))
    )
    processing_status: str = Field(
        default="pending", max_length=20
    )  # pending, processing, completed, failed

    # Relationships
    user: "User" = Relationship(back_populates="knowledge_bases")
    insight: Optional["KnowledgeBaseInsight"] = Relationship(back_populates="knowledge_base")


class KnowledgeBaseInsight(SQLModel, table=True):
    __tablename__ = "knowledge_base_insights"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    knowledge_base_id: UUID = Field(foreign_key="knowledge_bases.id", unique=True, index=True)
    summary: str = Field(sa_column=Column(Text))
    key_insights: str = Field(sa_column=Column(Text))  # JSON array of insights
    entities: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON array of entities
    topics: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON array of topics
    processed_content: Optional[str] = Field(
        default=None, sa_column=Column(Text)
    )  # Processed/cleaned content
    processing_time: Optional[float] = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True))
    )

    # Relationships
    knowledge_base: KnowledgeBase = Relationship(back_populates="insight")
