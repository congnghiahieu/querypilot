import time

import streamlit as st

from src.text2sql import convert_text_to_sql
from src.prompt import construct_full_prompt
from src.prompt_templates import get_sql_generation_prompt_template
from src.database_schema import get_database_schema
from src.sql_validator import validate_sql
from src.sql_executor import execute_sql

# Initialize chat history
if "messages" not in st.session_state:
	st.session_state.messages = []


def save_feedback(index):
	st.session_state.messages[index]["feedback"] = st.session_state[f"feedback_{index}"]


st.title("Query Pilot")


# Display chat messages from history on app rerun
for i, message in enumerate(st.session_state.messages):
	with st.chat_message(message["role"]):
		if "text" in message:
			st.write(message["text"])
		if "table" in message:
			st.dataframe(message["table"])
		if "chart" in message:
			st.line_chart(message["chart"])

		if message["role"] == "assistant":
			feedback = message.get("feedback", None)
			st.session_state[f"feedback_{i}"] = feedback
			st.feedback(
				"stars",
				key=f"feedback_{i}",
				disabled=feedback is not None,
				on_change=save_feedback,
				args=[i],
			)

# React to user input
if prompt := st.chat_input("What is up?"):
	# Step 1: User provides a prompt
	with st.chat_message("user"):
		st.markdown(prompt)
	st.session_state.messages.append({"role": "user", "text": prompt})

	# Step 2: Frontend show a thinking animation, Backend translate text to SQL
	with st.spinner("Translating text to SQL", show_time=True):
		error_counter = 0
		is_valid_sql_generated = False
		retry_counter = 1
		retry_limit = 3

		while not is_valid_sql_generated and retry_counter <= retry_limit:
			# Construct full prompt
			sql_generation_prompt_template = get_sql_generation_prompt_template()
			database_schema = get_database_schema()
			full_prompt = construct_full_prompt(
				system_prompt=sql_generation_prompt_template,
				database_schema=database_schema,
				user_prompt=prompt
			)

			# Convert text (prompt) to SQL
			sql = convert_text_to_sql(full_prompt)

			# Validate sql
			is_valid_sql_generated = validate_sql(sql)

			# Fake loading state
			time.sleep(1)

		if not is_valid_sql_generated:
			st.write(f"Can not generate valid SQL")
			st.stop()
	st.write(f"Generated SQL query: `{sql}`")

	# Step 3: Execute SQL query and get results
	with st.spinner("Executing generated SQL Query", show_time=True):
		try:
			execute_result = execute_sql(sql)
			time.sleep(1)
		except Exception as err:
			st.write(f"Can't execute the generated SQL: {sql} due to {err}")
			st.stop()
	st.write(f"Executing SQL successfully: `{sql}`")

	with st.chat_message("assistant"):
		st.write(f"Text Answer:")

		text_stream, table_data, chart_data = execute_sql(sql)

		text_data = None
		if text_stream is not None:
			text_data = st.write_stream(text_stream)

		res_table = None
		if table_data is not None:
			st.write("Table Answer:")
			res_table = st.dataframe(table_data)
		
		res_chart = None
		if chart_data is not None:
			st.write("Chart Answer:")
			res_chart = st.line_chart(chart_data)

		# Feedback
		st.feedback(
			"stars",
			key=f"feedback_{len(st.session_state.messages)}",
			on_change=save_feedback,
			args=[len(st.session_state.messages)],
		)

	# Add assistant response to chat history
	st.session_state.messages.append(
		{"role": "assistant", "text": text_data, "table": table_data, "chart": chart_data}
	)
