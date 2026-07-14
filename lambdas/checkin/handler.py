import json
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

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Checkin Lambda is live, CI/CD confimred",
            "owner": "Melody"
        })
    }