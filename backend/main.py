from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.auth import auth_router
from src.api.chat import chat_router
from src.api.kb import kb_router
from src.api.metrics import metrics_router
from src.api.query import query_router
from src.api.user import user_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(kb_router)
app.include_router(query_router)
app.include_router(user_router)
app.include_router(metrics_router)
