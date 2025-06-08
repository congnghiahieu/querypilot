import pandas as pd
import streamlit as st

from src.session import (
	create_session,
	delete_session,
	export_session,
	load_session_messages,
	load_user_sessions,
	update_session_title,
)


def render_session_management():
	st.header("Session Management")
	if st.button("New Chat"):
		new_session_id = create_session(st.session_state["user_id"])
		st.session_state["current_session_id"] = new_session_id
		st.session_state["messages"] = []
		st.rerun()

	sessions = load_user_sessions(st.session_state["user_id"])
	if sessions.empty:
		st.write("No sessions yet. Start a new chat!")
		return

	# Group sessions by day
	sessions["created_at"] = pd.to_datetime(sessions["created_at"])
	sessions["day"] = sessions["created_at"].apply(lambda x: x.date())
	unique_days = sessions["day"].drop_duplicates().sort_values(ascending=False)

	for day in unique_days:
		st.subheader(f"{day.strftime('%B %d, %Y')}")
		day_sessions = sessions[sessions["day"] == day].sort_values("created_at", ascending=False)
		for _, session in day_sessions.iterrows():
			title = (
				session["title"]
				if session["title"] != "New Chat"
				else f"Chat ({session['created_at'].strftime('%H:%M')})"
			)
			col1, col2, col3 = st.columns([3, 1, 1])
			with col1:
				if st.button(title, key=f"session_{session['session_id']}"):
					st.session_state["current_session_id"] = session["session_id"]
					st.session_state["messages"] = load_session_messages(session["session_id"])
					st.rerun()
			with col2:
				if st.button("✏️", key=f"rename_{session['session_id']}"):
					st.session_state[f"rename_session_{session['session_id']}"] = True
			with col3:
				if st.button("🗑️", key=f"delete_{session['session_id']}"):
					st.session_state[f"confirm_delete_{session['session_id']}"] = True

			if st.session_state.get(f"rename_session_{session['session_id']}", False):
				new_title = st.text_input(
					"New session title", value=title, key=f"rename_input_{session['session_id']}"
				)
				if st.button("Save", key=f"save_rename_{session['session_id']}"):
					update_session_title(session["session_id"], new_title)
					st.session_state[f"rename_session_{session['session_id']}"] = False
					st.rerun()

			if st.session_state.get(f"confirm_delete_{session['session_id']}"):
				st.warning("Are you sure you want to delete this session?")
				col1, col2 = st.columns(2)
				with col1:
					if st.button("Confirm", key=f"confirm_yes_{session['session_id']}"):
						delete_session(session["session_id"])
						if st.session_state["current_session_id"] == session["session_id"]:
							st.session_state["current_session_id"] = None
							st.session_state["messages"] = []
						st.session_state[f"confirm_delete_{session['session_id']}"] = False
						st.rerun()
				with col2:
					if st.button("Cancel", key=f"confirm_no_{session['session_id']}"):
						st.session_state[f"confirm_delete_{session['session_id']}"] = False
						st.rerun()

		if st.session_state.get("current_session_id"):
			st.download_button(
				"Export Chat",
				data=export_session(st.session_state["current_session_id"]),
				file_name=f"chat_{st.session_state['current_session_id']}.md",
				mime="text/markdown",
			)
