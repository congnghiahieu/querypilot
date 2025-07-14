from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.auth import auth_router
from src.api.chat import chat_router
from src.api.kb import kb_router
from src.api.metrics import metrics_router
from src.api.sqlite import sqlite_router
from src.api.user import user_router
from src.core.settings import ALLOWED_ORIGINS, STATIC_FOLDER

app = FastAPI(title="QueryPilot API", description="A text2sql chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Comment out AuthMiddleware for now to allow testing
# app.add_middleware(AuthMiddleware)

app.mount("/" + STATIC_FOLDER.strip("/"), StaticFiles(directory=STATIC_FOLDER), name=STATIC_FOLDER)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(kb_router)
app.include_router(sqlite_router)
app.include_router(user_router)
app.include_router(metrics_router)


@app.get("/", summary="Root Endpoint")
def root():
    return {"message": "Welcome to QueryPilot API!", "health_check": {"href": "/metrics/health"}}
