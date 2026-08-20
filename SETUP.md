# One More Day — Setup Guide

This document covers two setup paths:

- **Team Setup** — for existing team members who already have AWS credentials
- **Full Setup from Scratch** — for anyone recreating this project from zero

---

## Prerequisites (Both Paths)

Before starting, make sure you have the following installed and configured:

- Python 3.11
- AWS CLI v2 — confirm with `aws --version`
- AWS SAM CLI — confirm with `sam --version`
- Docker Desktop — must be running before any local testing
- Git

---

## Team Setup

For team members who already have AWS credentials.

### Step 1 — Clone the repo

```bash
git clone https://github.com/tagaertner/One-More-Day.git
cd One-More-Day
```

### Step 2 — Configure AWS credentials

Request your AWS access key and secret key from the account owner. Once you have them:

```bash
aws configure
```

Enter your access key, secret key, region `us-east-1`, and output format `json`.

Confirm it works:

```bash
aws sts get-caller-identity
```

### Step 3 — Set up your .env file

Copy the example file:

```bash
cp .env.example .env
```

Fill in the values:

```
COGNITO_CLIENT_ID=1to51psufqaktqgd2iutppi2im
COGNITO_USER_POOL_ID=us-east-1_I90ugMAM0
API_BASE_URL=https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod
```

### Step 4 — Get a Cognito token

```bash
python scripts/get_token.py
```

This logs you in and returns a Bearer token you can use for API testing.

### Step 5 — Run the app locally

```bash
cd streamlit
pip install -r requirements.txt
streamlit run app.py
```

### Step 6 — Branch and push workflow

Always work on a feature branch, never directly on dev or main:

```bash
git checkout dev
git pull origin dev
git checkout -b feature/your-feature-name
```

When done, push and open a PR into dev.

---

## Full Setup from Scratch

For anyone recreating this project in their own AWS account.

### Step 1 — Clone the repo

```bash
git clone https://github.com/tagaertner/One-More-Day.git
cd One-More-Day
```

### Step 2 — Create an AWS account and IAM user

1. Create an AWS account at aws.amazon.com
2. Lock away the root user — create an IAM admin user for daily use
3. Generate access keys for your IAM user
4. Run `aws configure` and enter your credentials

Confirm it works:

```bash
aws sts get-caller-identity
```

### Step 3 — Set up a billing alarm

Go to AWS Console → CloudWatch → Alarms → Create alarm. Set a threshold at $10 so you are not surprised by unexpected charges.

### Step 4 — Deploy the infrastructure

Build and deploy the entire stack with one command:

```bash
cd infrastructure
sam build --template template.yaml
sam deploy --template template.yaml --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM --guided
```

On first run `--guided` will ask you for the stack name and region. Use:

- Stack name: `one-more-day`
- Region: `us-east-1`

After deploy completes, note the outputs:

- `ApiGatewayUrl` — your API base URL
- `UserPoolId` — your Cognito User Pool ID
- `UserPoolClientId` — your Cognito Client ID

### Step 5 — Verify SES email identity

Before reminders can send, verify your sending email address:

```bash
aws ses verify-email-identity --email-address your-email@gmail.com --region us-east-1
```

Check your inbox and click the verification link from AWS. Confirm it worked:

```bash
aws ses get-identity-verification-attributes --identities your-email@gmail.com --region us-east-1
```

Status should show `Success`.

Update `SESEmailIdentity` in `infrastructure/template.yaml` to your email address, then redeploy.

### Step 6 — Create Cognito users

```bash
python scripts/create_cognito_users.py
```

This creates the default user accounts. Edit the script first to use your real email addresses.

### Step 7 — Seed the database

```bash
python scripts/seed_data.py
```

This populates DynamoDB with 30 days of realistic habit and check-in data for all users.

### Step 8 — Enable EventBridge rule

The daily reminder rule deploys as disabled. Enable it when ready:

```bash
aws events enable-rule --name one-more-day-daily-reminder --region us-east-1
```

Or change `State: DISABLED` to `State: ENABLED` in `template.yaml` and redeploy.

### Step 9 — Set up your .env file

```bash
cp .env.example .env
```

Fill in your values from the SAM deploy outputs:

```
COGNITO_CLIENT_ID=your-client-id
COGNITO_USER_POOL_ID=your-user-pool-id
API_BASE_URL=your-api-gateway-url
```

### Step 10 — Run the app locally

```bash
cd streamlit
pip install -r requirements.txt
streamlit run app.py
```

### Step 11 — Deploy to Streamlit Community Cloud

1. Push your repo to GitHub
2. Go to share.streamlit.io
3. Connect your GitHub repo
4. Set the main file path to `streamlit/app.py`
5. Add your secrets in the Streamlit dashboard under Settings → Secrets:

```
COGNITO_CLIENT_ID = "your-client-id"
COGNITO_USER_POOL_ID = "your-user-pool-id"
API_BASE_URL = "your-api-gateway-url"
AWS_ACCESS_KEY_ID = "your-key"
AWS_SECRET_ACCESS_KEY = "your-secret"
AWS_DEFAULT_REGION = "us-east-1"
```

### Step 12 — Set up GitHub Actions secrets

For CI/CD to work, add the following secrets to your GitHub repo under Settings → Secrets → Actions:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION
COGNITO_CLIENT_ID
COGNITO_USER_POOL_ID
SMOKE_TEST_EMAIL
SMOKE_TEST_PASSWORD
API_BASE_URL
```

### Step 13 — Install Playwright for e2e tests

```bash
pip install playwright pytest-playwright
playwright install chromium
```

Run e2e tests:

```bash
pytest tests/e2e/test_ui.py -v
```

---

## Running Tests

### Unit tests

```bash
pytest lambdas/habits/tests/ -v
pytest lambdas/checkin/tests/ -v
pytest lambdas/analytics/tests/ -v
```

### Integration tests

Requires a live deployment and valid Cognito credentials:

```bash
export API_BASE_URL=your-api-url
export COGNITO_CLIENT_ID=your-client-id
export SMOKE_TEST_EMAIL=your-email
export SMOKE_TEST_PASSWORD=your-password
pytest tests/ -v -m integration
```

### Smoke test

```bash
python scripts/smoke_test.py
```

### E2e tests

```bash
pytest tests/e2e/test_ui.py -v
```

---

## Useful Commands

Get a Cognito token for API testing:

```bash
python scripts/get_token.py
```

Run a load test to generate CloudWatch metrics:

```bash
python scripts/load_test.py
```

Check CloudWatch dashboard URL:

```bash
aws cloudformation describe-stacks --stack-name one-more-day \
  --query "Stacks[0].Outputs[?OutputKey=='DashboardURL'].OutputValue" \
  --output text
```

Verify all CloudWatch alarms:

```bash
aws cloudwatch describe-alarms --alarm-name-prefix one-more-day --region us-east-1
```

---

## Architecture

- **Frontend:** Streamlit Community Cloud
- **API:** AWS API Gateway (REST)
- **Auth:** Amazon Cognito (JWT tokens)
- **Functions:** AWS Lambda (Python 3.11)
- **Database:** Amazon DynamoDB (single table design)
- **Messaging:** Amazon SNS
- **Email:** Amazon SES
- **Scheduling:** Amazon EventBridge
- **Storage:** Amazon S3
- **Observability:** Amazon CloudWatch
- **Tracing:** AWS X-Ray
- **IaC:** AWS SAM
- **CI/CD:** GitHub Actions
