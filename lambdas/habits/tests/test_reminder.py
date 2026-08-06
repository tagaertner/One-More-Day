from unittest.mock import MagicMock, patch
import os
import pytest

from handler import send_daily_reminders

# mocking boto3 client for SES
@pytest.fixture
def mock_environment():
    os.environ["COGNITO_USER_POOL_ID"] = "test-pool"
    os.environ["SENDER_EMAIL"] = "noreply@test.com"

@pytest.fixture
def mock_cognito():
    with patch("handler.cognito") as mock:
        yield mock

@pytest.fixture
def mock_ses():
    with patch("handler.ses") as mock:
        yield mock

# @pytest.fixture
# def mock_ses():
#     with patch("handler.ses") as mock:

#         mock.get_identity_verification_attributes.return_value = {
#             "VerificationAttributes": {
#                 "test@example.com": {
#                     "VerificationStatus": "Success"
#                 }
#             }
#         }

#         yield mock

# mocking boto3 client for SES
@pytest.fixture
def mock_habits():
    return [
        {
            "userId": "user-123",
            "SK": "HABIT#1",
            "habitId": "1",
            "habitName": "Drink water",
            "category": "Health",
            "active": True
        },
        {
            "userId": "user-123",
            "SK": "HABIT#2",
            "habitId": "2",
            "habitName": "Exercise",
            "category": "Fitness",
            "active": True
        },
        {
            "userId": "user-456",
            "SK": "HABIT#3",
            "habitId": "3",
            "habitName": "Read book",
            "category": "Learning",
            "active": False
        }
    ]
# Test that the send_daily_reminders function sends an email with the correct habits for each user
def test_send_daily_reminders_sends_email(
    mock_environment,
    mock_habits,
    mock_ses, mock_cognito
):
    # Mock DynamoDB scan
    mock_table_response = {
        "Items": mock_habits
    }

    # Mock Cognito response
    mock_cognito.admin_get_user.return_value = {
    "Username": "user-123",
    "UserAttributes": [
        {
            "Name": "email",
            "Value": "test@example.com"
        }
    ]
}    
    # Mock SES verification
    mock_ses.get_identity_verification_attributes.return_value = {
        "VerificationAttributes": {
            "test@example.com": {
                "VerificationStatus": "Success"
            }
        }
    }

    with patch(
        "handler.table.scan",
        return_value=mock_table_response
    ), patch(
        "handler.record_metric"
    ):

        response = send_daily_reminders()

        # Check Lambda response
        assert response["statusCode"] == 200

        # Check SES called
        mock_ses.send_email.assert_called_once()
        call_args = mock_ses.send_email.call_args.kwargs

        # Verify recipient
        assert (
            call_args["Destination"]["ToAddresses"][0]
            == "test@example.com"
        )
        # Verify email content
        body = (
            call_args["Message"]
            ["Body"]
            ["Text"]
            ["Data"]
        )

        assert "Drink water" in body
        assert "Exercise" in body
        assert "One More Day" in (
            call_args["Message"]
            ["Subject"]
            ["Data"]
        )

# Test that inactive habits are not sent in the email
def test_inactive_habits_are_not_sent(
    mock_environment, mock_ses
):

    inactive_habit = [
        {
            "userId": "user-123",
            "SK": "HABIT#1",
            "habitName": "Wake up early",
            "active": False
        }
    ]

    with patch(
        "handler.table.scan",
        return_value={
            "Items": inactive_habit
        }
    ), patch(
    "handler.record_metric"
):

        response = send_daily_reminders()
    assert response["statusCode"] == 200
    mock_ses.send_email.assert_not_called()

# Test that if Cognito fails, the Lambda does not crash and continues processing other users
def test_cognito_failure_does_not_crash_lambda(
    mock_environment,
    mock_habits
):

    with patch(
        "handler.table.scan",
        return_value={
            "Items": mock_habits[:1]
        }
    ), patch(
        "handler.cognito.admin_get_user",
        side_effect=Exception("Cognito error")
    ), patch(
        "handler.ses.send_email"
    ) as mock_send_email:

        response = send_daily_reminders()
        assert response["statusCode"] == 200
        mock_send_email.assert_not_called()
# Test that if SES fails, the Lambda does not crash and continues processing other users
def test_skip_unverified_email(
    mock_environment,
    mock_ses
):

    # Mock DynamoDB active habit
    mock_habits = [
        {
            "userId": "user-123",
            "SK": "HABIT#1",
            "habitName": "Drink water",
            "active": True
        }
    ]

    # Mock Cognito returning user email
    mock_cognito_response = {
        "UserAttributes": [
            {
                "Name": "email",
                "Value": "test123@example.com"
            }
        ]
    }

    with patch(
        "handler.table.scan",
        return_value={
            "Items": mock_habits
        }
    ), patch(
        "handler.cognito.admin_get_user",
        return_value=mock_cognito_response
    ):

        # SES says email is NOT verified
        mock_ses.get_identity_verification_attributes.return_value = {
            "VerificationAttributes": {
                "test123@example.com": {
                    "VerificationStatus": "Pending"
                }
            }
        }

        response = send_daily_reminders()

        # Lambda should complete successfully
        assert response["statusCode"] == 200

        # Email should NOT be sent
        mock_ses.send_email.assert_not_called()

        # Optional: verify skip counter
        assert response["body"]

# If email doesn't exist in SES, the Lambda should skip sending and not crash
def test_skip_missing_ses_identity(
    mock_environment,
    mock_habits,
    mock_ses,
    mock_cognito
):

    mock_cognito.admin_get_user.return_value = {
        "UserAttributes": [
            {
                "Name": "email",
                "Value": "missing@example.com"
            }
        ]
    }

    mock_ses.get_identity_verification_attributes.return_value = {
        "VerificationAttributes": {}
    }

    with patch(
    "handler.table.scan",
    return_value={
        "Items": mock_habits[:1]
    }
), patch(
    "handler.record_metric"
):
        response = send_daily_reminders()

    assert response["statusCode"] == 200

    mock_ses.send_email.assert_not_called()