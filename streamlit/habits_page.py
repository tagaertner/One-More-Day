import streamlit as st
import login_page

def show():
    st.header("Welcome to One More Day!")
    #st.subheader("Here you can manage your daily habits!")
    st.divider()
    st.subheader("Create a new habit")
    with st.form(key='habit_creation_form'):
        st.text_input("Add a new habit name", key='habit_name')
        st.subheader("Select a category for your habit:")
        st.selectbox("Category", ["Health",
            "Fitness",
            "Mind",
            "Learning",
            "Productivity",
            "Finance"], key='habit_category')
    
        submitted = st.form_submit_button('Create Habit')

    if submitted:
        # Call the API to create a habit
        create_response = login_page.call_api('/habits', method='POST', json={
        'habitName': st.session_state.habit_name,
        'category': st.session_state.habit_category
        })
        if create_response.status_code == 201:
            st.success("Habit created!")
            st.rerun()
        else:
            st.error("Failed to create habit.")

    st.divider()
    st.subheader("My habits")
# Call the API to get the user's habits
    response = login_page.call_api('/habits', method="GET")
    if response.status_code == 200:
        habits = response.json()
        if habits:
            for habit in habits:
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    st.write(habit["habitName"])
                with col2:
                    st.write(habit["category"])
                with col3:
                    if st.button("Delete", key=habit["habitId"]):
                        delete_response = login_page.call_api(f"/habits/{habit['habitId']}", method="DELETE")
                        if delete_response.status_code == 200:
                            st.success("Habit deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete habit.")
            
        else:
            st.write('You have no habits yet.')
    else:
        st.error("Unable to load habits.")




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
