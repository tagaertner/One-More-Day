# ─── Nilu — Analytics Tests ───
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


def _fake_event(path="/stats"):
    """Simulates the event shape API Gateway sends after Cognito auth."""
    return {
        "httpMethod": "GET",
        "path": path,
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


REPORT_BUCKET = "one-more-day-reports"


@mock_aws
def test_export_report():
    """GET /report/export writes a JSON report to S3 and returns a presigned URL"""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = create_fake_table(dynamodb)

    s3 = boto3.client("s3", region_name=REGION)
    s3.create_bucket(Bucket=REPORT_BUCKET)

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
    table.put_item(Item={
        "userId": USER_ID,
        "SK": f"CHECKIN#h1#{_date_days_ago(0)}",
        "habitId": "h1",
        "date": _date_days_ago(0),
        "completed": True,
    })

    from handler import lambda_handler
    response = lambda_handler(_fake_event(path="/report/export"), None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["userId"] == USER_ID
    assert "reportUrl" in body
    assert body["reportUrl"].startswith("https://")

    # Confirm something was actually written to S3
    objects = s3.list_objects_v2(Bucket=REPORT_BUCKET, Prefix=f"reports/{USER_ID}/")
    assert objects["KeyCount"] == 1
    print("✅ test_export_report passed")