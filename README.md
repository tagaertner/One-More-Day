# One More Day — Habit Tracker

A serverless habit tracker built with Python, AWS Lambda, DynamoDB, and Streamlit.

**Live app:** https://one-more-day-kke2zulaouzzarvjyhkrz6.streamlit.app  
**API base URL:** https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod

---

## System Architecture

![System Architecture](docs/system_design.png)

> User → Streamlit Frontend → API Gateway → Lambda Functions → DynamoDB / SNS / S3 / CloudWatch  
> GitHub → GitHub Actions → AWS SAM → AWS infrastructure

---

## Tech Stack

| Layer          | Technology                                            |
| -------------- | ----------------------------------------------------- |
| Language       | Python 3.11                                           |
| Functions      | AWS Lambda — one per engineer                         |
| Database       | DynamoDB — single table, pay per request              |
| API            | AWS API Gateway — all endpoints, API key required     |
| Frontend       | Streamlit — deployed on Community Cloud               |
| Infrastructure | AWS SAM — infrastructure as code                      |
| CI/CD          | GitHub Actions — tests + deploy on every merge to dev |
| Local dev      | Docker + DynamoDB Local                               |

---

## Repo Structure

```
one-more-day/
├── lambdas/
│   ├── habits/          ← Aksana
│   ├── checkin/         ← Melody
│   ├── analytics/       ← Nilu
│   └── health/          ← Tami
├── streamlit/
│   ├── app.py           ← main entry point
│   ├── habits_page.py   ← Aksana
│   ├── checkin_page.py  ← Melody
│   ├── analytics_page.py ← Nilu
│   └── health_page.py   ← Tami
├── infrastructure/
│   └── template.yaml    ← AWS SAM — all infrastructure defined here
├── scripts/
│   ├── seed_data.py     ← seeds DynamoDB with test data
│   └── smoke_test.py    ← confirms all endpoints are live after deploy
├── docker-compose.yml   ← runs all four Lambdas locally
├── .env.example         ← copy this to .env and fill in your values
└── .github/workflows/   ← CI/CD pipeline — do not touch
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
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
DYNAMODB_TABLE=one-more-day-habits
S3_BUCKET_REPORTS=one-more-day-reports
S3_BUCKET_LOGS=one-more-day-habit-logs
SNS_TOPIC_ARN=your_topic_arn_here
API_BASE_URL=https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod
API_KEY=your_api_key_here
STREAMLIT_URL=https://one-more-day-kke2zulaouzzarvjyhkrz6.streamlit.app
LOCAL_USER_ID=your-dev-prefix-here
DYNAMODB_ENDPOINT=http://localhost:8000
```

> **Never commit your .env file. It is already in .gitignore.**

### Step 3 — Set your userId prefix

Each person uses their own prefix so nobody overwrites each other's test data:

| Person | LOCAL_USER_ID |
| ------ | ------------- |
| Aksana | aksana-dev    |
| Melody | melody-dev    |
| Nilu   | nilu-dev      |
| Tami   | tami-dev      |

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

You should see your username in the Arn — `aksana-dev`, `melody-dev`, or `nilu-dev`.

### Step 5 — Confirm DynamoDB connection

```bash
aws dynamodb describe-table --table-name one-more-day-habits
```

You should see the table details. If you get an error check your credentials and region.

### Step 6 — Create your feature branch

```bash
git checkout -b feature/aksana-habits     # Aksana
git checkout -b feature/melody-checkin    # Melody
git checkout -b feature/nilu-analytics    # Nilu
```

---

## Running Locally with Docker

Docker gives everyone the same environment and catches bugs that simple Python testing misses.

### Install Docker

Download Docker Desktop from docker.com/products/docker-desktop. Make sure it is running — you should see the whale icon in your menu bar.

### Start DynamoDB Local + your Lambda

```bash
# Start just DynamoDB local
docker compose up dynamodb-local

# Start your Lambda (in a separate terminal)
docker compose up habits      # Aksana
docker compose up checkin     # Melody
docker compose up analytics   # Nilu
docker compose up health      # Tami

# Or start everything at once
docker compose up
```

### Test your Lambda locally

```bash
# Test health check
curl http://localhost:8004/2015-03-31/functions/function/invocations \
  -d '{}'

# Test habits
curl http://localhost:8001/2015-03-31/functions/function/invocations \
  -d '{"body": "{\"habitName\": \"Drink water\", \"category\": \"Health\", \"userId\": \"aksana-dev\"}"}'
```

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

### Item Types

| Item         | SK format              | Owner          |
| ------------ | ---------------------- | -------------- |
| HABIT        | `HABIT#habitId`        | Aksana creates |
| CHECKIN      | `CHECKIN#habitId#date` | Melody creates |
| USER profile | `USER#profile`         | Seeded by Tami |

