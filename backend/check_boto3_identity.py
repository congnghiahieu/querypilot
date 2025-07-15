import boto3

identity = boto3.client("sts").get_caller_identity()
print(identity)
# Kết quả: {"UserId": "...", "Account": "...", "Arn": "arn:aws:iam::123456789012:role/MyEC2Role"}
