import boto3
from botocore.exceptions import ClientError

from src.core.settings import APP_SETTINGS

USER_POOL_ID = APP_SETTINGS.AWS_COGNITO_USER_POOL_ID
CLIENT_ID = APP_SETTINGS.AWS_COGNITO_CLIENT_ID
CLIENT_SECRET = APP_SETTINGS.AWS_COGNITO_CLIENT_SECRET

cognito = boto3.client(
    "cognito-idp",
    aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
    region_name=APP_SETTINGS.AWS_REGION,
)


def get_secret_hash(user):
    import base64
    import hashlib
    import hmac

    msg = user + CLIENT_ID
    dig = hmac.new(CLIENT_SECRET.encode(), msg.encode(), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def health_cognito():
    try:
        resp = cognito.list_user_pools(MaxResults=10)
        ids = [u["Id"] for u in resp.get("UserPools", [])]
        return {"user_pools": ids}
    except Exception as e:
        return {"error": str(e)}


def signup_test(username="testuser", password="TempP@ss123", email="test@example.com"):
    kwargs = {
        "ClientId": CLIENT_ID,
        "Username": username,
        "Password": password,
        "UserAttributes": [{"Name": "email", "Value": email}],
    }
    if CLIENT_SECRET:
        kwargs["SecretHash"] = get_secret_hash(username)
    try:
        resp = cognito.sign_up(**kwargs)
        return {"signup": True, "status": resp.get("UserConfirmed", False)}
    except ClientError as e:
        return {"signup_error": e.response["Error"]["Message"]}


print(health_cognito())
print(signup_test())

# response = requests.post(
#     "https://ap-southeast-1cilyxp1eo.auth.ap-southeast-1.amazoncognito.com/oauth2/token",
#     data=f"grant_type=client_credentials&client_id={APP_SETTINGS.AWS_COGNITO_CLIENT_ID}&client_secret={APP_SETTINGS.AWS_COGNITO_CLIENT_SECRET}&scope=default-m2m-resource-server-u6rq5l/read",
#     headers={"Content-Type": "application/x-www-form-urlencoded"},
# )
# print(response.json())


# def signup_user(username, password, email):
#     resp = cognito.sign_up(
#         ClientId=CLIENT_ID,
#         Username=username,
#         Password=password,
#         UserAttributes=[{"Name": "email", "Value": email}],
#     )
#     print("Signup", resp)


# def confirm_user(username, code):
#     resp = cognito.confirm_sign_up(ClientId=CLIENT_ID, Username=username, ConfirmationCode=code)
#     print("Confirmed", resp)


# def login_user(username, password):
#     resp = cognito.initiate_auth(
#         ClientId=CLIENT_ID,
#         AuthFlow="USER_PASSWORD_AUTH",
#         AuthParameters={"USERNAME": username, "PASSWORD": password},
#     )
#     return resp["AuthenticationResult"]  # chứa IdToken, AccessToken


# def get_aws_creds(id_token):
#     identity = boto3.client(
#         "cognito-identity",
#         aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
#         aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
#         region_name=APP_SETTINGS.AWS_REGION,
#     )
#     id_resp = identity.get_id(
#         IdentityPoolId=APP_SETTINGS.AWS_COGNITO_IDENTITY_POOL_ID,
#         Logins={
#             f"cognito-idp.{APP_SETTINGS.AWS_REGION}.amazonaws.com/{APP_SETTINGS.AWS_COGNITO_USER_POOL_ID}": id_token
#         },
#     )
#     creds_resp = identity.get_credentials_for_identity(
#         IdentityId=id_resp["IdentityId"],
#         Logins={
#             f"cognito-idp.{APP_SETTINGS.AWS_REGION}.amazonaws.com/{APP_SETTINGS.AWS_COGNITO_USER_POOL_ID}": id_token
#         },
#     )
#     return creds_resp["Credentials"]
