import os
from typing import Literal

from openai import OpenAI
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    STAGE: Literal["dev", "prod"] = "dev"
    ENV: Literal["local", "aws"] = "local"

    @property
    def is_dev(self):
        return self.STAGE == "dev"

    @property
    def is_local(self):
        return self.ENV == "local"

    DEEPSEEK_API_KEY: str
    SECRET_KEY: str
    CLIENT_URL: str = "http://localhost:3000"
    DATABASE_URL: str = "postgresql+psycopg2://querypilot:querypilot@localhost:5432/querypilot"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_ignore_empty": True,
        "case_sensitive": False,
    }


APP_SETTINGS = AppSettings()

ALLOWED_ORIGINS = ["*" if APP_SETTINGS.is_dev else APP_SETTINGS.CLIENT_URL]

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".txt", ".csv", ".json", ".md", ".pdf", ".docx", ".xlsx", ".xls"}

LLM_BASE_URL = "https://api.deepseek.com"
LLM_MODEL_NAME = "deepseek-chat"
LLM_CLIENT = OpenAI(api_key=APP_SETTINGS.DEEPSEEK_API_KEY, base_url=LLM_BASE_URL)

PRIVATE_PATHS = ["/chat", "/kb", "/query", "/user", "/auth/logout"]

STATIC_FOLDER = "static"
KB_FOLDER = os.path.join(STATIC_FOLDER, "knowledge")
DOWNLOADS_FOLDER = os.path.join(STATIC_FOLDER, "downloads")
VECTOR_STORE_FOLDER = os.path.join(STATIC_FOLDER, "vector_store")

# RAG Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_CONTEXT_TOKENS = 4000

os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(KB_FOLDER, exist_ok=True)
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)
os.makedirs(VECTOR_STORE_FOLDER, exist_ok=True)
