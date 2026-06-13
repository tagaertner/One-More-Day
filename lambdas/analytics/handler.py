import json

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Analytics Lambda is live , CI/CD confirmed",
            "owner": "Nilu"
        })
    }
# CI/CD confirmed
