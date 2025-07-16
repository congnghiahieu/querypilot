import time

import boto3

from src.core.settings import APP_SETTINGS

athena = boto3.client(
    "athena",
    aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
    region_name=APP_SETTINGS.AWS_REGION,
)


def run_query(sql: str):
    resp = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={
            "Database": APP_SETTINGS.AWS_ATHENA_DATABASE,
            "Catalog": APP_SETTINGS.AWS_ATHENA_CATALOG,
        },
        ResultConfiguration={"OutputLocation": APP_SETTINGS.AWS_ATHENA_OUTPUT_LOCATION},
        WorkGroup=APP_SETTINGS.AWS_ATHENA_WORKGROUP,
    )
    qid = resp["QueryExecutionId"]
    while True:
        status = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"][
            "State"
        ]
        if status in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)
    if status != "SUCCEEDED":
        raise Exception("Athena query failed: " + status)

    result = athena.get_query_results(QueryExecutionId=qid)["ResultSet"]["Rows"]
    print("Boto3 rows:", result)
    return result


rows = run_query("SELECT 1;")
print("Athena OK:", rows)
