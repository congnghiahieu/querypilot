import io  # Add this import at the top of chat_utils.py
import time
from datetime import datetime

import pandas as pd
import pygwalker as pyg
import streamlit as st
from streamlit_chat import message as st_chat_message

from src.db_utils import get_app_connection, get_target_connection
from src.prompt import construct_full_prompt
from src.prompt_templates import get_sql_generation_prompt_template
from src.render_utils import generate_fake_chart, generate_fake_table
from src.sql_utils import analyze_query_plan
from src.text2sql import convert_text_to_sql


def render_chat_message(message: dict, index):
	is_user = message["role"] == "user"
	content = message.get("content", "")
	st_chat_message(content, is_user=is_user, key=f"msg_{index}", allow_html=True)

	# Deserialize table_data from JSON if it exists
	if message.get("table_data"):
		try:
			table_data = pd.read_json(io.StringIO(message["table_data"]))
			st.markdown("### Table Answer")
			st.dataframe(table_data)
			if st.button("Explore with PyGWalker", key=f"pyg_{index}"):
				pyg.walk(table_data, return_html=True)
		except ValueError as e:
			st.error(f"Error deserializing table data: {e}")

	# Deserialize chart_data from JSON if it exists
	if message.get("chart_data"):
		try:
			chart_data = pd.read_json(io.StringIO(message["chart_data"]))
			st.markdown("### Chart Answer")
			st.line_chart(chart_data)
		except ValueError as e:
			st.error(f"Error deserializing chart data: {e}")

	if message["role"] == "assistant":
		feedback = message.get("feedback", None)
		st.session_state[f"feedback_{index}"] = feedback
		# st.feedback(
		#   "stars",
		#   key=f"feedback_{index}",
		#   disabled=feedback is not None,
		#   on_change=lambda: save_message(
		#       st.session_state["current_session_id"],
		#       message["role"],
		#       message.get("content"),
		#       table_data if message.get("table_data") else None,
		#       chart_data if message.get("chart_data") else None,
		#       st.session_state[f"feedback_{index}"],
		#   ),
		#   args=[index],
		# )


def save_message(
	session_id, role, content, table_data: pd.DataFrame, chart_data: pd.DataFrame, feedback
):
	with get_app_connection() as conn:
		cursor = conn.cursor()
		# Serialize table_data to JSON if it exists and is a DataFrame
		table_data_json = (
			table_data.to_json()
			if table_data is not None and isinstance(table_data, pd.DataFrame)
			else None
		)
		# Serialize chart_data to JSON if it exists and is a DataFrame
		chart_data_json = (
			chart_data.to_json()
			if chart_data is not None and isinstance(chart_data, pd.DataFrame)
			else None
		)

		cursor.execute(
			"""
            INSERT INTO messages (session_id, role, content, table_data, chart_data, feedback, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
			(session_id, role, content, table_data_json, chart_data_json, feedback, datetime.now()),
		)
		conn.commit()


def generate_sql_response(prompt, session_id):
	final_sql_query = ""
	conn = get_target_connection()
	if conn is None:
		st_chat_message(
			"No target database connection configured.",
			is_user=False,
			key="msg_no_connection",
			allow_html=True,
		)
		return "", None, None

	with st.spinner("Translating text to SQL"):
		is_valid_sql_generated = False
		retry_counter = 1
		retry_limit = 3

		while not is_valid_sql_generated and retry_counter <= retry_limit:
			time.sleep(1)
			sql_generation_prompt_template = get_sql_generation_prompt_template()
			# Placeholder for dynamic schema retrieval (implement in src.sql_utils)
			database_schema = "Placeholder schema"  # Replace with actual schema retrieval
			full_prompt = construct_full_prompt(
				system_prompt=sql_generation_prompt_template,
				database_schema=database_schema,
				user_prompt=prompt,
			)
			generated_sql = convert_text_to_sql(full_prompt)
			# is_valid_sql_in_loop, validate_message = validate_sql_query(conn, generated_sql)
			# if not is_valid_sql_in_loop:
			#   message(
			#       f"Can not generate valid SQL in #{retry_counter} attempt(s). Reason: {validate_message}",
			#       is_user=False,
			#       key=f"msg_error_{retry_counter}",
			#       allow_html=True,
			#   )
			#   retry_counter += 1
			#   continue
			is_performant_query, analyze_message = analyze_query_plan(generated_sql)
			if not is_performant_query:
				st_chat_message(
					f"Generated SQL is not performant in #{retry_counter} attempt(s). Reason: {analyze_message}",
					is_user=False,
					key=f"msg_perf_{retry_counter}",
					allow_html=True,
				)
				retry_counter += 1
				continue
			is_valid_sql_generated = True
			final_sql_query = generated_sql

		if not is_valid_sql_generated:
			st_chat_message(
				f"Failed to generate valid SQL after {retry_limit} attempts.",
				is_user=False,
				key="msg_fail",
				allow_html=True,
			)
			return "", None, None

	st_chat_message(
		f"Generated SQL query: ```sql\n{final_sql_query}\n```",
		is_user=False,
		key="msg_sql",
		allow_html=True,
	)

	execute_result = None
	with st.spinner("Executing generated SQL Query"):
		try:
			time.sleep(1)
			execute_result = conn.query(final_sql_query)
		except Exception as err:
			st_chat_message(
				f"Can't execute the generated SQL: ```sql\n{final_sql_query}\n``` due to {err}",
				is_user=False,
				key="msg_exec_error",
				allow_html=True,
			)
			return "", None, None

	st_chat_message(
		f"Executing SQL successfully: ```sql\n{final_sql_query}\n```",
		is_user=False,
		key="msg_exec_success",
		allow_html=True,
	)

	assert execute_result is not None, "Execute result should not be None"

	st_chat_message("### Text Answer", is_user=False, key="msg_text_answer", allow_html=True)
	text_data = "This is a text answer to the query."
	table_data = execute_result if execute_result is not None else generate_fake_table()
	chart_data = (
		pd.DataFrame({"x": range(len(table_data)), "y": table_data.iloc[:, 0]})
		if table_data is not None
		else generate_fake_chart()
	)

	st_chat_message(
		text_data,
		is_user=False,
		key=f"msg_stream_{len(st.session_state['messages'])}",
		allow_html=True,
	)

	if table_data is not None:
		st.markdown("### Table Answer")
		st.dataframe(table_data)
		if st.button("Explore with PyGWalker", key=f"pyg_{len(st.session_state['messages'])}"):
			pyg.walk(table_data, return_html=True)

	if chart_data is not None:
		st.markdown("### Chart Answer")
		st.line_chart(chart_data)

	save_message(session_id, "assistant", text_data, table_data, chart_data, None)
	return text_data, table_data, chart_data
