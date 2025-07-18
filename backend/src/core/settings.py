import os
from pathlib import Path
from typing import Literal

from openai import OpenAI
from pydantic import Field
from pydantic_settings import BaseSettings

# Project root directory (backend folder)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class AppSettings(BaseSettings):
    STAGE: Literal["dev", "prod"] = "dev"
    ENV: Literal["local", "aws"] = (
        "local"  # Global environment (legacy, for backward compatibility)
    )

    # Fine-grained service configurations
    DATA_SOURCE: Literal["local", "aws"] = (
        "local"  # Controls where data queries go (SQLite vs Athena)
    )
    AUTH_SOURCE: Literal["local", "aws"] = "local"  # Controls authentication (local vs Cognito)
    FILE_STORAGE: Literal["local", "aws"] = "local"  # Controls file storage (local vs S3)
    USER_DB: Literal["local", "aws"] = (
        "local"  # Controls user/session database (local PostgreSQL vs RDS)
    )

    @property
    def is_dev(self):
        return self.STAGE == "dev"

    @property
    def is_prod(self):
        return self.STAGE == "prod"

    @property
    def is_local(self):
        return self.ENV == "local"

    @property
    def is_aws(self):
        return self.ENV == "aws"

    # New granular properties
    @property
    def use_aws_data(self):
        """Whether to use AWS Athena for data queries"""
        return self.DATA_SOURCE == "aws"

    @property
    def use_aws_auth(self):
        """Whether to use AWS Cognito for authentication"""
        return self.AUTH_SOURCE == "aws"

    @property
    def use_aws_storage(self):
        """Whether to use AWS S3 for file storage"""
        return self.FILE_STORAGE == "aws"

    @property
    def use_aws_user_db(self):
        """Whether to use AWS RDS for user/session database"""
        return self.USER_DB == "aws"

    # Athena database selection methods
    def get_athena_database(self, database_type: str = "raw") -> str:
        """
        Get Athena database name based on type

        Args:
            database_type: "raw", "agg", "aggregated", or "default"

        Returns:
            Database name to use for queries
        """
        if database_type.lower() in ["raw", "raw_data", "detailed", "raw_database"]:
            return self.AWS_ATHENA_RAW_DATABASE or self.AWS_ATHENA_DATABASE
        elif database_type.lower() in ["agg", "aggregated", "summary", "aggregate", "agg_database"]:
            return self.AWS_ATHENA_AGG_DATABASE or self.AWS_ATHENA_DATABASE
        else:
            # Default fallback
            return self.AWS_ATHENA_DATABASE

    def get_available_athena_databases(self) -> dict[str, str]:
        """Get all configured Athena databases"""
        databases = {"default": self.AWS_ATHENA_DATABASE}

        if self.AWS_ATHENA_RAW_DATABASE:
            databases["raw"] = self.AWS_ATHENA_RAW_DATABASE
        if self.AWS_ATHENA_AGG_DATABASE:
            databases["agg"] = self.AWS_ATHENA_AGG_DATABASE

        return databases

    DEEPSEEK_API_KEY: str
    SECRET_KEY: str
    CLIENT_URL: str = "http://localhost:3000"

    # Local Database Configuration
    DATABASE_URL: str = "postgresql+psycopg2://querypilot:querypilot@localhost:5432/querypilot"

    # SQLite Database Configuration
    SQLITE_DB_PATH: str = Field(default="Chinook.db", description="Default SQLite database path")
    SQLITE_DATABASES: dict[str, str] = Field(
        default={
            "chinook": "Chinook.db",
            # Path formats (all relative to backend/ directory):
            "vpbank": "dataset/vpbank.sqlite",  # In backend/dataset/ root
        },
        description="Available SQLite databases (paths relative to backend/ directory)",
    )

    # AWS RDS Configuration
    AWS_RDS_HOST: str = ""
    AWS_RDS_PORT: int = 5432
    AWS_RDS_DB_NAME: str = ""
    AWS_RDS_USERNAME: str = ""
    AWS_RDS_PASSWORD: str = ""

    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET_NAME: str = ""
    AWS_S3_BUCKET_URL: str = ""  # Optional: Custom S3 URL

    # AWS Athena Configuration
    AWS_ATHENA_DATABASE: str = Field(
        default="default", description="Primary Athena database name (for backward compatibility)"
    )
    AWS_ATHENA_RAW_DATABASE: str = Field(
        default="", description="Athena database for raw/detailed data"
    )
    AWS_ATHENA_AGG_DATABASE: str = Field(
        default="", description="Athena database for aggregated/summary data"
    )
    AWS_ATHENA_WORKGROUP: str = Field(default="primary", description="Athena workgroup")
    AWS_ATHENA_OUTPUT_LOCATION: str = Field(
        default="", description="S3 bucket for Athena query results"
    )
    AWS_ATHENA_TIMEOUT: int = Field(default=300, description="Athena query timeout in seconds")

    # AWS Cognito Configuration
    AWS_COGNITO_USER_POOL_ID: str = Field(default="", description="AWS Cognito User Pool ID")
    AWS_COGNITO_CLIENT_ID: str = Field(default="", description="AWS Cognito App Client ID")
    AWS_COGNITO_CLIENT_SECRET: str = Field(default="", description="AWS Cognito App Client Secret")
    AWS_COGNITO_REGION: str = Field(default="", description="AWS Cognito Region")
    AWS_COGNITO_DOMAIN: str = Field(default="", description="AWS Cognito Domain")

    # AWS IAM Configuration for user roles
    AWS_IAM_ROLE_PREFIX: str = Field(
        default="QueryPilot-User-", description="Prefix for user IAM roles"
    )
    AWS_IAM_POLICY_ARN_BASE: str = Field(default="", description="Base policy ARN for users")

    @property
    def get_database_url(self) -> str:
        """Get database URL for user/session data (not data queries)"""
        if self.use_aws_user_db:
            return f"postgresql+psycopg2://{self.AWS_RDS_USERNAME}:{self.AWS_RDS_PASSWORD}@{self.AWS_RDS_HOST}:{self.AWS_RDS_PORT}/{self.AWS_RDS_DB_NAME}"
        return self.DATABASE_URL

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_ignore_empty": True,
        "case_sensitive": False,
        "extra": "allow",
    }


APP_SETTINGS = AppSettings()

ALLOWED_ORIGINS = [APP_SETTINGS.CLIENT_URL]

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