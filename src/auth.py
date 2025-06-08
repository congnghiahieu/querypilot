import sqlite3
import uuid
from datetime import datetime, timedelta

import bcrypt
import streamlit as st

from src.db_utils import get_app_connection


def register_user(username: str, password: str) -> bool:
	if len(username) < 3 or len(password) < 6:
		return False
	try:
		with get_app_connection() as conn:
			cursor = conn.cursor()
			cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
			if cursor.fetchone():
				st.error(f"Username '{username}' is already taken. Please choose another.")
				return False
			password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
			cursor.execute(
				"INSERT INTO users (username, password_hash) VALUES (?, ?)",
				(username, password_hash),
			)
			conn.commit()
		return True
	except sqlite3.IntegrityError:
		st.error(f"Registration failed: Username '{username}' may already exist or is invalid.")
		return False
	except Exception as e:
		st.error(f"Registration error: {str(e)}")
		return False


def authenticate_user(username: str, password: str) -> int:
	with get_app_connection() as conn:
		cursor = conn.cursor()
		cursor.execute("SELECT user_id, password_hash FROM users WHERE username = ?", (username,))
		result = cursor.fetchone()
		if result and bcrypt.checkpw(password.encode("utf-8"), result[1]):
			# Create a new session token
			session_token = str(uuid.uuid4())
			expires_at = datetime.now() + timedelta(hours=24)  # Session valid for 24 hours
			cursor.execute(
				"INSERT INTO auth_sessions (session_token, user_id, expires_at) VALUES (?, ?, ?)",
				(session_token, result[0], expires_at),
			)
			conn.commit()
			st.session_state["session_token"] = session_token  # Store token in session state
			return result[0]
		return None


def check_session() -> bool:
	# If session_token is in st.session_state, use it first
	if "session_token" in st.session_state:
		with get_app_connection() as conn:
			cursor = conn.cursor()
			cursor.execute(
				"SELECT user_id FROM auth_sessions WHERE session_token = ? AND expires_at > ?",
				(st.session_state["session_token"], datetime.now()),
			)
			result = cursor.fetchone()
			if result:
				st.session_state["user_id"] = result[0]
				return True
	else:
		# If not in st.session_state, check for any active session for the user
		if "user_id" in st.session_state:
			with get_app_connection() as conn:
				cursor = conn.cursor()
				cursor.execute(
					"SELECT session_token, user_id FROM auth_sessions WHERE user_id = ? AND expires_at > ?",
					(st.session_state["user_id"], datetime.now()),
				)
				result = cursor.fetchone()
				if result:
					st.session_state["session_token"] = result[0]
					st.session_state["user_id"] = result[1]
					return True
	return False


def logout():
	if "session_token" in st.session_state:
		with get_app_connection() as conn:
			cursor = conn.cursor()
			cursor.execute(
				"DELETE FROM auth_sessions WHERE session_token = ?",
				(st.session_state["session_token"],),
			)
			conn.commit()
		del st.session_state["session_token"]
		del st.session_state["user_id"]
		st.rerun()
