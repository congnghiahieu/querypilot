import os
from typing import Literal

from openai import OpenAI
from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    STAGE: Literal["dev", "prod"] = "dev"
    ENV: Literal["local", "aws"] = "local"

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

    DEEPSEEK_API_KEY: str
    SECRET_KEY: str
    CLIENT_URL: str = "http://localhost:3000"

    # Local Database Configuration
    DATABASE_URL: str = "postgresql+psycopg2://querypilot:querypilot@localhost:5432/querypilot"

    AWS_REGION: str = ""

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
    AWS_ATHENA_DATABASE: str = Field(default="default", description="Athena database name")
    AWS_ATHENA_WORKGROUP: str = Field(default="primary", description="Athena workgroup")
    AWS_ATHENA_OUTPUT_LOCATION: str = Field(
        default="", description="S3 bucket for Athena query results"
    )
    AWS_ATHENA_CATALOG: str = Field(default="AwsDataCatalog", description="Athena catalog name")
    AWS_ATHENA_TIMEOUT: int = Field(default=300, description="Athena query timeout in seconds")

    # AWS Cognito Configuration
    AWS_COGNITO_USER_POOL_ID: str = Field(default="", description="AWS Cognito User Pool ID")
    AWS_COGNITO_IDENTITY_POOL_ID: str = Field(
        default="", description="AWS Cognito Identity Pool ID"
    )
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
        if self.is_aws:
            return f"postgresql+psycopg2://{self.AWS_RDS_USERNAME}:{self.AWS_RDS_PASSWORD}@{self.AWS_RDS_HOST}:{self.AWS_RDS_PORT}/{self.AWS_RDS_DB_NAME}"
        return self.DATABASE_URL

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_ignore_empty": True,
        "case_sensitive": False,
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
