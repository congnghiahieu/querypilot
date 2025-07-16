import boto3

from src.core.settings import APP_SETTINGS

identity = boto3.client(
    "sts",
    aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
    region_name=APP_SETTINGS.AWS_REGION,
).get_caller_identity()

print(identity)
