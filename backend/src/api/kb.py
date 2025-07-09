import os
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.core.settings import KB_FOLDER

kb_router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


@kb_router.post("/upload")
def upload_kb(file: UploadFile = File(...)):
    file_path = os.path.join(KB_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"msg": "uploaded", "filename": file.filename}


@kb_router.get("/list")
def list_kb():
    return [{"filename": f} for f in os.listdir(KB_FOLDER)]


@kb_router.delete("/{id}")
def delete_kb(id: str):
    file_path = os.path.join(KB_FOLDER, id)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"msg": "deleted"}
    raise HTTPException(status_code=404, detail="File not found")
