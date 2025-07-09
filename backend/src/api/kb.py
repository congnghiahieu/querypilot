import os
import shutil
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from src.api.auth import get_current_user
from src.core.settings import ALLOWED_EXTENSIONS, KB_FOLDER, MAX_FILE_SIZE
from src.models.user import User

kb_router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


class FileInfo(BaseModel):
    filename: str
    size: int
    upload_date: str
    file_type: str


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024 * 1024):.1f}MB",
        )

    # Check file extension
    if file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
            )


@kb_router.post("/upload")
def upload_kb(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Upload knowledge base file"""
    # Validate file
    validate_file(file)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Create user-specific folder
    user_kb_folder = os.path.join(KB_FOLDER, str(current_user.id))
    os.makedirs(user_kb_folder, exist_ok=True)

    # Save file with user prefix to avoid conflicts
    safe_filename = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(user_kb_folder, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "size": os.path.getsize(file_path),
            "path": file_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


@kb_router.get("/list", response_model=List[FileInfo])
def list_kb(current_user: User = Depends(get_current_user)):
    """List knowledge base files for current user"""
    user_kb_folder = os.path.join(KB_FOLDER, str(current_user.id))

    if not os.path.exists(user_kb_folder):
        return []

    files_info = []
    for filename in os.listdir(user_kb_folder):
        file_path = os.path.join(user_kb_folder, filename)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            files_info.append(
                FileInfo(
                    filename=filename,
                    size=stat.st_size,
                    upload_date=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    file_type=os.path.splitext(filename)[1][1:] or "unknown",
                )
            )

    return files_info


@kb_router.delete("/{filename}")
def delete_kb(filename: str, current_user: User = Depends(get_current_user)):
    """Delete knowledge base file"""
    user_kb_folder = os.path.join(KB_FOLDER, str(current_user.id))
    file_path = os.path.join(user_kb_folder, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Security check: ensure file belongs to current user
    if not file_path.startswith(user_kb_folder):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        os.remove(file_path)
        return {"message": "File deleted successfully", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@kb_router.get("/download/{filename}")
def download_kb(filename: str, current_user: User = Depends(get_current_user)):
    """Download knowledge base file"""
    from fastapi.responses import FileResponse

    user_kb_folder = os.path.join(KB_FOLDER, str(current_user.id))
    file_path = os.path.join(user_kb_folder, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Security check: ensure file belongs to current user
    if not file_path.startswith(user_kb_folder):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")
