import streamlit as st

chat_page = st.Page("./src/pages/chat.py", title="Query Pilot", icon="🤖")

customer_insight_page = st.Page(
	"./src/pages/customer_insight.py", title="Customer Insight", icon="📈"
)

# Set up navigation
pg = st.navigation(
	[
		chat_page,
		# customer_insight_page
	]
)

# Run the selected page
pg.run()
