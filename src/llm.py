from openai.types.chat import ChatCompletionMessageParam

from src.settings import LLM_CLIENT, SETTINGS


def call_llm(messages: list[ChatCompletionMessageParam]):
	response = LLM_CLIENT.chat.completions.create(
		model=SETTINGS.LLM_MODEL_NAME,
		messages=messages,
		stream=False,
	)
	return response.choices[0].message.content
