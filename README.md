# One More Day — Habit Tracker

A serverless habit tracker built with Python, AWS Lambda, DynamoDB, and Streamlit.

**Live app:** https://one-more-day-kke2zulaouzzarvjyhkrz6.streamlit.app
**API base URL:** https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod

---

## System Architecture

![System Architecture](docs/system_design.png)

> User → Streamlit Frontend (login required) → API Gateway (Cognito auth) → Lambda Functions → DynamoDB / SNS / S3 / CloudWatch
> GitHub → GitHub Actions → AWS SAM → AWS infrastructure

---

## Tech Stack

| Layer          | Technology                                            |
| -------------- | ----------------------------------------------------- |
| Language       | Python 3.11                                           |
| Functions      | AWS Lambda — one per engineer                         |
| Database       | DynamoDB — single table, pay per request              |
| Auth           | AWS Cognito — real login required on every endpoint   |
| API            | AWS API Gateway — all endpoints, Cognito-authorized   |
| Frontend       | Streamlit — deployed on Community Cloud               |
| Infrastructure | AWS SAM — infrastructure as code                      |
| CI/CD          | GitHub Actions — tests + deploy on every merge to dev |
| Local dev      | Docker + DynamoDB Local                               |

---

## Repo Structure

```
one-more-day/
├── lambdas/
│   ├── habits/              ← Aksana
│   │   ├── handler.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── tests/
│   ├── checkin/             ← Melody
│   │   ├── handler.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── tests/
│   ├── analytics/           ← Nilu
│       ├── handler.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── tests/
├── streamlit/
│   ├── app.py               ← main entry point, requires login first
│   ├── login_page.py        ← Tami — login, sign up, shared call_api() helper
│   ├── habits_page.py       ← Aksana
│   ├── checkin_page.py      ← Melody
│   └── analytics_page.py    ← Nilu
├── docs/
│   └── examples/            ← reference only, not part of the live app
│       ├── health_page_example.py
│       └── test_health_example.py
├── infrastructure/
│   └── template.yaml        ← AWS SAM — all infrastructure defined here
├── scripts/
│   ├── seed_data.py             ← seeds DynamoDB with test data
│   ├── create_cognito_users.py  ← one-time script, creates the 4 real accounts
│   ├── get_token.py             ← self-serve script to get a real login token
│   └── smoke_test.py            ← confirms all endpoints are live after deploy
├── docker-compose.yml       ← runs all four Lambdas locally
├── .env.example             ← copy this to .env and fill in your values
└── .github/workflows/       ← CI/CD pipeline — do not touch
```

---

## Local Setup

### Step 1 — Clone the repo and switch to dev

```bash
git clone https://github.com/tagaertner/One-More-Day.git
cd One-More-Day
git checkout dev
```

### Step 2 — Create your .env file

```bash
cp .env.example .env
```

Open `.env` and fill in your values. Get your credentials from Tami securely.

```bash
# AWS credentials — get these from Tami
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here

# DynamoDB
DYNAMODB_TABLE=one-more-day-habits
DYNAMODB_ENDPOINT=http://localhost:8000

# S3
S3_BUCKET_REPORTS=one-more-day-reports
S3_BUCKET_LOGS=one-more-day-habit-logs

# SNS
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:061361823578:one-more-day-checkin-notifications

# API
API_BASE_URL=https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod

# Cognito — auth is handled by Cognito, not an API key
# Get these from Tami, or run:
# aws cloudformation describe-stacks --stack-name one-more-day --query "Stacks[0].Outputs"
COGNITO_USER_POOL_ID=your_user_pool_id_here
COGNITO_CLIENT_ID=your_user_pool_client_id_here

# Streamlit
STREAMLIT_URL=https://one-more-day-kke2zulaouzzarvjyhkrz6.streamlit.app

# Stretch goal variables — only needed when working on stretch features
ATHENA_WORKGROUP=one-more-day-workgroup
ATHENA_OUTPUT=s3://one-more-day-habit-logs/athena-results/
SES_FROM_EMAIL=one-more-day-notifications@gmail.com
EVENTBRIDGE_RULE=one-more-day-daily-reminder
BEDROCK_MODEL_ID=your_bedrock_model_id_here
```

