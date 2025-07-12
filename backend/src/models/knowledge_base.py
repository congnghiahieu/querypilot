from __future__ import annotations

import json
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlmodel import Column, Field, Relationship, SQLModel, Text

from src.core.file_storage import S3FileStorage, file_storage


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

    def get_download_url(self) -> str:
        """Get download URL for the knowledge base file"""
        return file_storage.get_file_url(self.file_path)

    def get_presigned_download_url(self, expiration: int = 3600) -> str:
        """Get presigned download URL for secure access (S3 only)"""

        if hasattr(file_storage, "get_presigned_url"):
            assert isinstance(file_storage, S3FileStorage)
            return file_storage.get_presigned_url(self.file_path, expiration)
        return self.get_download_url()


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

    def get_key_insights(self) -> list:
        """Safely parse key_insights JSON string to list"""
        if not self.key_insights:
            return []
        try:
            return json.loads(self.key_insights)
        except json.JSONDecodeError:
            return []

    def get_entities(self) -> list:
        """Safely parse entities JSON string to list"""
        if not self.entities:
            return []
        try:
            return json.loads(self.entities)
        except json.JSONDecodeError:
            return []

    def get_topics(self) -> list:
        """Safely parse topics JSON string to list"""
        if not self.topics:
            return []
        try:
            return json.loads(self.topics)
        except json.JSONDecodeError:
            return []

    def set_key_insights(self, insights: list):
        """Safely convert list to JSON string for storage"""
        self.key_insights = json.dumps(insights)

    def set_entities(self, entities: list):
        """Safely convert list to JSON string for storage"""
        self.entities = json.dumps(entities)

    def set_topics(self, topics: list):
        """Safely convert list to JSON string for storage"""
        self.topics = json.dumps(topics)
