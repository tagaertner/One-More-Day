import json

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Checkin Lambda is live, CI/CD confimred",
            "owner": "Melody"
        })
    }
