import json
from unicodedata import category
import uuid
from datetime import datetime, timezone
import boto3
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import logging
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
# adding logging to help with debugging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    endpoint_url=os.environ.get("DYNAMODB_ENDPOINT")
)
ses = boto3.client("ses", region_name="us-east-1")
cognito = boto3.client("cognito-idp", region_name="us-east-1")
cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")

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

    # adding cloudwatch metric for habit creation
    record_metric("HabitCreated")

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
    # Adding CloudWatch metric for habit listing
    record_metric("HabitViewed")

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
    habit_id = event["pathParameters"]["id"]

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
    # adding cloudwatch metric for habit deletion
    record_metric("HabitDeleted")

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

# Helper function to check if email is verified in SES sandbox
def is_email_verified(email):
    try:
        response = ses.get_identity_verification_attributes(
            Identities=[email]
        )

        status = (
            response
            .get("VerificationAttributes", {})
            .get(email, {})
            .get("VerificationStatus")
        )

        return status == "Success"

    except Exception as e:
        logger.error(
            f"Error checking SES verification for {email}: {e}"
        )
        return False

# Lambda function to send daily reminders to users about their habits
def send_daily_reminders():
    USER_POOL_ID = os.environ["COGNITO_USER_POOL_ID"]
    logger.info("Starting daily reminders")

    sent_count = 0
    skipped_count = 0
    failed_count = 0

    # Scan DynamoDB for active habits
    response = table.scan()
    items = response.get("Items", [])

    # Group habits by userId
    users = {}

    # Group habits by user
    for item in items:
        if (
            item["SK"].startswith("HABIT#")
            and item.get("active") is True
        ):
            user_id = item["userId"]

            if user_id not in users:
                users[user_id] = {
                    "habits": []
                }

            users[user_id]["habits"].append(
                item["habitName"]
            )

    logger.info(f"Found {len(users)} users with active habits")

    # Get email from Cognito and send reminders
    for user_id, user_data in users.items():

        try:
            # Query Cognito user by sub
            response = cognito.admin_get_user(
                UserPoolId=USER_POOL_ID,
                Username=user_id
            )

            attributes = {
                attr["Name"]: attr["Value"]
                for attr in response["UserAttributes"]
            }

            email = attributes.get("email")

            if not email:
                logger.warning(f"No email found for user {user_id}")
                failed_count += 1
                continue

        except Exception as e:
            logger.error(f"Error fetching user {user_id} from Cognito: {e}")
            failed_count += 1
            continue
        if not is_email_verified(email):
            logger.info(f"Skipping unverified email: {email}")
            skipped_count += 1
            record_metric("RemindersSkipped")
            continue
        
        # Send email using SES
        try:
            body = (
                "Good morning!\n\n"
                "Here are your habits for today:\n\n"
            )

            for habit in user_data["habits"]:
                body += f"- {habit}\n"

            body += "\n Have a great day and keep your streak alive!"

            logger.info(f"Sending reminder to {email}")

            # Send email using SES
            request = {
                "Source": "onemoredaynotifications@gmail.com",
                "Destination": {
                    "ToAddresses": [
                        email
                    ]
                },
                "Message": {
                    "Subject": {
                        "Data": "One More Day Reminder"
                    },
                    "Body": {
                        "Text": {
                            "Data": body
                        }
                    }
                }
            }
            logger.info(f"SES request source: {request['Source']}")

            ses.send_email(**request)
            sent_count += 1
            # adding cloudwatch metric for reminder sending
            record_metric("RemindersSent")
            logger.info(
                f"Reminder sent successfully to {email}"
            )


        except Exception as e:
            failed_count += 1
            logger.error(
                f"Failed sending reminder "
                f"for user {user_id}: {e}"
            )

    logger.info(
        "Finished sending daily reminders. "
        f"Sent: {sent_count}, "
        f"Skipped: {skipped_count}, "
        f"Failed: {failed_count}"
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Reminder emails processed",
            "sent": sent_count,
            "skipped": skipped_count,
            "failed": failed_count
        })
    }


def lambda_handler(event, context):

    # Scheduled reminder
    if event.get("source") == "aws.events":
        return send_daily_reminders()

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
# Helper function to record CloudWatch metrics
def record_metric(metric_name):
    try:
        cloudwatch.put_metric_data(
            Namespace="OneMoreDay/Usage",
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": 1,
                    "Unit": "Count"
                }
            ]
        )
    except Exception as e:
        logger.error(f"CloudWatch metric failed: {e}")

def decimal_to_int(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError

# trigger smoke test
# trigger smoke test 2
# trigger smoke test 3
# force role update
