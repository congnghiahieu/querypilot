import boto3

from src.core.settings import APP_SETTINGS

lf = boto3.client(
    "lakeformation",
    region_name=APP_SETTINGS.AWS_REGION,
    aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
)


def check_connection():
    try:
        resp = lf.get_data_lake_settings()
        print("✅ Connected to LakeFormation:", resp)
    except Exception as e:
        print("❌ Connection failed:", e)


if __name__ == "__main__":
    check_connection()
