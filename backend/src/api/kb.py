import json
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session, desc, select

from src.api.auth import get_current_user
from src.core.db import get_session
from src.core.file_storage import S3FileStorage, file_storage
from src.core.rag import rag_service
from src.core.settings import ALLOWED_EXTENSIONS, APP_SETTINGS, MAX_FILE_SIZE
from src.models.knowledge_base import KnowledgeBase, KnowledgeBaseInsight
from src.models.user import User

kb_router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


class FileInfo(BaseModel):
    id: str
    filename: str
    original_filename: str
    size: int
    upload_date: str
    file_type: str
    processing_status: str
    has_insight: bool


class KnowledgeBaseResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    upload_date: str
    processing_status: str
    download_url: str
    insight: Optional["KnowledgeBaseInsightResponse"] = None


class KnowledgeBaseInsightResponse(BaseModel):
    summary: str
    key_insights: list[str]
    entities: list[str]
    topics: list[str]
    processing_time: Optional[float] = None


class TextUploadRequest(BaseModel):
    text: str
    title: str = "Text Input"


def process_document_insights(
    file_path: str, file_type: str, kb_id: str, filename: str, user_id: UUID
) -> dict:
    """
    Process document using RAG service to extract insights
    """
    try:
        return rag_service.process_document(file_path, file_type, kb_id, filename, user_id)
    except Exception as e:
        raise Exception(f"Error processing document: {str(e)}")


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024):.1f}MB",
        )

    if file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
            )


