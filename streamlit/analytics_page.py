import streamlit as st

"""
One More Day — Progress Dashboard page
Owner: Nilu

Follows the same conventions as habits_page.py / checkin_page.py:
  - exposes a `show()` function, called from app.py after login
  - uses the shared `login_page.call_api()` helper (handles the Cognito
    token automatically — no manual headers, no API key)
"""

import streamlit as st
import login_page


def show():
    st.title("📊 Progress Dashboard")

    if st.button("Refresh stats"):
        st.session_state.pop("stats_payload", None)

    if "stats_payload" not in st.session_state:
        with st.spinner("Loading your weekly stats..."):
            response = login_page.call_api("/stats", method="GET")

        if response.status_code != 200:
            st.error(f"Could not load stats (status {response.status_code}). Try again shortly.")
            return

        st.session_state["stats_payload"] = response.json()

    stats = st.session_state["stats_payload"].get("stats", {})

    col1, col2, col3 = st.columns(3)
    col1.metric("Weekly completion rate", f"{stats.get('weeklyCompletionRate', 0) * 100:.1f}%")
    col2.metric("Total completions this week", stats.get("totalCompletedThisWeek", 0))
    col3.metric("Best day", stats.get("bestDay") or "—")

    st.subheader("Strongest category")
    st.write(stats.get("strongestCategory") or "No completions yet this week.")

    needs_attention = stats.get("needsAttention")
    st.subheader("Needs attention")
    if needs_attention:
        st.warning(
            f"**{needs_attention['habitName']}** — "
            f"{needs_attention['completionRate'] * 100:.1f}% completion rate this week"
        )
    else:
        st.write("No active habits yet.")

    st.subheader("Per-habit streaks")
    habits = stats.get("habits", [])
    if habits:
        st.dataframe(
            [
                {
                    "Habit": h["habitName"],
                    "Category": h["category"],
                    "Current streak": h["streakCount"],
                    "Longest streak": h["longestStreak"],
                    "Completions this week": h["completionsThisWeek"],
                }
                for h in habits
            ],
            use_container_width=True,
        )
    else:
        st.write("No active habits yet.")

    st.divider()
    if st.button("Export weekly report"):
        with st.spinner("Generating your report..."):
            export_response = login_page.call_api("/report/export", method="GET")

        if export_response.status_code != 200:
            st.error(f"Could not export report (status {export_response.status_code}). Try again shortly.")
        else:
            report_url = export_response.json().get("reportUrl")
            st.success("Report exported.")
            st.markdown(f"[Download report]({report_url})")
