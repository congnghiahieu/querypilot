import uuid
from datetime import datetime

import pandas as pd

from src.db_utils import get_app_connection


def create_session(user_id: int, title: str = "New Chat") -> str:
	session_id = str(uuid.uuid4())
	with get_app_connection() as conn:
		cursor = conn.cursor()
		cursor.execute(
			"INSERT INTO sessions (session_id, user_id, created_at, title) VALUES (?, ?, ?, ?)",
			(session_id, user_id, datetime.now(), title),
		)
		conn.commit()
	return session_id


def load_user_sessions(user_id: int) -> pd.DataFrame:
	with get_app_connection() as conn:
		return pd.read_sql_query(
			"SELECT session_id, title, created_at FROM sessions WHERE user_id = ?",
			conn,
			params=(user_id,),
		)


def load_session_messages(session_id: str) -> list[dict]:
	with get_app_connection() as conn:
		cursor = conn.cursor()
		cursor.execute(
			"SELECT message_id, session_id, role, content, table_data, chart_data, feedback, created_at "
			"FROM messages WHERE session_id = ?",
			(session_id,),
		)
		rows = cursor.fetchall()
		messages = [
			{
				"message_id": row[0],
				"session_id": row[1],
				"role": row[2],
				"content": row[3],
				"table_data": row[4],
				"chart_data": row[5],
				"feedback": row[6],
				"created_at": row[7],
			}
			for row in rows
		]
	return messages


def update_session_title(session_id: str, title: str):
	with get_app_connection() as conn:
		cursor = conn.cursor()
		cursor.execute("UPDATE sessions SET title = ? WHERE session_id = ?", (title, session_id))
		conn.commit()


def delete_session(session_id: str):
	with get_app_connection() as conn:
		cursor = conn.cursor()
		cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
		cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
		conn.commit()


def export_session(session_id: str) -> str:
	messages = load_session_messages(session_id)
	markdown = f"# Chat Session {session_id}\n\n"
	for msg in messages:
		role = "User" if msg["role"] == "user" else "Assistant"
		markdown += f"## {role}\n{msg['content'] or ''}\n"
		if msg["table_data"]:
			markdown += "\n### Table Data\n```python\n" + msg["table_data"] + "\n```\n"
		if msg["chart_data"]:
			markdown += "\n### Chart Data\n```python\n" + msg["chart_data"] + "\n```\n"
		if msg["feedback"]:
			markdown += f"\n**Feedback**: {msg['feedback']} stars\n"
		markdown += "\n"
	return markdown
