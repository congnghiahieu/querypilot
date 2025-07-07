from openai import OpenAI
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    DEEPSEEK_API_KEY: str
    SECRET_KEY: str

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_ignore_empty": True,
        "case_sensitive": False,
        "secrets_dir": "env/",
    }


APP_SETTINGS = AppSettings()

LLM_BASE_URL = "https://api.deepseek.com"
LLM_MODEL_NAME = "deepseek-chat"
LLM_CLIENT = OpenAI(api_key=APP_SETTINGS.DEEPSEEK_API_KEY, base_url=LLM_BASE_URL)
