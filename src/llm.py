from openai.types.chat import ChatCompletionMessageParam

from src.settings import LLM_CLIENT, SETTINGS


# # Real call to OpenAI API to get a response
# stream = LLM_CLIENT.chat.completions.create(
# 	model=SETTINGS.LLM_MODEL_NAME,
# 	messages=[
# 		{"role": m["role"], "text": m["text"]} for m in st.session_state.messages
# 	],
# 	stream=True,
# )
# response = st.write_stream(stream)

def call_llm(messages: list[ChatCompletionMessageParam]):
	response = LLM_CLIENT.chat.completions.create(
		model=SETTINGS.LLM_MODEL_NAME,
		messages=messages,
		stream=False,
	)
	return response.choices[0].message.content