> **Never commit your .env file. It is already in .gitignore.**

### Step 3 — Log in with your real account

Authentication is handled by AWS Cognito — there is no more shared API key or `userId` prefix to set manually. Each person logs in with their own real email and password through the Streamlit login page.

| Person | Email              |
| ------ | ------------------ |
| Tami   | tami@example.com   |
| Aksana | aksana@example.com |
| Melody | melody@example.com |
| Nilu   | nilu@example.com   |

Get your password from Tami securely. Your real `userId` going forward is your Cognito `sub` — pulled automatically from your login token, never set manually.

### Step 4 — Configure AWS CLI

```bash
aws configure
```

```
AWS Access Key ID: paste your key
AWS Secret Access Key: paste your secret
Default region name: us-east-1
Default output format: json
```

Confirm it works:

```bash
aws sts get-caller-identity
```

### Step 5 — Confirm DynamoDB connection

```bash
aws dynamodb describe-table --table-name one-more-day-habits
```

You should see the table details. If you get an error check your credentials and confirm your region is us-east-1.

### Step 6 — Get a test token (optional, useful for curl/Postman testing)

```bash
python scripts/get_token.py
```

Enter your email and password — this prints a real Cognito token you can use directly in curl commands without opening the full Streamlit app.

### Step 7 — Create your feature branch

```bash
git checkout -b feature/aksana-habits     # Aksana
git checkout -b feature/melody-checkin    # Melody
git checkout -b feature/nilu-analytics    # Nilu
```

---

## Logging In to the App

Open the Streamlit app — you will land on a login screen, not the main app. Two tabs:

- **Log In** — use one of the real accounts above
- **Sign Up** — create a brand new account (no email verification required for MVP — your account works immediately after signing up)

Once logged in your session stays active and silently refreshes itself in the background — you will not be asked to log in again unless you are inactive for 7+ days.

---

## Running Locally with Docker

Docker is already configured — Dockerfiles and docker-compose.yml are set up for you. You just need Docker Desktop installed and running on your machine.

**Install Docker Desktop:** docker.com/products/docker-desktop
Make sure the whale icon is visible in your menu bar before continuing.

### Start DynamoDB Local + your Lambda

```bash
# Terminal 1 — start local DynamoDB
docker compose up dynamodb-local

# Terminal 2 — start your Lambda
docker compose up habits      # Aksana  — runs on port 8001
docker compose up checkin     # Melody  — runs on port 8002
docker compose up analytics   # Nilu    — runs on port 8003
```

### Test your Lambda locally

```bash
# Replace the port with your Lambda's port
# habits=8001, checkin=8002, analytics=8003, health=8004
curl http://localhost:8001/2015-03-31/functions/function/invocations \
  -d '{}'
```

You should see a 200 response. If you do your Lambda is running correctly in Docker.

### Stop everything

```bash
docker compose down
```

---

## DynamoDB Schema

**Table name:** `one-more-day-habits`
**Region:** `us-east-1`

### Primary Key Structure

| Key                | Attribute     | Type   |
| ------------------ | ------------- | ------ |
| Partition key (PK) | userId        | String |
| Sort key (SK)      | recordType#id | String |

`userId` is the real Cognito `sub` value for each person — not a manually chosen prefix.

### Item Types

| Item         | SK format              | Owner          |
| ------------ | ---------------------- | -------------- |
| HABIT        | `HABIT#habitId`        | Aksana creates |
| CHECKIN      | `CHECKIN#habitId#date` | Melody creates |
| USER profile | `USER#profile`         | Seeded by Tami |

### HABIT item fields

