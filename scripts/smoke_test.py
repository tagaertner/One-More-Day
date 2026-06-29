import requests
import os
import sys
import boto3

BASE_URL = os.environ["API_BASE_URL"]
COGNITO_CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]
SMOKE_TEST_EMAIL = os.environ["SMOKE_TEST_EMAIL"]
SMOKE_TEST_PASSWORD = os.environ["SMOKE_TEST_PASSWORD"]


def get_test_token():
    """Logs in as the smoke test account and returns a real Cognito token."""
    client = boto3.client('cognito-idp', region_name='us-east-1')
    response = client.initiate_auth(
        ClientId=COGNITO_CLIENT_ID,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': SMOKE_TEST_EMAIL,
            'PASSWORD': SMOKE_TEST_PASSWORD
        }
    )
    return response['AuthenticationResult']['IdToken']

def test_habits(headers):
    r = requests.get(f"{BASE_URL}/habits", headers=headers)
    assert r.status_code == 200, f"GET /habits failed: {r.status_code}"
    print("✅ GET /habits — ok")
    
if __name__ == "__main__":
    print("Running smoke tests...")
    try:
        token = get_test_token()
        headers = {"Authorization": f"Bearer {token}"}

        test_habits(headers)

        print("\n✅ All smoke tests passed")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Smoke test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Smoke test failed — could not get Cognito token: {e}")
        sys.exit(1)