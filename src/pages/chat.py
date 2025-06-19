import streamlit as st
from src.components.chat_ui import QueryPilotChat

st.title("Query Pilot")

# Initialize and render the chat interface
chat_interface = QueryPilotChat()
chat_interface.initialize_session_state()
chat_interface.initialize_data_and_prompt()

chat_interface.render_chat_history()
if question := st.chat_input("What do you want to know?"):
	chat_interface.process_user_question(question)
