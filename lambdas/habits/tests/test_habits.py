import json
import boto3
import handler
from moto import mock_aws

def setup_table():
    dynamodb = boto3.resource(
        "dynamodb",
        region_name="us-east-1"
    )

    table = dynamodb.create_table(
        TableName="one-more-day-habits",
        KeySchema=[
            {
                "AttributeName": "userId",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "SK",
                "KeyType": "RANGE"
            }
        ],
        AttributeDefinitions=[
            {
                "AttributeName": "userId",
                "AttributeType": "S"
            },
            {
                "AttributeName": "SK",
                "AttributeType": "S"
            }
        ],
        BillingMode="PAY_PER_REQUEST"
    )

    table.wait_until_exists()

    # handler.py will use the mocked table
    handler.table = table

    return table


@mock_aws
def test_create_habit():

    table = setup_table()
    # Mock API Gateway + Cognito event
    event = {

        "httpMethod": "POST",
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "aksana-dev"
                }
            }
        },

        "body": json.dumps({
            "habitName": "Drink water",
            "category": "Health"
        })
    }


    response = handler.lambda_handler(event, None)

    assert response["statusCode"] == 201

    body = json.loads(response["body"])


    assert body["habitName"] == "Drink water"
    assert body["category"] == "Health"
    assert body["active"] is True
    assert body["streakCount"] == 0
    assert body["longestStreak"] == 0
    assert body["lastCompletedDate"] is None
    item = table.get_item(
        Key={
            "userId": "aksana-dev",
            "SK": body["SK"]
        }
    )

@mock_aws
def test_create_habit_invalid_category():

    setup_table()

    event = {

        "httpMethod": "POST",

        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "aksana-dev"
                }
            }
        },

        "body": json.dumps({
            "habitName": "Drink water",
            "category": "Sports"
        })
    }

    response = handler.lambda_handler(event, None)

    assert response["statusCode"] == 400

    body = json.loads(response["body"])

    assert body["error"] == "Invalid category"


@mock_aws
def test_list_habits():

    table = setup_table()

    handler.table.put_item(
        Item={
            "userId": "aksana-dev",
            "SK": "HABIT#1",
            "habitId": "1",
            "habitName": "Read",
            "category": "Learning",
            "active": True
        }
    )

    event = {
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "aksana-dev"
                }
            }
        }
    }

    response = handler.list_habits(event)

    assert response["statusCode"] == 200

    habits = json.loads(response["body"])

    assert len(habits) == 1
    assert habits[0]["habitName"] == "Read"


@mock_aws
def test_list_habits_ignores_deleted():

    table = setup_table()

    table.put_item(
        Item={
            "userId": "aksana-dev",
            "SK": "HABIT#1",
            "habitId": "1",
            "habitName": "Read",
            "category": "Learning",
            "active": False
        }
    )

    event = {
        "httpMethod": "GET",
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "aksana-dev"
                }
            }
        }
    }

    response = handler.lambda_handler(event, None)

    habits = json.loads(response["body"])

    assert habits == []

@mock_aws
def test_delete_habit():

    table = setup_table()

    table.put_item(
        Item={
            "userId": "aksana-dev",
            "SK": "HABIT#1",
            "habitId": "1",
            "habitName": "Read",
            "category": "Learning",
            "active": True
        }
    )

    event = {
        "httpMethod": "DELETE",
        "pathParameters": {
            "id": "1"
        },
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "aksana-dev"
                }
            }
        }
    }

    response = handler.lambda_handler(event, None)

    assert response["statusCode"] == 200

    item = table.get_item(
        Key={
            "userId": "aksana-dev",
            "SK": "HABIT#1"
        }
    )["Item"]

    assert item["active"] is False

@mock_aws
def test_delete_sets_deleted_timestamp():

    table = setup_table()

    table.put_item(
        Item={
            "userId": "aksana-dev",
            "SK": "HABIT#1",
            "id": "1",
            "habitName": "Read",
            "category": "Learning",
            "active": True
        }
    )

    event = {
        "httpMethod": "DELETE",
        "pathParameters": {
            "id": "1"
        },
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "aksana-dev"
                }
            }
        }
    }

    handler.lambda_handler(event, None)

    item = table.get_item(
        Key={
            "userId": "aksana-dev",
            "SK": "HABIT#1"
        }
    )["Item"]

    assert item["deletedAt"] is not None