from datetime import datetime

import streamlit as st
from streamlit_chat import message as st_chat_message

from src.auth import authenticate_user, check_session, logout, register_user
from src.chat_utils import generate_sql_response, render_chat_message
from src.db_utils import get_app_connection, init_app_db
from src.pages.querypilot.session_management import render_session_management
from src.session import create_session, update_session_title

st.set_page_config(page_title="Query Pilot", layout="centered")

# Initialize app database
init_app_db()

# Check session on load to restore user_id
if not check_session():
	st.session_state.pop("user_id", None)
	st.session_state.pop("session_token", None)
	st.session_state.pop("current_session_id", None)
	st.session_state.pop("messages", None)
else:
	# If session is valid, ensure user_id is set
	if "user_id" not in st.session_state:
		st.session_state["user_id"] = st.session_state.get(
			"user_id", None
		)  # Should be set by check_session

# Authentication and session management UI
if "user_id" not in st.session_state:
	st.title("Login or Register")
	tab1, tab2, tab3 = st.tabs(["Login", "Register", "Logout"])

	with tab1:
		with st.form(key="login_form"):
			username = st.text_input("Username", key="login_username")
			password = st.text_input("Password", key="login_password", type="password")
			submit_button = st.form_submit_button("Login")
			if submit_button:
				user_id = authenticate_user(username, password)
				if user_id:
					st.session_state["user_id"] = user_id
					st.success("Logged in successfully!")
					st.rerun()
				else:
					st.error("Invalid username or password")

	with tab2:
		with st.form(key="register_form"):
			username = st.text_input("Username", key="register_username")
			password = st.text_input("Password", key="register_password", type="password")
			submit_button = st.form_submit_button("Register")
			if submit_button:
				if register_user(username, password):
					st.success("Registered successfully! Please log in.")
				else:
					st.error("Username already exists")

	with tab3:
		if st.button("Logout"):
			logout()
else:
	st.title("Query Pilot")

	# Sidebar
	with st.sidebar:
		st.markdown("---")
		render_session_management()

	# Initialize session state for chat
	if "current_session_id" not in st.session_state or not st.session_state["current_session_id"]:
		st.session_state["current_session_id"] = create_session(st.session_state["user_id"])
		st.session_state["messages"] = []

	# Display chat history
	chat_container = st.container()
	with chat_container:
		for i, message in enumerate(st.session_state["messages"]):
			render_chat_message(message, i)

	# Handle user input
	if prompt := st.chat_input("What is up?"):
		with chat_container:
			st_chat_message(prompt, is_user=True, key=f"msg_{len(st.session_state['messages'])}")
		st.session_state["messages"].append({"role": "user", "content": prompt})
		with get_app_connection() as conn:
			cursor = conn.cursor()
			cursor.execute(
				"""
                INSERT INTO messages (session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
				(st.session_state["current_session_id"], "user", prompt, datetime.now()),
			)
			conn.commit()

		# Update session title with first 30 characters of user prompt
		if len(st.session_state["messages"]) == 1:
			update_session_title(st.session_state["current_session_id"], prompt[:30])

		# Generate SQL response
		with chat_container:
			full_text, table_data, chart_data = generate_sql_response(
				prompt, st.session_state["current_session_id"]
			)
		st.session_state["messages"].append(
			{
				"role": "assistant",
				"content": full_text,
				"table_data": table_data,
				"chart_data": chart_data,
			}
		)
