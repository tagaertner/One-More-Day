import streamlit as st
import login_page

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
    st.header("Daily check-in")
    st.divider()

    # Get all habits
    response = login_page.call_api("/habits", method="GET")

    if response.status_code != 200:
        st.error("Unable to load habits.")
        return

    habits = response.json()

    active_habits = [
        habit for habit in habits
        if habit.get("active", True)
    ]

    if not active_habits:
        st.info("You don't have any active habits yet.")
        return

    # Build dropdown
    options = {
        f"{habit['habitName']} ({habit['category']})": habit
        for habit in active_habits
    }

    st.markdown(
    "<p style='font-size:24px; font-weight:600;'>Select your habit:</p>",
    unsafe_allow_html=True)

    #selected = st.selectbox("", list(options.keys()))
    selected = st.selectbox(
    "Choose today's habit",
    list(options.keys()),
    label_visibility="collapsed")

    habit = options[selected]

    st.subheader(habit["habitName"])

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"Current streak: {habit.get('streakCount', 0)}")

    with col2:
        st.write(f"Longest streak: {habit.get('longestStreak', 0)}")

    notes = st.text_area("Notes (optional)")

    if st.button("Complete Today"):

        complete_response = login_page.call_api(
            f"/habits/{habit['habitId']}/complete",
            method="POST",
            json={
                "notes": notes
            }
        )

        if complete_response.status_code == 200:

            data = complete_response.json()

            st.success("Habit completed!")

            st.write(f"Current streak: {data['streakCount']}")

            st.write(f"Longest streak: {data['longestStreak']}")

            st.rerun()

        else:
            error = complete_response.json()
            st.error(
                error.get(
                    "message",
                    "Unable to complete habit."
                )
            )

    st.divider()

    if st.button("View History"):

        history_response = login_page.call_api(
            f"/habits/{habit['habitId']}/history",
            method="GET"
        )

        if history_response.status_code == 200:

            history = history_response.json().get("history", [])

            if history:
                st.subheader("Recent Check-ins")

                for checkin in history:

                    st.write(f"{checkin['date']}")

                    if checkin.get("notes"):
                        st.caption(checkin["notes"])

            else:
                st.info("No check-in history yet.")

        else:
            st.error("Unable to load history.")
