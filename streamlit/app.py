import streamlit as st

st.set_page_config(
    page_title="One More Day",
    page_icon="✅",
    layout="wide"
)

page = st.sidebar.selectbox(
    "Navigate",
    ["Health Check", "Habits", "Check-in", "Dashboard"]
)

if page == "Health Check":
    st.title("System Health Check")
    st.write("Tami's health check page coming soon.")

elif page == "Habits":
    st.title("Habit Management")
    st.write("Aksana's habits page coming soon.")

elif page == "Check-in":
    st.title("Daily Check-In")
    st.write("Melody's check-in page coming soon.")

elif page == "Dashboard":
    st.title("Progress Dashboard")
    st.write("Nilu's dashboard page coming soon.")
