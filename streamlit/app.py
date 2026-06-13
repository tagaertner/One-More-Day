import streamlit as st
import habits_page
import checkin_page
import analytics_page
import health_page

st.set_page_config(
    page_title="One More Day",
    page_icon="🌄",
    layout="wide"
)

page = st.sidebar.selectbox(
    "Navigate",
    ["Health Check", "Habits", "Check-in", "Dashboard"]
)

if page == "Health Check":
    health_page.show()
elif page == "Habits":
    habits_page.show()
elif page == "Check-in":
    checkin_page.show()
elif page == "Dashboard":
    analytics_page.show()