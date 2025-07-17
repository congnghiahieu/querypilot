import json
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlmodel import Column, Field, Relationship, SQLModel, Text

from src.core.file_storage import S3FileStorage, file_storage
from .user import User


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

    # Fields from RAG processing result
    chunks_count: Optional[int] = Field(default=None)
    text_length: Optional[int] = Field(default=None)
    processing_time: Optional[float] = Field(default=None)
    processed_content: Optional[str] = Field(
        default=None, sa_column=Column(Text)
    )  # Snippet of processed content for preview

    # Relationships - use string reference
    user: "User" = Relationship(back_populates="knowledge_bases")

    def get_download_url(self) -> str:
        """Get download URL for the knowledge base file"""
        return file_storage.get_file_url(self.file_path)

    def get_presigned_download_url(self, expiration: int = 3600) -> str:
        """Get presigned download URL for secure access (S3 only)"""

        if hasattr(file_storage, "get_presigned_url"):
            assert isinstance(file_storage, S3FileStorage)
            return file_storage.get_presigned_url(self.file_path, expiration)
        return self.get_download_url()

    def update_from_rag_result(self, rag_result: dict):
        """Update knowledge base with results from RAG processing"""
        if rag_result.get("status") == "success":
            self.processing_status = "completed"
            self.chunks_count = rag_result.get("chunks_count")
            self.text_length = rag_result.get("text_length")
            self.processing_time = rag_result.get("processing_time")
            self.processed_content = rag_result.get("processed_content")
        else:
            self.processing_status = "failed"

    def get_processing_stats(self) -> dict:
        """Get processing statistics"""
        return {
            "chunks_count": self.chunks_count,
            "text_length": self.text_length,
            "processing_time": self.processing_time,
            "status": self.processing_status,
        }
