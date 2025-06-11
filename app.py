import streamlit as st

querypilot_page = st.Page("./src/pages/querypilot.py", title="Query Pilot", icon="🤖")

customer_insight_page = st.Page(
	"./src/pages/customer_insight.py", title="Customer Insight", icon="📈"
)

# Set up navigation
pg = st.navigation(
	[
		querypilot_page,
		# customer_insight_page
	]
)

# Run the selected page
pg.run()
