import logging
import os

import boto3
from backend.src.core.settings import APP_SETTINGS
from botocore.config import Config
from botocore.exceptions import ClientError

s3 = boto3.client("s3")


def upload_file(file_path, bucket_name, object_key=None):
    if object_key is None:
        object_key = os.path.basename(file_path)
    try:
        s3.upload_file(file_path, bucket_name, object_key)
        return True
    except ClientError as e:
        print("Upload error:", e)
        return False


# Test
print(upload_file("/tmp/test.pdf", APP_SETTINGS.AWS_S3_BUCKET_NAME, "user123/test.pdf"))

s3 = boto3.client("s3", config=Config(signature_version="s3v4"))


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


download_url = create_presigned_url(
    "querypilot-application-s3", "uploads/myfile.pdf", "get_object", 3600
)
upload_url = create_presigned_url(
    "querypilot-application-s3", "uploads/myfile.pdf", "put_object", 3600
)

import os

import boto3

BUCKET = os.getenv("UPLOAD_BUCKET", "querypilot-application-s3")
s3 = boto3.client("s3")


def health_s3():
    try:
        resp = s3.list_objects_v2(Bucket=BUCKET, MaxKeys=1)
        exists = "Contents" in resp
        return {"s3_bucket": BUCKET, "exists": exists}
    except Exception as e:
        return {"s3_bucket": BUCKET, "error": str(e)}


def test_presigned():
    key = "test-connection"
    url = s3.generate_presigned_url(
        "put_object", Params={"Bucket": BUCKET, "Key": key}, ExpiresIn=60
    )
    return {"presigned_url": url}


if __name__ == "__main__":
    print(health_s3())
    print(test_presigned())