```json
{
  "userId": "f458b498-e0c1-7019-2c53-f757e908294a",
  "SK": "HABIT#abc123",
  "habitId": "abc123",
  "habitName": "Drink water",
  "category": "Health",
  "active": true,
  "streakCount": 5,
  "longestStreak": 14,
  "lastCompletedDate": "2026-06-12",
  "createdAt": "2026-04-13T10:00:00Z",
  "deletedAt": null
}
```

### CHECKIN item fields

```json
{
  "userId": "2458b438-1041-70a1-b2d3-15c83f530be1",
  "SK": "CHECKIN#abc123#2026-06-12",
  "habitId": "abc123",
  "date": "2026-06-12",
  "completed": true,
  "notes": "Feeling great today",
  "timestamp": "2026-06-12T20:00:00Z"
}
```

### USER profile fields

```json
{
  "userId": "f458b498-e0c1-7019-2c53-f757e908294a",
  "SK": "USER#profile",
  "email": "aksana@example.com",
  "name": "Aksana",
  "preferredReminderTime": "08:00",
  "timezone": "EST",
  "createdAt": "2026-04-13T10:00:00Z"
}
```

### Date format rules

- `createdAt`, `timestamp` — UTC ISO format: `2026-06-12T20:00:00Z`
- `date`, `lastCompletedDate` — YYYY-MM-DD: `2026-06-12`

### Category values — fixed dropdown

```
Health | Fitness | Mind | Learning | Productivity | Finance
```

Always use exactly one of these six values. Never use a custom category — it will break Nilu's stats aggregation.

---

## API Endpoints

All endpoints require a real Cognito login token in the `Authorization` header. There is no API key anymore.

```bash
# Get a token first
python scripts/get_token.py

# Then use it
curl https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod/health \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

| Method | Endpoint              | Owner  | Description                              |
| ------ | --------------------- | ------ | ---------------------------------------- |
| POST   | /habits               | Aksana | Create a habit                           |
| GET    | /habits               | Aksana | List all active habits                   |
| DELETE | /habits/{id}          | Aksana | Soft delete a habit                      |
| POST   | /habits/{id}/complete | Melody | Mark habit complete                      |
| GET    | /habits/{id}/history  | Melody | View completion history (if time allows) |
| GET    | /stats                | Nilu   | Weekly progress summary                  |
| GET    | /report/export        | Nilu   | Export report to S3                      |

> System health is no longer exposed through the app — see **Observability** below.

### Calling the API from Streamlit

Use the shared helper instead of calling `requests` directly — it automatically attaches your login token and silently refreshes it if expired:

```python
import login_page

response = login_page.call_api("/habits", method="GET")
response = login_page.call_api("/habits", method="POST", json={"habitName": "Drink water", "category": "Health"})
```

The `userId` on the backend now comes from your verified token, not anything you send — every Lambda reads it like this:

```python
user_id = event['requestContext']['authorizer']['claims']['sub']
```

### Standard error response

Every Lambda returns this shape on failure — use the same shape in your code:

```json
{
  "status": "error",
  "message": "habit not found",
  "code": 404
}
```

---

## Observability

System health is monitored through a native **AWS CloudWatch Dashboard** instead of an in-app page — showing this kind of internal infrastructure detail to end users is a security exposure, and a real health check should never trigger side effects (like accidentally creating data).

View it at: AWS Console → CloudWatch → Dashboards → `one-more-day-system-health`
(Requires your IAM credentials — ask Tami if you get an access denied error.)

The dashboard shows Lambda errors, duration, throttles, API Gateway 4xx/5xx rates, and DynamoDB capacity — all pulled from alarms already deployed in `template.yaml`.

A reference copy of the original in-app health check (and its test pattern) is kept at `docs/examples/` for learning purposes only — it is not part of the live app.

---

## Running Tests

Each Lambda has a `tests/` folder with at least two tests. Run them locally before pushing:

```bash
# Install dependencies for your Lambda
pip install -r lambdas/habits/requirements.txt

