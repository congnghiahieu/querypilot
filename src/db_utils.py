import sqlite3

import bcrypt
import streamlit as st
from sqlalchemy import create_engine


# App database connection
def get_app_connection():
	return sqlite3.connect("./querypilot.db")


def init_app_db():
	with get_app_connection() as conn:
		cursor = conn.cursor()

		cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
		# Check if default user exists before inserting
		cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'default'")
		if cursor.fetchone()[0] == 0:
			default_password = bcrypt.hashpw("defaultpass".encode("utf-8"), bcrypt.gensalt())
			cursor.execute(
				"INSERT INTO users (username, password_hash) VALUES (?, ?)",
				("default", default_password),
			)

		cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                created_at TIMESTAMP,
                title TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

		cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT NOT NULL,
                content TEXT,
                table_data TEXT,
                chart_data TEXT,
                feedback INTEGER,
                created_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

		# New table for authentication sessions
		cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_sessions (
                session_token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

		conn.commit()


# Target database connection management
_target_connection = None


def set_target_connection(db_type, host, port, database, username, password):
	global _target_connection
	if db_type == "sqlite":
		_target_connection = st.connection("target_db", type="sql", url=f"sqlite:///{database}")
	else:
		url = f"{db_type}://{username}:{password}@{host}:{port}/{database}"
		_target_connection = st.connection("target_db", type="sql", url=url)
	st.session_state["target_db_config"] = {
		"db_type": db_type,
		"host": host,
		"port": port,
		"database": database,
		"username": username,
		"password": password,
	}


def test_target_connection(db_type, host, port, database, username, password):
	try:
		if db_type == "sqlite":
			conn = sqlite3.connect(database)
			conn.execute("SELECT 1")
		else:
			url = f"{db_type}://{username}:{password}@{host}:{port}/{database}"
			engine = create_engine(url)
			with engine.connect() as conn:
				conn.execute("SELECT 1")
		return True
	except Exception:
		return False


def get_target_connection():
	return st.connection("target_db", type="sql")

	# global _target_connection
	# if _target_connection is None and "target_db_config" in st.session_state:
	#   set_target_connection(**st.session_state["target_db_config"])
	# return _target_connection
