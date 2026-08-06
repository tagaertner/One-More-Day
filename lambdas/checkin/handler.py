
# ─────────────────────────────────────────
# AUTH NOTE — Cognito is live, read before building this page
# ─────────────────────────────────────────
# To get the authenticated user's ID, use:
#   user_id = event['requestContext']['authorizer']['claims']['sub']
#
# Do NOT read userId from the request body — it comes from the verified token.
#
# Example:
#   def lambda_handler(event, context):
#       user_id = event['requestContext']['authorizer']['claims']['sub']
#       http_method = event['httpMethod']
#       ...
# ─────────────────────────────────────────

import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    endpoint_url=os.environ.get("DYNAMODB_ENDPOINT")
)
sns = boto3.client("sns", region_name="us-east-1")
cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")

TABLE_NAME = "one-more-day-habits"
table = dynamodb.Table(TABLE_NAME)
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")


def get_user_id(event):
    """Get authenticated user from Cognito token"""
    return event["requestContext"]["authorizer"]["claims"]["sub"]


def complete_habit(event):
    user_id = get_user_id(event)
    habit_id = event["pathParameters"]["id"]

    body = json.loads(event.get("body") or "{}")
    note = body.get("notes")

    today = datetime.now(timezone.utc).date()
    today_str = today.strftime("%Y-%m-%d")

    # 1. Get the parent HABIT item to check lastCompletedDate / current streak
    habit_response = table.get_item(
        Key={"userId": user_id, "SK": f"HABIT#{habit_id}"}
    )
    habit = habit_response.get("Item")

    if not habit or not habit.get("active", True):
        return {
            "statusCode": 404,
            "body": json.dumps({"status": "error", "message": "habit not found", "code": 404})
        }

    # 2. Conditional write — DynamoDB rejects a duplicate check-in for today
    try:
        table.put_item(
            Item={
                "userId": user_id,
                "SK": f"CHECKIN#{habit_id}#{today_str}",
                "habitId": habit_id,
                "date": today_str,
                "completed": True,
                "notes": note,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            ConditionExpression="attribute_not_exists(SK)"
        )
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "status": "error",
                "message": "habit already completed today",
                "code": 400
            })
        }

    # 3. Streak logic
    last_completed = habit.get("lastCompletedDate")
    current_streak = int(habit.get("streakCount", 0))
    longest_streak = int(habit.get("longestStreak", 0))

    yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    if last_completed == yesterday_str:
        new_streak = current_streak + 1
    else:
        new_streak = 1

    new_longest = max(new_streak, longest_streak)

    table.update_item(
        Key={"userId": user_id, "SK": f"HABIT#{habit_id}"},
        UpdateExpression="""
            SET streakCount = :streak,
                longestStreak = :longest,
                lastCompletedDate = :today
        """,
        ExpressionAttributeValues={
            ":streak": new_streak,
            ":longest": new_longest,
            ":today": today_str,
        }
    )

    # 4. SNS confirmation — event-driven, best-effort
    try:
        if SNS_TOPIC_ARN:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="Habit completed",
                Message=json.dumps({
                    "userId": user_id,
                    "habitId": habit_id,
                    "date": today_str,
                    "streakCount": new_streak,
                })
            )
    except Exception as e:
        print(f"SNS publish failed: {e}")

    # 5. CloudWatch usage metric — best-effort, never blocks the response
    try:
        cloudwatch.put_metric_data(
            Namespace="OneMoreDay/Usage",
            MetricData=[{"MetricName": "CheckinCompleted", "Value": 1, "Unit": "Count"}]
        )
    except Exception as e:
        print(f"CloudWatch metric failed: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "habit marked complete",
            "habitId": habit_id,
            "date": today_str,
            "streakCount": new_streak,
            "longestStreak": new_longest,
        }, default=_decimal_default)
    }


def get_habit_history(event):
    """GET /habits/{id}/history — view recent completion history (if time allows)"""
    user_id = get_user_id(event)
    habit_id = event["pathParameters"]["id"]

    response = table.query(
        KeyConditionExpression=(
            Key("userId").eq(user_id) & Key("SK").begins_with(f"CHECKIN#{habit_id}#")
        )
    )
    items = response.get("Items", [])
    items.sort(key=lambda i: i.get("date", ""), reverse=True)

    history = [
        {"date": i.get("date"), "notes": i.get("notes")}
        for i in items
    ]

    return {
        "statusCode": 200,
        "body": json.dumps({"habitId": habit_id, "history": history}, default=_decimal_default)
    }


def _decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def lambda_handler(event, context):
    method = event.get("httpMethod")
    path = event.get("path", "")

    try:
        if method == "POST" and path.endswith("/complete"):
            return complete_habit(event)

        if method == "GET" and path.endswith("/history"):
            return get_habit_history(event)

        return {
            "statusCode": 405,
            "body": json.dumps({"status": "error", "message": "method not allowed", "code": 405})
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message": str(exc), "code": 500})
        }