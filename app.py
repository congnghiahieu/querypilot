import streamlit as st

# Define the pages
querypilot = st.Page("./src/pages/querypilot.py", title="Query Pilot", icon="🤖")
customer_insight = st.Page("./src/pages/customer_insight.py", title="Customer Insight", icon="📈")

# Set up navigation
pg = st.navigation([querypilot, customer_insight])

# Run the selected page
pg.run()
