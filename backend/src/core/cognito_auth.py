from typing import Any, Dict, Optional

import boto3
from jose import jwt

from src.core.settings import APP_SETTINGS


class CognitoAuthService:
    """AWS Cognito Authentication Service"""

    def __init__(self):
        if not APP_SETTINGS.is_aws:
            raise ValueError("Cognito authentication requires AWS environment")

        self.user_pool_id = APP_SETTINGS.AWS_COGNITO_USER_POOL_ID
        self.client_id = APP_SETTINGS.AWS_COGNITO_CLIENT_ID
        self.client_secret = APP_SETTINGS.AWS_COGNITO_CLIENT_SECRET
        self.region = APP_SETTINGS.AWS_COGNITO_REGION

        if not all([self.user_pool_id, self.client_id, self.region]):
            raise ValueError("AWS Cognito configuration is incomplete")

        self.cognito_client = boto3.client(
            "cognito-idp",
            region_name=self.region,
            aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
        )

    def sign_up(self, username: str, password: str, email: str, full_name: str) -> Dict[str, Any]:
        """Register a new user in Cognito"""
        try:
            secret_hash = self._calculate_secret_hash(username)

            response = self.cognito_client.sign_up(
                ClientId=self.client_id,
                Username=username,
                Password=password,
                SecretHash=secret_hash,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "name", "Value": full_name},
                ],
            )

            return {
                "success": True,
                "user_sub": response["UserSub"],
                "message": "User registered successfully. Check email for verification.",
                "confirmation_required": True,
            }

        except self.cognito_client.exceptions.UsernameExistsException:
            return {"success": False, "error": "Username already exists"}
        except self.cognito_client.exceptions.InvalidPasswordException:
            return {"success": False, "error": "Password does not meet requirements"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def confirm_sign_up(self, username: str, confirmation_code: str) -> Dict[str, Any]:
        """Confirm user registration"""
        try:
            secret_hash = self._calculate_secret_hash(username)

            self.cognito_client.confirm_sign_up(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=confirmation_code,
                SecretHash=secret_hash,
            )

            return {"success": True, "message": "User confirmed successfully"}

        except self.cognito_client.exceptions.CodeMismatchException:
            return {"success": False, "error": "Invalid confirmation code"}
        except self.cognito_client.exceptions.ExpiredCodeException:
            return {"success": False, "error": "Confirmation code has expired"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def sign_in(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return tokens"""
        try:
            secret_hash = self._calculate_secret_hash(username)

            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow="ADMIN_NO_SRP_AUTH",
                AuthParameters={
                    "USERNAME": username,
                    "PASSWORD": password,
                    "SECRET_HASH": secret_hash,
                },
            )

            auth_result = response["AuthenticationResult"]

            # Decode the ID token to get user information
            id_token = auth_result["IdToken"]
            user_info = jwt.get_unverified_claims(id_token)

            return {
                "success": True,
                "access_token": auth_result["AccessToken"],
                "id_token": id_token,
                "refresh_token": auth_result["RefreshToken"],
                "token_type": "Bearer",
                "expires_in": auth_result["ExpiresIn"],
                "user_info": {
                    "username": user_info.get("cognito:username"),
                    "email": user_info.get("email"),
                    "full_name": user_info.get("name"),
                    "user_id": user_info.get("sub"),
                    "email_verified": user_info.get("email_verified", False),
                },
            }

        except self.cognito_client.exceptions.NotAuthorizedException:
            return {"success": False, "error": "Invalid username or password"}
        except self.cognito_client.exceptions.UserNotConfirmedException:
            return {
                "success": False,
                "error": "User not confirmed. Please check your email for verification.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify_token(self, access_token: str) -> Dict[str, Any]:
        """Verify and decode access token"""
        try:
            response = self.cognito_client.get_user(AccessToken=access_token)

            username = response["Username"]
            user_attributes = {attr["Name"]: attr["Value"] for attr in response["UserAttributes"]}

            return {
                "success": True,
                "username": username,
                "user_attributes": user_attributes,
                "user_id": user_attributes.get("sub"),
                "email": user_attributes.get("email"),
                "full_name": user_attributes.get("name"),
                "email_verified": user_attributes.get("email_verified") == "true",
            }

        except self.cognito_client.exceptions.NotAuthorizedException:
            return {"success": False, "error": "Invalid or expired token"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def refresh_token(self, refresh_token: str, username: str) -> Dict[str, Any]:
        """Refresh access token"""
        try:
            secret_hash = self._calculate_secret_hash(username)

            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={
                    "REFRESH_TOKEN": refresh_token,
                    "SECRET_HASH": secret_hash,
                },
            )

            auth_result = response["AuthenticationResult"]

            return {
                "success": True,
                "access_token": auth_result["AccessToken"],
                "id_token": auth_result["IdToken"],
                "token_type": "Bearer",
                "expires_in": auth_result["ExpiresIn"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def sign_out(self, access_token: str) -> Dict[str, Any]:
        """Sign out user (revoke tokens)"""
        try:
            self.cognito_client.global_sign_out(AccessToken=access_token)
            return {"success": True, "message": "User signed out successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def forgot_password(self, username: str) -> Dict[str, Any]:
        """Initiate forgot password flow"""
        try:
            secret_hash = self._calculate_secret_hash(username)

            self.cognito_client.forgot_password(
                ClientId=self.client_id,
                Username=username,
                SecretHash=secret_hash,
            )

            return {"success": True, "message": "Password reset code sent to email"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def confirm_forgot_password(
        self, username: str, confirmation_code: str, new_password: str
    ) -> Dict[str, Any]:
        """Confirm forgot password with new password"""
        try:
            secret_hash = self._calculate_secret_hash(username)

            self.cognito_client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=confirmation_code,
                Password=new_password,
                SecretHash=secret_hash,
            )

            return {"success": True, "message": "Password reset successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_secret_hash(self, username: str) -> str:
        """Calculate secret hash for Cognito operations"""
        import base64
        import hashlib
        import hmac

        if not self.client_secret:
            return ""

        message = bytes(username + self.client_id, "utf-8")
        key = bytes(self.client_secret, "utf-8")
        secret_hash = base64.b64encode(
            hmac.new(key, message, digestmod=hashlib.sha256).digest()
        ).decode()

        return secret_hash

    def get_user_groups(self, username: str) -> Dict[str, Any]:
        """Get user groups from Cognito"""
        try:
            response = self.cognito_client.admin_list_groups_for_user(
                UserPoolId=self.user_pool_id,
                Username=username,
            )

            groups = [group["GroupName"] for group in response["Groups"]]

            return {"success": True, "groups": groups}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_user_to_group(self, username: str, group_name: str) -> Dict[str, Any]:
        """Add user to a Cognito group"""
        try:
            self.cognito_client.admin_add_user_to_group(
                UserPoolId=self.user_pool_id,
                Username=username,
                GroupName=group_name,
            )

            return {"success": True, "message": f"User added to group {group_name}"}

        except Exception as e:
            return {"success": False, "error": str(e)}


# Global Cognito service instance
cognito_service = None


def get_cognito_service() -> Optional[CognitoAuthService]:
    """Get Cognito authentication service instance"""
    global cognito_service
    if cognito_service is None and APP_SETTINGS.is_aws:
        try:
            cognito_service = CognitoAuthService()
        except Exception as e:
            print(f"Failed to initialize Cognito service: {e}")
            return None
    return cognito_service