# Run your tests
pytest lambdas/habits/tests/     # Aksana
pytest lambdas/checkin/tests/    # Melody
pytest lambdas/analytics/tests/  # Nilu
```

### Using moto to mock AWS services

Use `moto` in your tests so you never hit the real DynamoDB table during testing:

```python
from moto import mock_aws
import boto3
import json

@mock_aws
def test_create_habit():
    # moto creates a fake DynamoDB table in memory
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='one-more-day-habits',
        KeySchema=[
            {'AttributeName': 'userId', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'userId', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    # call your Lambda handler with a test event
    from handler import lambda_handler
    event = {'body': json.dumps({'habitName': 'Drink water', 'category': 'Health'})}
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
```

See `docs/examples/test_health_example.py` for a complete working example of this pattern.

---

## CI/CD Pipeline

When you push code and open a pull request to dev, GitHub Actions automatically:

1. Installs your dependencies from `requirements.txt`
2. Runs your tests with pytest — deploy is blocked if any test fails
3. Deploys your Lambda to AWS if tests pass

You do not trigger this manually. It just fires when you merge to dev.

**Watch your pipeline:** github.com/tagaertner/One-More-Day → Actions tab

After every successful deploy a smoke test runs automatically — it logs in with a real Cognito test account and confirms the API is live and authenticated correctly.

---

## Git Workflow

```bash
# Every day before you start — sync with dev
git checkout dev
git pull origin dev
git checkout feature/your-branch
git merge dev

# Commit often with clear messages
git add .
git commit -m "add streak increment logic"

# When your feature is ready — open a pull request
git push origin feature/your-branch
# Go to GitHub → open pull request → base: dev → tag a teammate to review
# Wait for approval → merge
```

**Rules — no exceptions:**

- Never push directly to dev or main
- Never merge your own pull request
- Never commit your .env file
- Only edit files in your own folder
- If you are blocked post in the group chat the same day

---

## AWS Resources

| Resource              | Name                               |
| --------------------- | ---------------------------------- |
| DynamoDB table        | one-more-day-habits                |
| Cognito User Pool     | one-more-day-user                  |
| S3 reports bucket     | one-more-day-reports               |
| S3 logs bucket        | one-more-day-habit-logs            |
| SNS topic             | one-more-day-checkin-notifications |
| API Gateway           | one-more-day-api                   |
| CloudWatch log groups | /aws/lambda/one-more-day-\*        |
| CloudWatch Dashboard  | one-more-day-system-health         |
| CloudFormation stack  | one-more-day                       |
| Athena workgroup      | one-more-day-workgroup             |

---

## Checking CloudWatch Logs

When something breaks on AWS the answer is almost always in CloudWatch:

```bash
# Follow logs live — Ctrl+C to stop
aws logs tail /aws/lambda/one-more-day-habits --follow
aws logs tail /aws/lambda/one-more-day-checkin --follow
aws logs tail /aws/lambda/one-more-day-analytics --follow
aws logs tail /aws/lambda/one-more-day-health --follow

# Filter for errors only
aws logs filter-log-events \
  --log-group-name /aws/lambda/one-more-day-habits \
  --filter-pattern ERROR
```

---

## If Something Is Broken

1. Check CloudWatch logs first — that is where the real error is
2. Get a fresh token and confirm infrastructure is up:

```bash
python scripts/get_token.py

curl https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod/health \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

3. If you get `{"message":"Unauthorized"}` — your token may have expired, get a fresh one
4. Confirm your AWS credentials are correct: `aws sts get-caller-identity`
5. Confirm you are in us-east-1: `aws configure get region`
6. Confirm your .env values match what is in .env.example
7. Post in the group chat the same day — do not sit on a blocker for 24 hours

---

## Contacts

| Person | Role                  | Email              |
| ------ | --------------------- | ------------------ |
| Tami   | Infrastructure + Auth | tami@example.com   |
| Aksana | Habit Management      | aksana@example.com |
| Melody | Daily Check-In        | melody@example.com |
| Nilu   | Analytics + Dashboard | nilu@example.com   |
