import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

# ─────────────────────────────────────────
# AUTH NOTE — Cognito is live
#   user_id = event['requestContext']['authorizer']['claims']['sub']
#   Do NOT read userId from the request body — it comes from the verified token.
# ─────────────────────────────────────────

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    endpoint_url=os.environ.get("DYNAMODB_ENDPOINT")
)
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

TABLE_NAME = "one-more-day-habits"
table = dynamodb.Table(TABLE_NAME)

WEEK_WINDOW_DAYS = 7  # rolling 7 days ending today


def get_user_id(event):
    """Get authenticated user from Cognito token"""
    return event["requestContext"]["authorizer"]["claims"]["sub"]


def get_active_habits(user_id):
    """Query all active HABIT items for this user."""
    response = table.query(
        KeyConditionExpression=Key("userId").eq(user_id) & Key("SK").begins_with("HABIT#")
    )
    items = response.get("Items", [])
    return [item for item in items if item.get("active", True)]


def get_checkins_in_window(user_id, days=WEEK_WINDOW_DAYS):
    """Query all CHECKIN items for this user, filtered to the last N days."""
    response = table.query(
        KeyConditionExpression=Key("userId").eq(user_id) & Key("SK").begins_with("CHECKIN#")
    )
    items = response.get("Items", [])

    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days - 1)).date()
    in_window = []
    for item in items:
        if not item.get("completed", False):
            continue
        try:
            item_date = datetime.strptime(item["date"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            continue
        if item_date >= cutoff_date:
            in_window.append(item)
    return in_window


def compute_weekly_stats(habits, checkins, days=WEEK_WINDOW_DAYS):
    habit_by_id = {h["habitId"]: h for h in habits}
    completions_by_habit = Counter()
    completions_by_category = Counter()
    completions_by_weekday = Counter()

    for c in checkins:
        habit_id = c.get("habitId")
        completions_by_habit[habit_id] += 1

        habit = habit_by_id.get(habit_id)
        if habit:
            completions_by_category[habit.get("category", "Uncategorized")] += 1

        try:
            weekday_name = datetime.strptime(c["date"], "%Y-%m-%d").strftime("%A")
            completions_by_weekday[weekday_name] += 1
        except (KeyError, ValueError):
            continue

    total_habits = len(habits)
    total_completed = sum(completions_by_habit.values())
    total_possible = total_habits * days
    completion_rate = round(total_completed / total_possible, 4) if total_possible else 0.0

    strongest_category = (
        completions_by_category.most_common(1)[0][0] if completions_by_category else None
    )

    best_day = (
        completions_by_weekday.most_common(1)[0][0] if completions_by_weekday else None
    )

    needs_attention = None
    if habits:
        per_habit_rate = {
            h["habitId"]: completions_by_habit.get(h["habitId"], 0) / days for h in habits
        }
        lowest_habit_id = min(per_habit_rate, key=per_habit_rate.get)
        needs_attention = {
            "habitId": lowest_habit_id,
            "habitName": habit_by_id[lowest_habit_id].get("habitName"),
            "completionRate": round(per_habit_rate[lowest_habit_id], 4),
        }

    habit_streaks = [
        {
            "habitId": h["habitId"],
            "habitName": h.get("habitName"),
            "category": h.get("category"),
            "streakCount": int(h.get("streakCount", 0)),
            "longestStreak": int(h.get("longestStreak", 0)),
            "completionsThisWeek": completions_by_habit.get(h["habitId"], 0),
        }
        for h in habits
    ]

    return {
        "totalHabits": total_habits,
        "totalCompletedThisWeek": total_completed,
        "weeklyCompletionRate": completion_rate,
        "strongestCategory": strongest_category,
        "bestDay": best_day,
        "needsAttention": needs_attention,
        "habits": habit_streaks,
    }


def get_stats(event):
    user_id = get_user_id(event)
    habits = get_active_habits(user_id)
    checkins = get_checkins_in_window(user_id)
    stats = compute_weekly_stats(habits, checkins)

    try:
        cloudwatch.put_metric_data(
            Namespace='OneMoreDay/Usage',
            MetricData=[{'MetricName': 'DashboardViewed', 'Value': 1, 'Unit': 'Count'}]
        )
    except Exception as e:
        print(f"CloudWatch metric failed: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps({"stats": stats}, default=_decimal_default)
    }


def _decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def lambda_handler(event, context):
    http_method = event.get("httpMethod", "GET")
    path = event.get("path", "")

    try:
        if http_method == "GET" and path.endswith("/stats"):
            return get_stats(event)

        return {
            "statusCode": 404,
            "body": json.dumps({"status": "error", "message": "route not found", "code": 404})
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message": str(exc), "code": 500})
        }
