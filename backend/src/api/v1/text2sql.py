from fastapi import APIRouter
from openai import OpenAI

from src.config import settings

text2sql_router = APIRouter()

llm_client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_URL)


@text2sql_router.get("/generate")
def generate():
	response = llm_client.chat.completions.create(
		model="deepseek-chat",
		messages=[
			{"role": "system", "content": "You are a helpful assistant"},
			{"role": "user", "content": "Hello"},
		],
		stream=False,
	)
	return {"message": response.choices[0].message.content}
