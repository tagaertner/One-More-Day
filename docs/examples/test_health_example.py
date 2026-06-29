import json
import boto3
import pytest
from moto import mock_aws

''' use this command to run test 
pytest lambdas/health/tests/ -v'''


TABLE_NAME = "one-more-day-habits"
REGION = "us-east-1"


def create_fake_table(dynamodb):
    """Helper — creates a fake DynamoDB table for testing"""
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


@mock_aws
def test_health_returns_ok():
    """Health check returns status ok when all services are connected"""
    import os
    os.environ["DYNAMODB_TABLE"] = TABLE_NAME

    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    create_fake_table(dynamodb)

    logs = boto3.client("logs", region_name=REGION)
    logs.create_log_group(logGroupName="/aws/lambda/one-more-day-health")

    from handler import lambda_handler
    response = lambda_handler({}, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "ok"
    print("✅ test_health_returns_ok passed")


@mock_aws
def test_health_checks_dynamodb():
    """Health check response includes dynamoDB connected status and table name"""
    import os
    os.environ["DYNAMODB_TABLE"] = TABLE_NAME

    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    create_fake_table(dynamodb)

    logs = boto3.client("logs", region_name=REGION)
    logs.create_log_group(logGroupName="/aws/lambda/one-more-day-health")

    from handler import lambda_handler
    response = lambda_handler({}, None)

    body = json.loads(response["body"])
    assert "dynamoDB" in body["services"]
    assert body["services"]["dynamoDB"]["status"] == "connected"
    assert body["services"]["dynamoDB"]["tableName"] == TABLE_NAME
    print("✅ test_health_checks_dynamodb passed")