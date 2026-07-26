import pytest
import boto3


@pytest.fixture(scope="module")
def token():
    client = boto3.client("cognito-idp", region_name="us-east-1")
    response = client.initiate_auth(
        ClientId="1to51psufqaktqgd2iutppi2im",
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": "tami@example.com",
            "PASSWORD": "TempPass123!"
        }
    )
    return response["AuthenticationResult"]["IdToken"]

@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}"}