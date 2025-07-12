import json
import os
import shutil
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, desc, select

from src.api.auth import get_current_user
from src.core.db import get_session
from src.core.settings import ALLOWED_EXTENSIONS, KB_FOLDER, MAX_FILE_SIZE
from src.models.knowledge_base import KnowledgeBase, KnowledgeBaseInsight
from src.models.user import User
from src.nl2sql.rag import rag_service

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


class KnowledgeBaseInsightResponse(BaseModel):
    id: str
    summary: str
    key_insights: List[str]
    entities: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    processing_time: Optional[float] = None
    created_at: str


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


@kb_router.post("/upload")
def upload_kb(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Upload knowledge base file"""
    validate_file(file)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Create user-specific folder
    user_kb_folder = os.path.join(KB_FOLDER, str(current_user.id))
    os.makedirs(user_kb_folder, exist_ok=True)

    # Generate unique filename first
    file_extension = os.path.splitext(file.filename)[1]

    # Create knowledge base record with proper filename and file_path
    kb_record = KnowledgeBase(
        user_id=current_user.id,
        filename="",  # Will be updated after generating unique name
        original_filename=file.filename,
        file_path="",  # Will be updated after generating path
        file_type=os.path.splitext(file.filename)[1][1:].lower(),
        file_size=file.size or 0,
        processing_status="pending",
    )
    session.add(kb_record)
    session.commit()
    session.refresh(kb_record)

    # Now generate unique filename using the ID
    safe_filename = f"{kb_record.id}{file_extension}"
    file_path = os.path.join(user_kb_folder, safe_filename)

    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update file path and filename
        kb_record.filename = safe_filename
        kb_record.file_path = file_path
        kb_record.processing_status = "processing"
        session.commit()

        # Process document for insights using RAG
        try:
            insights_data = process_document_insights(
                file_path,
                kb_record.file_type,
                str(kb_record.id),
                kb_record.original_filename,
                current_user.id,
            )

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

        except Exception as e:
            kb_record.processing_status = "failed"
            session.commit()
            print(f"Error processing document insights: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

        return {
            "id": str(kb_record.id),
            "message": "File uploaded and processed successfully",
            "filename": file.filename,
            "size": os.path.getsize(file_path),
            "processing_status": kb_record.processing_status,
            "chunks_count": insights_data.get("chunks_count", 0),
        }

    except Exception as e:
        # Cleanup on error
        session.delete(kb_record)
        session.commit()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


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


@kb_router.get("/list", response_model=List[FileInfo])
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
        id=str(insight.id),
        summary=insight.summary,
        key_insights=json.loads(insight.key_insights),
        entities=json.loads(insight.entities) if insight.entities else None,
        topics=json.loads(insight.topics) if insight.topics else None,
        processing_time=insight.processing_time,
        created_at=insight.created_at.isoformat(),
    )


@kb_router.delete("/{kb_id}")
def delete_kb(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete knowledge base file"""
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

    try:
        # Remove from vector store
        rag_service.remove_knowledge_base(str(kb_record.id), current_user.id)

        # Delete file if it exists
        if kb_record.file_path and os.path.exists(kb_record.file_path):
            os.remove(kb_record.file_path)

        # Delete database record (cascade will handle insight)
        session.delete(kb_record)
        session.commit()

        return {"message": "Knowledge base deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@kb_router.get("/download/{kb_id}")
def download_kb(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Download knowledge base file"""
    from fastapi.responses import FileResponse

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

    if not os.path.exists(kb_record.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=kb_record.file_path,
        filename=kb_record.original_filename,
        media_type="application/octet-stream",
    )
