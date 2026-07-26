# ─── Nilu — Analytics Tests ───
# Replace this placeholder with real tests before merging
# Minimum two tests required — use moto to mock AWS services
# Suggested tests:
#   test_get_stats — GET /stats returns totalCompleted and strongestCategory
#   test_export_report — GET /report/export returns a presigned S3 URL

import json
from datetime import datetime, timedelta, timezone

import boto3
import pytest
from moto import mock_aws

TABLE_NAME = "one-more-day-habits"
REGION = "us-east-1"
USER_ID = "test-user-e4e8a428"


def create_fake_table(dynamodb):
    """Helper — creates a fake DynamoDB table matching the real schema."""
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


def _fake_event():
    """Simulates the event shape API Gateway sends after Cognito auth."""
    return {
        "httpMethod": "GET",
        "path": "/stats",
        "requestContext": {
            "authorizer": {
                "claims": {"sub": USER_ID}
            }
        }
    }


def _date_days_ago(n):
    return (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y-%m-%d")


@mock_aws
def test_get_stats():
    """GET /stats returns totalCompletedThisWeek and strongestCategory"""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = create_fake_table(dynamodb)

    # Seed one active habit
    table.put_item(Item={
        "userId": USER_ID,
        "SK": "HABIT#h1",
        "habitId": "h1",
        "habitName": "Drink water",
        "category": "Health",
        "active": True,
        "streakCount": 2,
        "longestStreak": 5,
    })

    # Seed two completed check-ins this week
    table.put_item(Item={
        "userId": USER_ID,
        "SK": f"CHECKIN#h1#{_date_days_ago(0)}",
        "habitId": "h1",
        "date": _date_days_ago(0),
        "completed": True,
        "notes": None,
    })
    table.put_item(Item={
        "userId": USER_ID,
        "SK": f"CHECKIN#h1#{_date_days_ago(1)}",
        "habitId": "h1",
        "date": _date_days_ago(1),
        "completed": True,
        "notes": None,
    })

    from handler import lambda_handler
    response = lambda_handler(_fake_event(), None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    stats = body["stats"]
    assert stats["totalCompletedThisWeek"] == 2
    assert stats["strongestCategory"] == "Health"
    print("✅ test_get_stats passed")


@mock_aws
def test_get_stats_includes_needs_attention_best_day_and_streaks():
    """GET /stats returns needsAttention, bestDay, and per-habit streak details"""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = create_fake_table(dynamodb)

    # Two habits: h1 completed often this week, h2 never completed
    table.put_item(Item={
        "userId": USER_ID,
        "SK": "HABIT#h1",
        "habitId": "h1",
        "habitName": "Drink water",
        "category": "Health",
        "active": True,
        "streakCount": 3,
        "longestStreak": 10,
    })
    table.put_item(Item={
        "userId": USER_ID,
        "SK": "HABIT#h2",
        "habitId": "h2",
        "habitName": "Read 10 pages",
        "category": "Learning",
        "active": True,
        "streakCount": 0,
        "longestStreak": 2,
    })

    # h1 completed twice this week, h2 never completed
    table.put_item(Item={
        "userId": USER_ID,
        "SK": f"CHECKIN#h1#{_date_days_ago(0)}",
        "habitId": "h1",
        "date": _date_days_ago(0),
        "completed": True,
    })
    table.put_item(Item={
        "userId": USER_ID,
        "SK": f"CHECKIN#h1#{_date_days_ago(1)}",
        "habitId": "h1",
        "date": _date_days_ago(1),
        "completed": True,
    })

    from handler import lambda_handler
    response = lambda_handler(_fake_event(), None)

    assert response["statusCode"] == 200
    stats = json.loads(response["body"])["stats"]

    # h2 has zero completions this week -> should be the one needing attention
    assert stats["needsAttention"]["habitId"] == "h2"
    assert stats["needsAttention"]["completionRate"] == 0.0

    # bestDay should be set to whichever weekday the two h1 check-ins landed on
    assert stats["bestDay"] is not None

    # per-habit streak list should include both habits with correct fields
    habit_ids = {h["habitId"] for h in stats["habits"]}
    assert habit_ids == {"h1", "h2"}
    h1_entry = next(h for h in stats["habits"] if h["habitId"] == "h1")
    assert h1_entry["streakCount"] == 3
    assert h1_entry["longestStreak"] == 10
    assert h1_entry["completionsThisWeek"] == 2
    print("✅ test_get_stats_includes_needs_attention_best_day_and_streaks passed")


@mock_aws
def test_get_stats_with_no_habits_returns_zero_rate():
    """GET /stats with no habits at all should not error and returns 0 rate"""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    create_fake_table(dynamodb)

    from handler import lambda_handler
    response = lambda_handler(_fake_event(), None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    stats = body["stats"]
    assert stats["totalHabits"] == 0
    assert stats["weeklyCompletionRate"] == 0.0
    assert stats["strongestCategory"] is None
    print("✅ test_get_stats_with_no_habits_returns_zero_rate passed")
