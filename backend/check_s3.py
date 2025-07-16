import logging
import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from src.core.settings import APP_SETTINGS

s3 = boto3.client(
    "s3",
    config=Config(signature_version="s3v4"),
    aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
    region_name=APP_SETTINGS.AWS_REGION,
)


def upload_file(file_path, bucket_name, object_key=None):
    if object_key is None:
        object_key = os.path.basename(file_path)
    try:
        s3.upload_file(file_path, bucket_name, object_key)
        return True
    except ClientError as e:
        print("Upload error:", e)
        return False


# print(upload_file("/tmp/test.pdf", APP_SETTINGS.AWS_S3_BUCKET_NAME, "user123/test.pdf"))


def create_presigned_url(bucket_name, object_key, method="get_object", expires=3600):
    """
    Generate a presigned URL (GET or PUT).
    """
    try:
        url = s3.generate_presigned_url(
            ClientMethod=method,
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expires,
        )
    except ClientError as e:
        logging.error(e)
        return None
    return url


# download_url = create_presigned_url(
#     "querypilot-application-s3", "uploads/myfile.pdf", "get_object", 3600
# )
# upload_url = create_presigned_url(
#     "querypilot-application-s3", "uploads/myfile.pdf", "put_object", 3600
# )


def health_s3():
    try:
        resp = s3.list_objects_v2(Bucket=APP_SETTINGS.AWS_S3_BUCKET_NAME, MaxKeys=1)
        exists = "Contents" in resp
        return {"s3_bucket": APP_SETTINGS.AWS_S3_BUCKET_NAME, "exists": exists}
    except Exception as e:
        return {"s3_bucket": APP_SETTINGS.AWS_S3_BUCKET_NAME, "error": str(e)}


def test_presigned():
    key = "test-connection"
    url = s3.generate_presigned_url(
        "put_object", Params={"Bucket": APP_SETTINGS.AWS_S3_BUCKET_NAME, "Key": key}, ExpiresIn=60
    )
    return {"presigned_url": url}


if __name__ == "__main__":
    print(health_s3())
    print(test_presigned())