### HABIT item fields

```json
{
  "userId": "aksana-dev",
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
  "userId": "melody-dev",
  "SK": "CHECKIN#abc123#2026-06-12",
  "habitId": "abc123",
  "date": "2026-06-12",
  "completed": true,
  "notes": "Feeling great today",
  "timestamp": "2026-06-12T20:00:00Z"
}
```

### Date format rules

- `createdAt`, `timestamp` — UTC ISO format: `2026-06-12T20:00:00Z`
- `date`, `lastCompletedDate` — YYYY-MM-DD: `2026-06-12`

---

## API Endpoints

All endpoints require the `x-api-key` header.

```bash
# Example
curl https://3utc3xlera.execute-api.us-east-1.amazonaws.com/prod/health \
  -H "x-api-key: YOUR_API_KEY"
```

| Method | Endpoint              | Owner  | Description             |
| ------ | --------------------- | ------ | ----------------------- |
| POST   | /habits               | Aksana | Create a habit          |
| GET    | /habits               | Aksana | List all active habits  |
| DELETE | /habits/{id}          | Aksana | Soft delete a habit     |
| POST   | /habits/{id}/complete | Melody | Mark habit complete     |
| GET    | /habits/{id}/history  | Melody | View completion history |
| GET    | /stats                | Nilu   | Weekly progress summary |
| GET    | /report/export        | Nilu   | Export report to S3     |
| GET    | /health               | Tami   | System health check     |

### Standard error response

Every Lambda returns this shape on failure:

```json
{
  "status": "error",
  "message": "habit not found",
  "code": 404
}
```

---

## Running Tests

Each Lambda has a `tests/` folder with at least two tests. Run them locally:

```bash
# Install dependencies
pip install -r lambdas/habits/requirements.txt

# Run tests for your Lambda
pytest lambdas/habits/tests/
pytest lambdas/checkin/tests/
pytest lambdas/analytics/tests/
pytest lambdas/health/tests/
```

Use `moto` to mock AWS services in your tests — your Lambda code does not change, moto intercepts boto3 calls and fakes the responses:

```python
from moto import mock_dynamodb
import boto3

@mock_dynamodb
def test_create_habit():
    # moto creates a fake DynamoDB table
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
    # test your Lambda handler here
    assert True
```

---

## CI/CD Pipeline

When you push code and merge to dev, GitHub Actions automatically:

1. Installs your dependencies
2. Runs your tests — deploy is blocked if tests fail
3. Deploys your Lambda to AWS

You do not trigger this manually. It just fires.

**Watch your pipeline:** github.com/tagaertner/One-More-Day → Actions tab

After every successful deploy, a smoke test runs automatically to confirm all core endpoints are live.

---

## Git Workflow

```bash
# Every day before you start
git checkout dev
git pull origin dev
git checkout feature/your-branch
git merge dev

# Commit often
git add .
git commit -m "add streak increment logic"

# When your feature is ready
git push origin feature/your-branch
# Open a pull request to dev on GitHub
# Tag a teammate to review
# Merge after approval
```

**Rules:**

- Never push directly to dev or main
- Never merge your own pull request
- Never commit your .env file
- Only edit files in your own folder

---

## AWS Resources

| Resource              | Name                               |
| --------------------- | ---------------------------------- |
| DynamoDB table        | one-more-day-habits                |
| S3 reports bucket     | one-more-day-reports               |
| S3 logs bucket        | one-more-day-habit-logs            |
| SNS topic             | one-more-day-checkin-notifications |
| API Gateway           | one-more-day-api                   |
| CloudWatch log groups | /aws/lambda/one-more-day-\*        |
| CloudFormation stack  | one-more-day                       |

---

## Checking CloudWatch Logs

When something breaks on AWS the answer is in CloudWatch:

```bash
# Follow logs live
aws logs tail /aws/lambda/one-more-day-habits --follow
aws logs tail /aws/lambda/one-more-day-checkin --follow
aws logs tail /aws/lambda/one-more-day-analytics --follow
aws logs tail /aws/lambda/one-more-day-health --follow

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/one-more-day-habits \
  --filter-pattern ERROR
```

---

## If Something Is Broken

1. Check CloudWatch logs first
2. Run the health check: `curl .../prod/health -H "x-api-key: ..."`
3. Confirm your AWS credentials are correct: `aws sts get-caller-identity`
4. Confirm you are in us-east-1: `aws configure get region`
5. Post in the group chat the same day — do not sit on a blocker

---

## Contacts

| Person | Role                          | userId prefix |
| ------ | ----------------------------- | ------------- |
| Tami   | Infrastructure + Health Check | tami-dev      |
| Aksana | Habit Management              | aksana-dev    |
| Melody | Daily Check-In                | melody-dev    |
| Nilu   | Analytics + Dashboard         | nilu-dev      |
