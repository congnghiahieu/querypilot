import json

import boto3

from src.core.settings import APP_SETTINGS

# Config
# account_id = APP_SETTINGS.AWS_ACCOUNT_ID
account_id = "692859913811"  # Replace with your actual AWS Account ID
catalog_id = account_id
# database_name = APP_SETTINGS.AWS_LAKEFORMATION_DATABASE_NAME
database_name = "agg_database"  # Example database name, replace as needed

# Load policies
with open("lakeformation_group_based_policies.json") as f:
    policies = json.load(f)["grant_policies"]

# Init boto3 Lake Formation client with configured credentials
lf = boto3.client(
    "lakeformation",
    region_name=APP_SETTINGS.AWS_REGION,
    aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
)


# Utility: safe name for filter
def sanitize_name(s):
    return s.replace("-", "_").replace("*", "ALL")


# Iterate policies
for entry in policies:
    principal_name = entry["principal"]
    table_name = entry["table"]
    row_filter_expr = entry.get("filter")

    principal_arn = f"arn:aws:iam::{account_id}:role/{principal_name}"

    if row_filter_expr:
        filter_name = sanitize_name(f"{principal_name}_{table_name}")

        try:
            lf.create_data_cells_filter(
                TableData={
                    "TableCatalogId": catalog_id,
                    "DatabaseName": database_name,
                    "TableName": table_name,
                    "Name": filter_name,
                    "RowFilter": {"FilterExpression": row_filter_expr},
                }
            )
            print(f"✅ Created DataCellsFilter: {filter_name}")
        except lf.exceptions.AlreadyExistsException:
            print(f"⚠️ Filter {filter_name} already exists, skipping...")

        lf.grant_permissions(
            Principal={"DataLakePrincipalIdentifier": principal_arn},
            Resource={
                "DataCellsFilter": {
                    "TableCatalogId": catalog_id,
                    "DatabaseName": database_name,
                    "TableName": table_name,
                    "Name": filter_name,
                }
            },
            Permissions=["SELECT"],
            PermissionsWithGrantOption=[],
        )
        print(f"✅ Granted SELECT on {table_name} to {principal_name} (filtered)")
    else:
        lf.grant_permissions(
            Principal={"DataLakePrincipalIdentifier": principal_arn},
            Resource={
                "Table": {
                    "DatabaseName": database_name,
                    "Name": table_name,
                }
            },
            Permissions=["SELECT"],
            PermissionsWithGrantOption=[],
        )
        print(f"✅ Granted SELECT on {table_name} to {principal_name} (unfiltered)")
