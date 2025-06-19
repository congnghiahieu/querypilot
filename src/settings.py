import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path="./.env")


#def get_env(name: str, cast_type: type, required: bool = True) -> Any:
#	value = os.getenv(name)
#	is_empty_value = value in [None, ""]
#
#	if required and is_empty_value:
#		raise EnvironmentError(f"Missing required environment variable: {name}")
#
#	try:
#		if is_empty_value:
#			return ""
#		return cast_type(value)
#	except Exception as e:
#		raise ValueError(f"Environment variable {name} is not valid {cast_type.__name__}: {e}")
#
#
#@dataclass(frozen=True)
#class Settings:
#	LLM_API_KEY: str
#	LLM_BASE_URL: str
#	LLM_MODEL_NAME: str
#
#	@staticmethod
#	def load():
#		return Settings(
#			LLM_API_KEY=get_env("LLM_API_KEY", str),
#			LLM_BASE_URL=get_env("LLM_BASE_URL", str),
#			LLM_MODEL_NAME=get_env("LLM_MODEL_NAME", str),
#		)
#
#
#SETTINGS = Settings.load()
#LLM_CLIENT = OpenAI(api_key=SETTINGS.LLM_API_KEY, base_url=SETTINGS.LLM_BASE_URL)
