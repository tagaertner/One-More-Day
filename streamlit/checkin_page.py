import streamlit as st
# ─────────────────────────────────────────
# AUTH NOTE — Cognito is live, read before building this page
# ─────────────────────────────────────────
# When you call the API from this page, use login_page.call_api()
# instead of calling requests directly with an x-api-key header.
# That helper automatically attaches your real login token, and
# silently refreshes it if it has expired — you don't need to
# handle auth yourself.
#
# Example:
#   import login_page
#   response = login_page.call_api("/habits/{id}/complete", method="POST", json={"notes": "..."})
#
# The userId no longer comes from anything you send — it's already
# pulled from the verified token on the Lambda side.
# ─────────────────────────────────────────


def show():
    st.title("Daily Check-In")
    st.write("Melody's check-in page — coming soon.")
