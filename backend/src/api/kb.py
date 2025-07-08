from fastapi import APIRouter, UploadFile

kb_router = APIRouter(prefix="/kb", tags=["KnowledgeBase"])


@kb_router.post("/upload")
def upload_kb(file: UploadFile):
    pass


@kb_router.get("/list")
def list_kb():
    pass


@kb_router.delete("/{id}")
def delete_kb(id: str):
    pass
