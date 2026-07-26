import pytest
import requests

BASE_URL = "https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod"

@pytest.mark.integration
def test_no_token_returns_401():
    r = requests.get(f"{BASE_URL}/habits")
    assert r.status_code == 401
    
@pytest.mark.integration
def test_create_habit_returns_201(headers):
    payload = {"habitName": "Integration Test Habit", "category": "Health"}
    r = requests.post(f"{BASE_URL}/habits", json=payload, headers=headers)
    assert r.status_code == 201
    body = r.json()
    assert body["habitName"] == "Integration Test Habit"
    assert body["category"] == "Health"
    assert body["active"] == True
    assert "habitId" in body
       

@pytest.mark.integration
def test_create_habit_invalid_category(headers):
    payload = {"habitName": "Bad Habit", "category": "Sports"}
    r = requests.post(f"{BASE_URL}/habits", json=payload, headers=headers)
    assert r.status_code == 400

@pytest.mark.integration
def test_list_habits_return_200(headers):
    r = requests.get(f"{BASE_URL}/habits", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(),list)
    
@pytest.mark.integration
def test_delete_habit(headers):
    payload = {"habitName": "Delete Me", "category": "Mind"}
    create = requests.post(f"{BASE_URL}/habits", json=payload, headers=headers)
    habit_id = create.json()["habitId"]
    r = requests.delete(f"{BASE_URL}/habits/{habit_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["message"] == "Habit deleted"



