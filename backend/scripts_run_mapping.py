import json

import boto3

# Cấu hình
account_id = "123456789012"  # Thay bằng AWS Account ID thật
catalog_id = account_id
database_name = "vp_bank"

# Load JSON file
with open("lakeformation_group_based_policies.json") as f:
    policies = json.load(f)["grant_policies"]

# Khởi tạo client
lf = boto3.client("lakeformation")


# Hàm sinh tên filter an toàn
def sanitize_name(s):
    return s.replace("-", "_").replace("*", "ALL")


# Duyệt qua từng policy và cấp quyền
for entry in policies:
    principal_name = entry["principal"]
    table_name = entry["table"]
    row_filter_expr = entry["filter"]

    principal_arn = f"arn:aws:iam::{account_id}:role/{principal_name}"

    if row_filter_expr:
        # Tạo DataCellsFilter name duy nhất
        filter_name = sanitize_name(f"{principal_name}_{table_name}")

        # Tạo DataCellsFilter nếu chưa có (bạn có thể tách riêng bước tạo filter nếu cần)
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

        # Grant permission with filter
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
        print(f"✅ Granted SELECT on {table_name} to {principal_name} with filter")
    else:
        # Không có RowFilter, cấp quyền toàn bảng
        lf.grant_permissions(
            Principal={"DataLakePrincipalIdentifier": principal_arn},
            Resource={"Table": {"DatabaseName": database_name, "Name": table_name}},
            Permissions=["SELECT"],
            PermissionsWithGrantOption=[],
        )
        print(f"✅ Granted SELECT on {table_name} to {principal_name} (no filter)")
