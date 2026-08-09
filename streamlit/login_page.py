import streamlit as st
import boto3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID")
USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")
BASE_URL = os.environ.get("API_BASE_URL")

client = boto3.client('cognito-idp', region_name='us-east-1')


def show():
    st.title("🌅 Welcome to One More Day")

    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    with tab1:
        login_form()

    with tab2:
        signup_form()


def login_form():
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pw")

    if st.button("Log In"):
        try:
            response = client.initiate_auth(
                ClientId=CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={'USERNAME': email, 'PASSWORD': password}
            )
            st.session_state['token'] = response['AuthenticationResult']['IdToken']
            st.session_state['refresh_token'] = response['AuthenticationResult']['RefreshToken']
            st.session_state['logged_in'] = True
            st.session_state['email'] = email
            st.success("Logged in!")
            st.rerun()

        except client.exceptions.NotAuthorizedException:
            st.error("Incorrect email or password.")
        except client.exceptions.UserNotFoundException:
            st.error("No account exists for this email.")
        except Exception as e:
            st.error(f"Login failed: {e}")


def signup_form():
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_pw")
    st.caption("Password must be at least 8 characters.")
    
    if st.button("Sign Up"):
        if len(password) < 8:
            st.error("Password must be at least 8 characters.")
            return
        try:
            client.sign_up(
                ClientId=CLIENT_ID,
                Username=email,
                Password=password,
                UserAttributes=[{"Name": "email", "Value": email}]
            )

            # Path A: account is UNCONFIRMED by default after self-signup.
            # Auto-confirm it immediately so no code screen is needed.
            client.admin_confirm_sign_up(
                UserPoolId=USER_POOL_ID,
                Username=email
            )

            st.success("Account created! You can log in now.")

        except client.exceptions.UsernameExistsException:
            st.error("An account with this email already exists.")
        except client.exceptions.InvalidPasswordException as e:
            st.error(f"Password does not meet requirements: {e}")
        except Exception as e:
            st.error(f"Sign up failed: {e}")


def call_api(endpoint, method="GET", **kwargs):
    """
    Shared API call helper used by every page (habits, checkin, analytics, health).
    Automatically attaches the current token, and silently refreshes it
    if it has expired — no login screen interruption while the user is active.
    """
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    response = requests.request(
        method, f"{BASE_URL}{endpoint}", headers=headers, **kwargs
    )

    if response.status_code == 401:
        # token expired — silently get a new one, no login screen shown
        try:
            refreshed = client.initiate_auth(
                ClientId=CLIENT_ID,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={'REFRESH_TOKEN': st.session_state['refresh_token']}
            )
            st.session_state['token'] = refreshed['AuthenticationResult']['IdToken']

            # retry the original request with the new token
            headers = {"Authorization": f"Bearer {st.session_state['token']}"}
            response = requests.request(
                method, f"{BASE_URL}{endpoint}", headers=headers, **kwargs
            )
        except Exception:
            # refresh token itself is gone too — this is a REAL logout
            st.session_state['logged_in'] = False
            st.warning("Your session expired — please log in again.")
            st.rerun()

    return response