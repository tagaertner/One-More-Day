import requests
import boto3
import os
import time

BASE_URL = "https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod"
CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]
EMAIL = os.environ["SMOKE_TEST_EMAIL"]
PASSWORD = "TamiPass1234"

def get_token():
    client = boto3.client('cognito-idp', region_name='us-east-1')
    response = client.initiate_auth(
        ClientId=CLIENT_ID,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={'USERNAME': EMAIL, 'PASSWORD': PASSWORD}
    )
    return response['AuthenticationResult']['IdToken']

def run_load():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    created_habits = []

    print("Creating habits...")
    categories = ["Health", "Fitness", "Mind", "Learning", "Productivity", "Finance"]
    for i, category in enumerate(categories):
        r = requests.post(f"{BASE_URL}/habits", headers=headers, json={"habitName": f"Load Test Habit {i+1}", "category": category})
        if r.status_code == 201:
            created_habits.append(r.json()["habitId"])
            print(f"Created habit {i+1}")

    print("\nListing habits...")
    for i in range(20):
        requests.get(f"{BASE_URL}/habits", headers=headers)
        print(f"List request {i+1}")
        time.sleep(0.2)

    print("\nChecking in...")
    for habit_id in created_habits:
        r = requests.post(f"{BASE_URL}/habits/{habit_id}/complete", headers=headers, json={})
        print(f"Checkin: {r.status_code}")
        time.sleep(0.2)

    print("\nHitting analytics...")
    for i in range(20):
        requests.get(f"{BASE_URL}/stats", headers=headers)
        print(f"Stats request {i+1}")
        time.sleep(0.2)

    print("\nExporting report...")
    r = requests.get(f"{BASE_URL}/report/export", headers=headers)
    print(f"Export: {r.status_code}")

    print("\nBad requests for 4xx alarms...")
    
    # for i in range(50):
    #     requests.get(f"{BASE_URL}/habits", headers={"Authorization": "Bearer badtoken"})
    #     print(f"Bad request {i+1}")

    print("\nCleaning up...")
    for habit_id in created_habits:
        requests.delete(f"{BASE_URL}/habits/{habit_id}", headers=headers)
        print(f"Deleted {habit_id}")

    print("\nDone! Wait 5-10 minutes then check CloudWatch.")

if __name__ == "__main__":
    run_load()
