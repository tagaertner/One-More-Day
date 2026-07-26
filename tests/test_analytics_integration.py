import pytest
import requests

BASE_URL = "https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod"

@pytest.mark.integration
def test_no_token_returns_401():
    r = requests.get(f"{BASE_URL}/stats")
    assert r.status_code == 401



@pytest.mark.integration
def test_get_stats_return_200(headers):
   r = requests.get(f"{BASE_URL}/stats", headers=headers)
   assert r.status_code == 200
   body = r.json()
   assert "stats" in body

@pytest.mark.integration
def test_stats_has_correct_keys(headers):
    r = requests.get(f"{BASE_URL}/stats", headers=headers)
    stats = r.json()["stats"]
    assert "totalHabits" in stats
    assert "weeklyCompletionRate" in stats
    assert "bestDay" in stats
    assert "needsAttention" in stats
    assert "habits" in stats