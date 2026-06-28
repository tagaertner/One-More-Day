import streamlit as st
import login_page

st.set_page_config(
    page_title="One More Day",
    page_icon="🌅",
    layout="wide"
)

# ─── Require login before anything else ───
if not st.session_state.get('logged_in'):
    login_page.show()
    st.stop()

# ─── Everything below only runs after a successful login ───

import habits_page
import checkin_page
import analytics_page

page = st.sidebar.selectbox(
    "Navigate",
    ["Habits", "Check-in", "Dashboard"]
)

st.sidebar.markdown(f"Logged in as: **{st.session_state.get('email', '')}**")
if st.sidebar.button("Log Out"):
    st.session_state['logged_in'] = False
    st.session_state.pop('token', None)
    st.session_state.pop('refresh_token', None)
    st.rerun()

if page == "Habits":
    habits_page.show()
elif page == "Check-in":
    checkin_page.show()
elif page == "Dashboard":
    analytics_page.show()