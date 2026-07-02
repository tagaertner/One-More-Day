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
#   response = login_page.call_api("/habits", method="GET")
#   response = login_page.call_api("/habits", method="POST", json={"habitName": "Drink water", "category": "Health"})
#
# The userId no longer comes from anything you send — it's already
# pulled from the verified token on the Lambda side.
# ─────────────────────────────────────────


def show():
    st.title("Habit Management")
    st.write("Aksana's habits page — coming soon.")# retest smoke test part 3
# retest smoke test part 4
# play it again sam t part 5
# play it again sam part 6
# play it again sam part 7

