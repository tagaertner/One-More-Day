import requests
import os
import sys

BASE_URL = os.environ["API_BASE_URL"]
API_KEY = os.environ["API_KEY"]
headers = {"x-api-key": API_KEY}

def test_health():
    r = requests.get(f"{BASE_URL}/health", headers=headers)
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    body = r.json()
    assert body["status"] == "ok", f"Health status not ok: {body}"
    print("✅ GET /health — ok")

if __name__ == "__main__":
    print("Running smoke tests...")
    try:
        test_health()
        print("\n✅ All smoke tests passed")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Smoke test failed: {e}")
        sys.exit(1)

