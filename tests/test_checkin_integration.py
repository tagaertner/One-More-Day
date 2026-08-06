import pytest
import requests
import os

BASE_URL = "https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod"

@pytest.mark.integration
def test_no_token_returns_401():
    r = requests.post(f"{BASE_URL}/habits/test-id/complete")
    assert r.status_code == 401

@pytest.mark.integration
def test_complete_habit_returns_200(headers):
    # Step 1 — create a real habit
    create = requests.post(
        f"{BASE_URL}/habits",
        headers=headers,
        json={"habitName": "Integration Test Checkin Habit", "category": "Health"}
    )
    assert create.status_code == 201
    habit_id = create.json()["habitId"]

    # Step 2 — check in on it
    r = requests.post(
        f"{BASE_URL}/habits/{habit_id}/complete",
        headers=headers,
        json={}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["habitId"] == habit_id
    assert "streakCount" in body
    assert "date" in body

    # Step 3 — clean up
    requests.delete(f"{BASE_URL}/habits/{habit_id}", headers=headers)

@pytest.mark.integration
def test_duplicate_checkin_returns_400(headers):
    # Step 1 — create a real habit
    create = requests.post(
        f"{BASE_URL}/habits",
        headers=headers,
        json={"habitName": "Integration Test Duplicate Checkin", "category": "Health"}
    )
    assert create.status_code == 201
    habit_id = create.json()["habitId"]

    # Step 2 — first check-in should succeed
    first = requests.post(
        f"{BASE_URL}/habits/{habit_id}/complete",
        headers=headers,
        json={}
    )
    assert first.status_code == 200

    # Step 3 — second check-in same day should fail
    second = requests.post(
        f"{BASE_URL}/habits/{habit_id}/complete",
        headers=headers,
        json={}
    )
    assert second.status_code == 400

    # Step 4 — clean up
    requests.delete(f"{BASE_URL}/habits/{habit_id}", headers=headers)

@pytest.mark.integration
def test_get_history_returns_200(headers):
    # Step 1 — create a real habit
    create = requests.post(
        f"{BASE_URL}/habits",
        headers=headers,
        json={"habitName": "Integration Test History Habit", "category": "Health"}
    )
    assert create.status_code == 201
    habit_id = create.json()["habitId"]

    # Step 2 — check in so history has something
    requests.post(
        f"{BASE_URL}/habits/{habit_id}/complete",
        headers=headers,
        json={}
    )

    # Step 3 — get history
    r = requests.get(
        f"{BASE_URL}/habits/{habit_id}/history",
        headers=headers
    )
    assert r.status_code == 200

    # Step 4 — clean up
    requests.delete(f"{BASE_URL}/habits/{habit_id}", headers=headers)

@pytest.mark.integration
def test_history_has_correct_keys(headers):
    # Step 1 — create a real habit
    create = requests.post(
        f"{BASE_URL}/habits",
        headers=headers,
        json={"habitName": "Integration Test Keys Habit", "category": "Health"}
    )
    assert create.status_code == 201
    habit_id = create.json()["habitId"]

    # Step 2 — check in
    requests.post(
        f"{BASE_URL}/habits/{habit_id}/complete",
        headers=headers,
        json={}
    )

    # Step 3 — verify response keys
    r = requests.get(
        f"{BASE_URL}/habits/{habit_id}/history",
        headers=headers
    )
    assert r.status_code == 200
    body = r.json()
    assert "habitId" in body
    assert "history" in body
    assert isinstance(body["history"], list)

    # Step 4 — clean up
    requests.delete(f"{BASE_URL}/habits/{habit_id}", headers=headers)