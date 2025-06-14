import time
from typing import Optional

import pandas as pd
import streamlit as st

from src.prompt import construct_full_prompt
from src.prompt_templates import get_sql_generation_prompt_template
from src.render_utils import generate_text_stream
from src.sql_utils import (
	execute_select_query,
	export_schema_to_string,
	get_sqlite_connection,
)
from src.text2sql import convert_text_to_sql

st.title("Query Pilot")

if "messages" not in st.session_state:
	st.session_state.messages = []


def save_feedback(index: int):
	st.session_state.messages[index]["feedback"] = st.session_state[f"feedback_{index}"]


for i, validate_message in enumerate(st.session_state.messages):
	with st.chat_message(validate_message["role"]):
		if "text" in validate_message:
			st.write(validate_message["text"])
		if "table" in validate_message:
			st.dataframe(validate_message["table"])
		if "chart" in validate_message:
			st.line_chart(validate_message["chart"])

		if validate_message["role"] == "assistant":
			feedback = validate_message.get("feedback", None)
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
	final_sql_query = ""
	is_valid_sql_generated = False

	with get_sqlite_connection("./Chinook.db") as conn:
		with st.spinner("Translating text to SQL", show_time=True):
			retry_counter = 1
			retry_limit = 3

			while not is_valid_sql_generated and retry_counter <= retry_limit:
				time.sleep(1)  # Fake loading state

				# Construct full prompt
				sql_generation_prompt_template = get_sql_generation_prompt_template()
				database_schema = export_schema_to_string(conn)
				full_prompt = construct_full_prompt(
					system_prompt=sql_generation_prompt_template,
					database_schema=database_schema,
					user_prompt=prompt,
				)

				# Convert text (prompt) to SQL
				generated_sql = convert_text_to_sql(full_prompt)

				# # Validate sql
				# is_valid_sql_in_loop, validate_message = validate_sql_query(conn, generated_sql)
				# if not is_valid_sql_in_loop:
				# 	st.write(f"Can not generate valid SQL in #{retry_counter} attempt(s).")
				# 	st.write(f"Reason: {validate_message}")
				# 	retry_counter += 1
				# 	continue

				# # If SQL is performant and valid, break the loop
				# is_performant_query, analyze_message = analyze_query_plan(conn, generated_sql)
				# if not is_performant_query:
				# 	st.write(f"Generated SQL is not performant in #{retry_counter} attempt(s).")
				# 	st.write(f"Reason: {analyze_message}")
				# 	retry_counter += 1
				# 	continue

				is_valid_sql_generated = True
				final_sql_query = generated_sql

		if not is_valid_sql_generated:
			st.write(f"Failed to generate valid SQL after {retry_limit} attempts.")
			st.stop()

		st.write(f"Generated SQL query: `{final_sql_query}`")

		# Step 3: Execute SQL query and get results
		execute_result: Optional[pd.DataFrame] = None
		with st.spinner("Executing generated SQL Query", show_time=True):
			try:
				time.sleep(1)
				execute_result = execute_select_query(conn, final_sql_query)
			except Exception as err:
				st.write(f"Can't execute the generated SQL: {final_sql_query} due to {err}")
				st.stop()

		st.write(f"Executing SQL successfully: `{final_sql_query}`")
		assert execute_result is not None, "Execute result should not be None"

		with st.chat_message("assistant"):
			st.write(f"Text Answer:")

			# Mock data generation for text, table, and chart
			text_stream = generate_text_stream("This is a text answer to the query.")
			table_data = execute_result
			chart_data = execute_result

			full_text = ""
			if text_stream is not None:
				full_text = st.write_stream(text_stream)

			if table_data is not None:
				st.write("Table Answer:")
				st.dataframe(table_data)

			if chart_data is not None:
				st.write("Chart Answer:")
				st.line_chart(chart_data)

			# Feedback
			st.feedback(
				"stars",
				key=f"feedback_{len(st.session_state.messages)}",
				on_change=save_feedback,
				args=[len(st.session_state.messages)],
			)

	# Add assistant response to chat history
	st.session_state.messages.append(
		{"role": "assistant", "text": full_text, "table": table_data, "chart": chart_data}
	)
