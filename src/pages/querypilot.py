from typing import Optional

import pandas as pd
import streamlit as st

from src.render_utils import generate_text_stream
from src.sql_utils import (
	execute_sql_select,
	get_sqlite_connection,
)
from src.nl2sql.nl2sql import convert_nl2sql

st.title("Query Pilot")


if "messages" not in st.session_state:
	"""
	st.session_state.messages = [
	{
		"role": "user" | "assistant",
		"text": str",
		"table": None | pd.DataFrame(...),
		"chart": None | pd.DataFrame(...),
	}]
	"""
	st.session_state.messages = []

for _, msg in enumerate(st.session_state.messages):
	with st.chat_message(msg["role"]):
		if "text" in msg:
			st.write(msg["text"])
		if "table" in msg:
			st.dataframe(msg["table"])
		if "chart" in msg:
			st.line_chart(msg["chart"])

# React to user input
if prompt := st.chat_input("What do you want to know?"):
	# Step 1: User provides a prompt
	with st.chat_message("user"):
		st.markdown(prompt)
	st.session_state.messages.append({"role": "user", "text": prompt})

	# Step 2: UI show loading animation, backend translate text to SQL
	final_sql_select = ""
	is_valid_sql_generated = False

	with get_sqlite_connection("./dataset/bull/database_en/ccks_fund/ccks_fund.sqlite") as conn:
		with st.spinner("Translating text to SQL ...", show_time=True):
			retry_counter = 1
			retry_limit = 3

			while not is_valid_sql_generated and retry_counter <= retry_limit:
				# Convert text (prompt) to SQL
				generated_sql_select = convert_nl2sql(prompt)

				# # Validate sql syntax
				# is_valid_sql_in_loop, validate_message = validate_sql_query(conn, generated_sql)
				# if not is_valid_sql_in_loop:
				# 	st.write(f"Can not generate valid SQL in #{retry_counter} attempt(s).")
				# 	st.write(f"Reason: {validate_message}")
				# 	retry_counter += 1
				# 	continue

				# # Analyze sql performance
				# is_performant_query, analyze_message = analyze_query_plan(conn, generated_sql)
				# if not is_performant_query:
				# 	st.write(f"Generated SQL is not performant in #{retry_counter} attempt(s).")
				# 	st.write(f"Reason: {analyze_message}")
				# 	retry_counter += 1
				# 	continue

				is_valid_sql_generated = True
				final_sql_select = generated_sql_select

		if not is_valid_sql_generated:
			st.write(f"Failed to generate valid SQL after {retry_limit} attempts.")
			st.stop()

		st.write(f"Generated SQL query: `{final_sql_select}`")

		# Step 3: Execute SQL query and get results
		sql_execution_result: Optional[pd.DataFrame] = None
		with st.spinner("Executing generated SQL Query", show_time=True):
			try:
				sql_execution_result = execute_sql_select(conn, final_sql_select)
			except Exception as err:
				st.write(f"Can't execute the generated SQL: {final_sql_select} due to {err}")
				st.stop()

		st.write(f"Executing SQL successfully: `{final_sql_select}`")
		assert sql_execution_result is not None, "Execute result should not be None"

		with st.chat_message("assistant"):
			# Mock data generation for text, table, and chart
			text_stream = generate_text_stream("This is a text answer to the query.")
			table_data = sql_execution_result
			chart_data = sql_execution_result

			full_text = ""
			if text_stream is not None:
				st.write(f"Text Answer:")
				full_text = st.write_stream(text_stream)

			if table_data is not None:
				st.write("Table Answer:")
				st.dataframe(table_data)

			#if chart_data is not None:
			#	st.write("Chart Answer:")
			#	st.line_chart(chart_data)

	# Add assistant response to chat history
	st.session_state.messages.append(
		{"role": "assistant", "text": full_text, "table": table_data, "chart": chart_data}
	)
