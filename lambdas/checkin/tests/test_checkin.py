# ─── Melody — Daily Check-In Tests ───
# Replace this placeholder with real tests before merging
# Minimum two tests required — use moto to mock AWS services
# Suggested tests:
#   test_complete_habit — POST complete returns 200 and writes CHECKIN item
#   test_duplicate_checkin_rejected — second POST on same day returns 400

import json
from datetime import datetime, timedelta, timezone

import boto3
from moto import mock_aws

TABLE_NAME = "one-more-day-habits"
REGION = "us-east-1"
USER_ID = "test-user-melody"


def create_fake_table(dynamodb):
    return dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "userId", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "userId", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )


def _fake_event(habit_id="h1", path_suffix="/complete", method="POST", notes=None):
    return {
        "httpMethod": method,
        "path": f"/habits/{habit_id}{path_suffix}",
        "pathParameters": {"id": habit_id},
        "body": json.dumps({"notes": notes}) if notes is not None else json.dumps({}),
        "requestContext": {
            "authorizer": {
                "claims": {"sub": USER_ID}
            }
        }
    }


@mock_aws
def test_complete_habit():
    """POST /habits/{id}/complete writes a CHECKIN item and increments the streak"""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = create_fake_table(dynamodb)

    table.put_item(Item={
        "userId": USER_ID,
        "SK": "HABIT#h1",
        "habitId": "h1",
        "habitName": "Drink water",
        "category": "Health",
        "active": True,
        "streakCount": 0,
        "longestStreak": 0,
        "lastCompletedDate": None,
    })

    from handler import lambda_handler
    response = lambda_handler(_fake_event(notes="Feeling good"), None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["streakCount"] == 1
    assert body["habitId"] == "h1"

    # confirm the CHECKIN item actually landed in the table
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    item = table.get_item(Key={"userId": USER_ID, "SK": f"CHECKIN#h1#{today_str}"}).get("Item")
    assert item is not None
    assert item["completed"] is True
    assert item["notes"] == "Feeling good"
    print("✅ test_complete_habit passed")


@mock_aws
def test_duplicate_checkin_rejected():
    """A second POST /complete on the same day is rejected, not double-counted"""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = create_fake_table(dynamodb)

    table.put_item(Item={
        "userId": USER_ID,
        "SK": "HABIT#h1",
        "habitId": "h1",
        "habitName": "Drink water",
        "category": "Health",
        "active": True,
        "streakCount": 0,
        "longestStreak": 0,
        "lastCompletedDate": None,
    })

    from handler import lambda_handler
    first = lambda_handler(_fake_event(), None)
    assert first["statusCode"] == 200

    second = lambda_handler(_fake_event(), None)
    assert second["statusCode"] == 400
    body = json.loads(second["body"])
    assert body["status"] == "error"
    print("✅ test_duplicate_checkin_rejected passed")


@mock_aws
def test_streak_increments_from_yesterday():
    """If lastCompletedDate was yesterday, streak increments instead of resetting"""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = create_fake_table(dynamodb)

    yesterday_str = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    table.put_item(Item={
        "userId": USER_ID,
        "SK": "HABIT#h1",
        "habitId": "h1",
        "habitName": "Drink water",
        "category": "Health",
        "active": True,
        "streakCount": 4,
        "longestStreak": 4,
        "lastCompletedDate": yesterday_str,
    })

    from handler import lambda_handler
    response = lambda_handler(_fake_event(), None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["streakCount"] == 5
    assert body["longestStreak"] == 5
    print("✅ test_streak_increments_from_yesterday passed")
