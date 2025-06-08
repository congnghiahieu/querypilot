import streamlit as st

from src.db_utils import set_target_connection, test_target_connection


def render_database_config():
	if "show_db_config" not in st.session_state:
		st.session_state["show_db_config"] = False
	with st.expander("Database Configuration", expanded=st.session_state["show_db_config"]):
		db_type = st.selectbox("Select Database Type", ["sqlite", "postgresql", "redshift"])
		host = st.text_input("Host", "localhost" if db_type == "sqlite" else "")
		port = st.number_input(
			"Port",
			value=5432 if db_type in ["postgresql", "redshift"] else 0,
			min_value=0,
			max_value=65535,
		)
		database = st.text_input("Database", "Chinook.db" if db_type == "sqlite" else "")
		username = st.text_input("Username")
		password = st.text_input("Password", type="password")
		if st.button("Test Connection"):
			if test_target_connection(db_type, host, port, database, username, password):
				st.success("Connection successful!")
				set_target_connection(db_type, host, port, database, username, password)
			else:
				st.error("Connection failed!")
		if st.button("Show/Hide Config"):
			st.session_state["show_db_config"] = not st.session_state["show_db_config"]