@kb_router.post("/upload", response_model=KnowledgeBaseResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Upload file to knowledge base"""
    validate_file(file)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_extension = os.path.splitext(file.filename)[1][1:].lower()

    try:
        # Reset file pointer
        await file.seek(0)

        # Use file storage service
        storage_info = file_storage.save_file(file.file, file.filename, file_extension)

        # Create knowledge base entry
        kb_entry = KnowledgeBase(
            user_id=current_user.id,
            filename=storage_info["filename"],
            original_filename=file.filename,
            file_path=storage_info["file_path"],
            file_type=file_extension,
            file_size=storage_info["file_size"],
            processing_status="processing",
        )

        session.add(kb_entry)
        session.commit()
        session.refresh(kb_entry)

        # Process document with RAG
        try:
            # For S3, we need to download the file temporarily for processing
            if APP_SETTINGS.is_aws:
                assert isinstance(file_storage, S3FileStorage)
                # Download file from S3 for processing
                import tempfile

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{file_extension}"
                ) as temp_file:
                    temp_file_path = temp_file.name
                    # Download from S3
                    s3_client = file_storage.s3_client
                    s3_client.download_file(
                        file_storage.bucket_name,
                        storage_info["file_path"],
                        temp_file_path,
                    )

                    # Process the temporary file
                    insights = rag_service.process_document(
                        temp_file_path,
                        file_extension,
                        str(kb_entry.id),
                        file.filename,
                        current_user.id,
                    )

                    # Clean up temporary file
                    os.unlink(temp_file_path)
            else:
                # For local storage, use the file path directly
                insights = rag_service.process_document(
                    storage_info["file_path"],
                    file_extension,
                    str(kb_entry.id),
                    file.filename,
                    current_user.id,
                )

            # Create insight entry
            insight = KnowledgeBaseInsight(
                knowledge_base_id=kb_entry.id,
                summary=insights["summary"],
                key_insights=str(insights["key_insights"]),
                entities=str(insights.get("entities", [])),
                topics=str(insights.get("topics", [])),
                processed_content=insights.get("processed_content"),
                processing_time=insights.get("processing_time"),
            )

            session.add(insight)
            kb_entry.processing_status = "completed"
            session.commit()
            session.refresh(insight)

        except Exception as e:
            print(f"Error processing document: {e}")
            kb_entry.processing_status = "failed"
            session.commit()

            # Clean up uploaded file if processing failed
            file_storage.delete_file(storage_info["file_path"])
            raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

        return KnowledgeBaseResponse(
            id=str(kb_entry.id),
            filename=kb_entry.filename,
            original_filename=kb_entry.original_filename,
            file_type=kb_entry.file_type,
            file_size=kb_entry.file_size,
            upload_date=kb_entry.upload_date.isoformat(),
            processing_status=kb_entry.processing_status,
            download_url=file_storage.get_file_url(kb_entry.file_path),
            insight=KnowledgeBaseInsightResponse(
                summary=insight.summary,
                key_insights=insight.get_key_insights(),
                entities=insight.get_entities(),
                topics=insight.get_topics(),
                processing_time=insight.processing_time,
            )
            if insight
            else None,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@kb_router.post("/upload-text")
def upload_text_kb(
    payload: TextUploadRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Upload text as knowledge base"""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text content cannot be empty")

    # Create knowledge base record for text
    kb_record = KnowledgeBase(
        user_id=current_user.id,
        filename=payload.title,
        original_filename=payload.title,
        file_path="",  # No file path for text
        file_type="text",
        file_size=len(payload.text.encode("utf-8")),
        processing_status="processing",
    )
    session.add(kb_record)
    session.commit()
    session.refresh(kb_record)

    try:
        # Process text using RAG
        insights_data = rag_service.process_text(payload.text, str(kb_record.id), current_user.id)

        # Create insight record
        insight = KnowledgeBaseInsight(
            knowledge_base_id=kb_record.id,
            summary=insights_data["summary"],
            key_insights=json.dumps(insights_data["key_insights"]),
            entities=json.dumps(insights_data.get("entities", [])),
            topics=json.dumps(insights_data.get("topics", [])),
            processed_content=insights_data.get("processed_content", ""),
            processing_time=insights_data.get("processing_time", 0.0),
        )
        session.add(insight)

        # Update processing status
        kb_record.processing_status = "completed"
        session.commit()

        return {
            "id": str(kb_record.id),
            "message": "Text uploaded and processed successfully",
            "title": payload.title,
            "size": len(payload.text.encode("utf-8")),
            "processing_status": kb_record.processing_status,
            "chunks_count": insights_data.get("chunks_count", 0),
        }

    except Exception as e:
        # Cleanup on error
        session.delete(kb_record)
        session.commit()
        print(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process text: {str(e)}")


@kb_router.get("/list", response_model=list[FileInfo])
def list_kb(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    """List knowledge base files for current user"""
    statement = (
        select(KnowledgeBase)
        .where(KnowledgeBase.user_id == current_user.id)
        .order_by(desc(KnowledgeBase.upload_date))
    )
    kb_records = session.exec(statement).all()

    files_info = []
    for kb in kb_records:
        files_info.append(
            FileInfo(
                id=str(kb.id),
                filename=kb.filename,
                original_filename=kb.original_filename,
                size=kb.file_size,
                upload_date=kb.upload_date.isoformat(),
                file_type=kb.file_type,
                processing_status=kb.processing_status,
                has_insight=kb.insight is not None,
            )
        )

    return files_info


@kb_router.get("/{kb_id}/insight")
def get_kb_insight(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get insight for a knowledge base file"""
    try:
        kb_uuid = UUID(kb_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid knowledge base ID format")

    statement = (
        select(KnowledgeBase)
        .where(KnowledgeBase.id == kb_uuid)
        .where(KnowledgeBase.user_id == current_user.id)
    )
    kb_record = session.exec(statement).first()

    if not kb_record:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    if not kb_record.insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    insight = kb_record.insight
    return KnowledgeBaseInsightResponse(
        summary=insight.summary,
        key_insights=json.loads(insight.key_insights),
        entities=json.loads(insight.entities) if insight.entities else None,
        topics=json.loads(insight.topics) if insight.topics else None,
        processing_time=insight.processing_time,
    )


@kb_router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete knowledge base entry"""
    try:
        kb_uuid = UUID(kb_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid knowledge base ID format")

    # Get knowledge base entry
    statement = (
        select(KnowledgeBase)
        .where(KnowledgeBase.id == kb_uuid)
        .where(KnowledgeBase.user_id == current_user.id)
    )
    kb_entry = session.exec(statement).first()

    if not kb_entry:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")

    try:
        # Delete from vector store
        rag_service.remove_knowledge_base(str(kb_entry.id), current_user.id)

        # Delete file from storage
        file_storage.delete_file(kb_entry.file_path)

        # Delete from database
        session.delete(kb_entry)
        session.commit()

        return {"message": "Knowledge base deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting knowledge base: {str(e)}")


@kb_router.get("/download/{kb_id}")
async def download_file(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Download file from knowledge base"""
    try:
        kb_uuid = UUID(kb_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid knowledge base ID format")

    # Get knowledge base entry
    statement = (
        select(KnowledgeBase)
        .where(KnowledgeBase.id == kb_uuid)
        .where(KnowledgeBase.user_id == current_user.id)
    )
    kb_entry = session.exec(statement).first()

    if not kb_entry:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")

    # Handle download based on storage type
    if APP_SETTINGS.is_aws:
        assert isinstance(file_storage, S3FileStorage)
        # For S3, generate presigned URL for secure download
        try:
            presigned_url = file_storage.get_presigned_url(kb_entry.file_path)
            return RedirectResponse(url=presigned_url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating download URL: {str(e)}")
    else:
        # For local storage, return static file URL
        download_url = file_storage.get_file_url(kb_entry.file_path)
        return RedirectResponse(url=download_url)
