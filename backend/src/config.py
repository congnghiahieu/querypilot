from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	LLM_API_KEY: str
	LLM_URL: str

	model_config = {
		"env_prefix": "QUERY_PILOT_",
		"extra": "allow",
		"env_file": ".env",
		"env_file_encoding": "utf-8",
	}


settings = Settings()
