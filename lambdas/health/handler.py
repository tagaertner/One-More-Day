import json
import boto3
import os

def lambda_handler(event, context):
    
    dynamodb_status = "connected"
    cloudwatch_status = "connected"
    table_name = os.environ.get('DYNAMODB_TABLE', 'unknown')
    
    # ─── Check DynamoDB ───
    try:
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        dynamodb.describe_table(TableName=table_name)
    except Exception as e:
        dynamodb_status = f"error: {str(e)}"

    # ─── Check CloudWatch ───
    try:
        logs = boto3.client('logs', region_name='us-east-1')
        logs.describe_log_groups(logGroupNamePrefix='/aws/lambda/one-more-day')
    except Exception as e:
        cloudwatch_status = f"error: {str(e)}"

    # ─── Build response ───
    all_healthy = dynamodb_status == "connected" and cloudwatch_status == "connected"
    
    response_body = {
        "status": "ok" if all_healthy else "degraded",
        "services": {
            "dynamoDB": {
                "status": dynamodb_status,
                "tableName": table_name
            },
            "cloudWatch": {
                "status": cloudwatch_status,
                "logGroups": [
                    "/aws/lambda/one-more-day-habits",
                    "/aws/lambda/one-more-day-checkin",
                    "/aws/lambda/one-more-day-analytics",
                    "/aws/lambda/one-more-day-health"
                ]
            },
            "apiGateway": {
                "status": "connected",
                "endpoint": "https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod"
            }
        },
        "routes": {
            "GET /habits": "configured",
            "POST /habits": "configured",
            "DELETE /habits/{id}": "configured",
            "POST /habits/{id}/complete": "configured",
            "GET /habits/{id}/history": "configured",
            "GET /stats": "configured",
            "GET /report/export": "configured",
            "GET /health": "configured"
        },
        "owner": "Tami"
    }

    return {
        "statusCode": 200 if all_healthy else 503,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(response_body)
    }
# smoke test trigger
# demo CI/CD for team
