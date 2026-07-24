import json
from unicodedata import category
import uuid
from datetime import datetime, timezone
import boto3
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal
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

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    endpoint_url=os.environ.get("DYNAMODB_ENDPOINT")
)

TABLE_NAME = "one-more-day-habits"

table = dynamodb.Table(TABLE_NAME)


ALLOWED_CATEGORIES = {
    "Health",
    "Fitness",
    "Mind",
    "Learning",
    "Productivity",
    "Finance"
}


def get_user_id(event):
    """
    Get authenticated user from Cognito token
    """
    return event["requestContext"]["authorizer"]["claims"]["sub"]


def create_habit(event):

    user_id = get_user_id(event)

    body = json.loads(event["body"])

    habit_name = body.get("habitName")
    category = body.get("category")

    if category not in ALLOWED_CATEGORIES:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Invalid category"
            })
        }

    habit_id = str(uuid.uuid4())

    item = {
        "userId": user_id,
        "SK": f"HABIT#{habit_id}",

        "habitId": habit_id,
        "habitName": habit_name,
        "category": category,

        "active": True,

        "createdAt": datetime.now(timezone.utc).isoformat(),
        "deletedAt": None,

        "streakCount": 0,
        "longestStreak": 0,
        "lastCompletedDate": None
    }


    table.put_item(Item=item)


    return {
        "statusCode": 201,
        "body": json.dumps(item)
    }

def list_habits(event):
    user_id = get_user_id(event)
    response = table.query(
        KeyConditionExpression=
            Key("userId").eq(user_id)
            &
            Key("SK").begins_with("HABIT#")
    )

    habits = [
        item for item in response["Items"]
        if item.get("active") is True
    ]

    return {
        "statusCode": 200,
        "body": json.dumps(
        habits,
        default=decimal_to_int
    )
    }


def delete_habit(event):
    user_id = get_user_id(event)
    habit_id = event["pathParameters"]["habitId"]

    response = table.update_item(
        Key={
            "userId": user_id,
            "SK": f"HABIT#{habit_id}"
        },
        UpdateExpression="""
            SET active = :false,
                deletedAt = :date
        """,
        ExpressionAttributeValues={
            ":false": False,
            ":date": datetime.now(timezone.utc).isoformat()
        },
        ReturnValues="ALL_NEW"
    )

    return {
    "statusCode": 200,
    "body": json.dumps(
        {
            "message": "Habit deleted",
            "habit": response["Attributes"]
        },
        default=decimal_to_int
    )
}

def lambda_handler(event, context):

    method = event["httpMethod"]

    if method == "POST":
        return create_habit(event)

    if method == "GET":
        return list_habits(event)

    if method == "DELETE":
        return delete_habit(event)

    return {
        "statusCode": 405,
        "body": json.dumps({
            "error": "Method not allowed"
        })
    }
def decimal_to_int(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError