import json
from typing import Any, Optional

import boto3

from src.core.settings import APP_SETTINGS


class IAMRoleService:
    """Service for managing IAM roles for users"""

    def __init__(self):
        if not APP_SETTINGS.is_aws:
            raise ValueError("IAM role service requires AWS environment")

        self.iam_client = boto3.client(
            "iam",
            aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
            region_name=APP_SETTINGS.AWS_REGION,
        )

        self.role_prefix = APP_SETTINGS.AWS_IAM_ROLE_PREFIX
        self.base_policy_arn = APP_SETTINGS.AWS_IAM_POLICY_ARN_BASE

    def create_user_role(
        self, user_id: str, username: str, user_level: str = "basic"
    ) -> dict[str, Any]:
        """Create a new IAM role for a user"""
        try:
            role_name = f"{self.role_prefix}{username}-{user_id[:8]}"

            # Define trust policy - allows the user to assume this role
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:root"
                        },
                        "Action": "sts:AssumeRole",
                        "Condition": {"StringEquals": {"sts:ExternalId": user_id}},
                    }
                ],
            }

            # Create the role
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"Role for QueryPilot user {username}",
                Tags=[
                    {"Key": "Application", "Value": "QueryPilot"},
                    {"Key": "UserID", "Value": user_id},
                    {"Key": "Username", "Value": username},
                    {"Key": "UserLevel", "Value": user_level},
                ],
            )

            role_arn = response["Role"]["Arn"]

            # Attach basic policies based on user level
            policies = self._get_policies_for_user_level(user_level)

            for policy_arn in policies:
                try:
                    self.iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
                except Exception as e:
                    print(f"Warning: Could not attach policy {policy_arn}: {e}")

            # Create inline policy for data access (this will be customized per user)
            self._create_user_data_policy(role_name, user_id, user_level)

            return {
                "success": True,
                "role_name": role_name,
                "role_arn": role_arn,
                "message": "User role created successfully",
            }

        except self.iam_client.exceptions.EntityAlreadyExistsException:
            return {"success": False, "error": "Role already exists for this user"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_policies_for_user_level(self, user_level: str) -> list[str]:
        """Get list of managed policies based on user level"""
        base_policies = [
            "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",  # Basic S3 read access
        ]

        if user_level == "basic":
            return base_policies
        elif user_level == "advanced":
            return base_policies + [
                "arn:aws:iam::aws:policy/AmazonAthenaFullAccess",  # Athena access
            ]
        elif user_level == "admin":
            return base_policies + [
                "arn:aws:iam::aws:policy/AmazonAthenaFullAccess",
                "arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess",  # Glue access
            ]
        else:
            return base_policies

    def _create_user_data_policy(self, role_name: str, user_id: str, user_level: str):
        """Create inline policy for user-specific data access"""
        policy_name = f"UserDataAccess-{user_id[:8]}"

        # Base policy - very restrictive by default
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject", "s3:ListBucket"],
                    "Resource": [
                        f"arn:aws:s3:::{APP_SETTINGS.AWS_S3_BUCKET_NAME}/public/*",
                        f"arn:aws:s3:::{APP_SETTINGS.AWS_S3_BUCKET_NAME}/users/{user_id}/*",
                    ],
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "athena:GetQueryExecution",
                        "athena:GetQueryResults",
                        "athena:StartQueryExecution",
                        "athena:StopQueryExecution",
                    ],
                    "Resource": "*",
                    "Condition": {"StringEquals": {"athena:WorkGroup": "primary"}},
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "glue:GetDatabase",
                        "glue:GetTable",
                        "glue:GetTables",
                        "glue:GetPartition",
                        "glue:GetPartitions",
                    ],
                    "Resource": "*",
                },
            ],
        }

        # Add more permissions based on user level
        if user_level in ["advanced", "admin"]:
            policy_document["Statement"].append(
                {"Effect": "Allow", "Action": ["lakeformation:GetDataAccess"], "Resource": "*"}
            )

        try:
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
            )
        except Exception as e:
            print(f"Warning: Could not create inline policy: {e}")

    def update_user_role_permissions(
        self, user_id: str, username: str, new_permissions: list[str]
    ) -> dict[str, Any]:
        """Update user role permissions"""
        try:
            role_name = f"{self.role_prefix}{username}-{user_id[:8]}"
            policy_name = f"UserDataAccess-{user_id[:8]}"

            # Get current policy
            try:
                current_policy = self.iam_client.get_role_policy(
                    RoleName=role_name, PolicyName=policy_name
                )
                policy_document = json.loads(current_policy["PolicyDocument"])
            except:
                # If policy doesn't exist, create new one
                policy_document = {"Version": "2012-10-17", "Statement": []}

            # Update policy based on new permissions
            # This is where you'd implement your specific permission logic
            # For now, we'll add basic datasource permissions

            new_statements = []
            for permission in new_permissions:
                if permission == "financial":
                    new_statements.append(
                        {
                            "Effect": "Allow",
                            "Action": ["s3:GetObject", "s3:ListBucket"],
                            "Resource": [
                                f"arn:aws:s3:::{APP_SETTINGS.AWS_S3_BUCKET_NAME}/financial/*"
                            ],
                        }
                    )
                elif permission == "sales":
                    new_statements.append(
                        {
                            "Effect": "Allow",
                            "Action": ["s3:GetObject", "s3:ListBucket"],
                            "Resource": [f"arn:aws:s3:::{APP_SETTINGS.AWS_S3_BUCKET_NAME}/sales/*"],
                        }
                    )
                # Add more datasource permissions as needed

            policy_document["Statement"].extend(new_statements)

            # Update the policy
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
            )

            return {"success": True, "message": "User permissions updated successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_user_role(self, user_id: str, username: str) -> dict[str, Any]:
        """Delete user IAM role"""
        try:
            role_name = f"{self.role_prefix}{username}-{user_id[:8]}"

            # Detach all managed policies
            try:
                attached_policies = self.iam_client.list_attached_role_policies(RoleName=role_name)
                for policy in attached_policies["AttachedPolicies"]:
                    self.iam_client.detach_role_policy(
                        RoleName=role_name, PolicyArn=policy["PolicyArn"]
                    )
            except:
                pass

            # Delete inline policies
            try:
                inline_policies = self.iam_client.list_role_policies(RoleName=role_name)
                for policy_name in inline_policies["PolicyNames"]:
                    self.iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
            except:
                pass

            # Delete the role
            self.iam_client.delete_role(RoleName=role_name)

            return {"success": True, "message": "User role deleted successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_role_info(self, user_id: str, username: str) -> dict[str, Any]:
        """Get user role information"""
        try:
            role_name = f"{self.role_prefix}{username}-{user_id[:8]}"

            role_info = self.iam_client.get_role(RoleName=role_name)

            # Get attached policies
            attached_policies = self.iam_client.list_attached_role_policies(RoleName=role_name)
            inline_policies = self.iam_client.list_role_policies(RoleName=role_name)

            return {
                "success": True,
                "role_name": role_name,
                "role_arn": role_info["Role"]["Arn"],
                "attached_policies": [
                    p["PolicyName"] for p in attached_policies["AttachedPolicies"]
                ],
                "inline_policies": inline_policies["PolicyNames"],
                "created_date": role_info["Role"]["CreateDate"],
                "tags": role_info["Role"].get("Tags", []),
            }

        except self.iam_client.exceptions.NoSuchEntityException:
            return {"success": False, "error": "User role not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global IAM service instance
iam_service = None


def get_iam_service() -> Optional[IAMRoleService]:
    """Get IAM role service instance"""
    global iam_service
    if iam_service is None and APP_SETTINGS.is_aws:
        try:
            iam_service = IAMRoleService()
        except Exception as e:
            print(f"Failed to initialize IAM service: {e}")
            return None
    return iam_service
