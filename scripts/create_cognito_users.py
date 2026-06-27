import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Cognito User Pool ID ───
USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")

if not USER_POOL_ID:
    raise ValueError(
        "COGNITO_USER_POOL_ID not found in .env. "
        "Add it: COGNITO_USER_POOL_ID=us-east-1_I90ugMAM0"
    )

client = boto3.client('cognito-idp', region_name='us-east-1')

# ─── The four real accounts ───
# Change these passwords before running if you want something other than the default
users = [
    {"email": "aksana@example.com", "password": "TempPass123!"},
    {"email": "melody@example.com", "password": "TempPass123!"},
    {"email": "nilu@example.com",   "password": "TempPass123!"},
    {"email": "tami@example.com",   "password": "TempPass123!"},
]

for u in users:
    try:
        client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=u["email"],
            UserAttributes=[
                {"Name": "email", "Value": u["email"]},
                {"Name": "email_verified", "Value": "true"}
            ],
            MessageAction="SUPPRESS",   # don't send Cognito's default invite email
            TemporaryPassword=u["password"]
        )
        client.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=u["email"],
            Password=u["password"],
            Permanent=True              # skip force-change-password-on-first-login
        )
        print(f"✅ Created {u['email']}")

    except client.exceptions.UsernameExistsException:
        print(f"⚠️  {u['email']} already exists — skipping")

    except Exception as e:
        print(f"❌ Failed to create {u['email']}: {e}")

print("\nDone. Confirm with:")
print(f"aws cognito-idp list-users --user-pool-id {USER_POOL_ID} --query \"Users[].Username\"")