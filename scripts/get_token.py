import boto3  
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ─── Cognito User Pool Client ID ───
# From .env — originally retrieved via:
# aws cloudformation describe-stacks --stack-name one-more-day --query "Stacks[0].Outputs"
CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID")

if not CLIENT_ID:
    print("❌ COGNITO_CLIENT_ID not found in .env")
    print("   Add it: COGNITO_CLIENT_ID=your_user_pool_client_id_here")
    sys.exit(1)

client = boto3.client('cognito-idp', region_name='us-east-1')

email = input("Email: ")
password = input("Password: ")

try:
    response = client.initiate_auth(
        ClientId=CLIENT_ID,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={'USERNAME': email, 'PASSWORD': password}
    )
    token = response['AuthenticationResult']['IdToken']

    print(f"\n✅ Login successful")
    print(f"\nYour token:\n{token}\n")
    print("Use it like this:")
    print(f'curl https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod/health \\')
    print(f'  -H "Authorization: Bearer {token}"')

except client.exceptions.NotAuthorizedException:
    print("\n❌ Login failed — incorrect email or password")
    sys.exit(1)

except client.exceptions.UserNotFoundException:
    print(f"\n❌ Login failed — no account exists for {email}")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Login failed: {e}")
    sys.exit(1)