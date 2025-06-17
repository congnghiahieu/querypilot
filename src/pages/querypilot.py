from typing import Optional

import pandas as pd
import streamlit as st

from src.render_utils import generate_text_stream
from src.sql_utils import (
	execute_sql_select,
	get_sqlite_connection,
)
from src.nl2sql.nl2sql import convert_nl2sql
from src.nl2sql.utils.data_builder import load_data
from src.nl2sql.utils.enums import REPR_TYPE, EXAMPLE_TYPE, SELECTOR_TYPE
from src.nl2sql.prompt.prompt_builder import prompt_factory

st.title("Query Pilot")

PATH_DATA = "BIRD_dataset/"
prompt_repr = REPR_TYPE.CODE_REPRESENTATION
example_type = EXAMPLE_TYPE.QA
selector_type = SELECTOR_TYPE.EUC_DISTANCE_QUESTION_MASK
k_shot = 7
MAX_ROWS = 100  # Maximum number of rows to return

# Initialize session state variables
if "initialized" not in st.session_state:
	st.session_state.initialized = False
	st.session_state.data = None
	st.session_state.prompt = None

# Run initialization steps if not done yet
if not st.session_state.initialized:
	with st.spinner("Initializing Query Pilot..."):
		st.session_state.data = load_data("bird", PATH_DATA, None)
		databases = st.session_state.data.get_databases()
		print("start getting prompt")
		st.session_state.prompt = prompt_factory(prompt_repr, k_shot, example_type, selector_type)(data=st.session_state.data, tokenizer="None")
		print("done getting prompt")

		# Mark initialization as complete
		st.session_state.initialized = True

# Initialize chat messages if not present
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
if question := st.chat_input("What do you want to know?"):
	# Step 1: User provides a prompt
	with st.chat_message("user"):
		st.markdown(question)
	st.session_state.messages.append({"role": "user", "text": question})

	# Step 2: UI show loading animation, backend translate text to SQL
	final_sql_select = ""
	is_valid_sql_generated = False

	with get_sqlite_connection("./BIRD_dataset/databases/financial/financial.sqlite") as conn:
		with st.spinner("Translating text to SQL ...", show_time=True):
			retry_counter = 1
			retry_limit = 3

			while not is_valid_sql_generated and retry_counter <= retry_limit:
				# Convert text (prompt) to SQL
				generated_sql_select = convert_nl2sql(question, st.session_state.data, st.session_state.prompt)

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
				# First, get total count of rows
				count_query = f"SELECT COUNT(*) as total_rows FROM ({final_sql_select}) as subquery"
				total_rows = execute_sql_select(conn, count_query).iloc[0]['total_rows']
				
				# Add LIMIT clause if not present
				if "LIMIT" not in final_sql_select.upper():
					final_sql_select = f"{final_sql_select} LIMIT {MAX_ROWS}"
				
				sql_execution_result = execute_sql_select(conn, final_sql_select)
				
				# Add warning if results are truncated
				if total_rows > MAX_ROWS:
					st.warning(f"⚠️ Results are limited to {MAX_ROWS} rows out of {total_rows} total rows. Please refine your query for more specific results.")
				st.write(f"Total rows: {total_rows}")
				
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
