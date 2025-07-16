# AWS Athena Setup Guide

This guide will help you configure your QueryPilot application to use AWS Athena for querying data stored in S3. 

## 🎯 Hybrid Configuration (Recommended)

The latest version supports **granular service configuration**, allowing you to use AWS for data queries while keeping other services local. This approach offers:

- ✅ **Cost-effective**: Only pay for Athena queries, no RDS/S3 storage costs
- ✅ **Simple setup**: Minimal AWS configuration required  
- ✅ **Fast development**: Local auth, storage, and user management
- ✅ **Big data access**: Query large S3 datasets via Athena
- ✅ **Incremental migration**: Move services to AWS later as needed

## Prerequisites

1. **AWS Account** with access to:
   - S3 (your data storage)
   - Athena (query service)
   - Glue Catalog (metadata management)
   - IAM (permissions)

2. **Data in S3**: Your data should be stored in S3 in a format supported by Athena (CSV, JSON, Parquet, ORC, etc.)

## Step 1: AWS Infrastructure Setup

### 1.1 Create S3 Buckets
You need at least two S3 locations:
- **Data Bucket**: Where your actual data files are stored
- **Query Results Bucket**: Where Athena stores query results

```bash
# Example structure:
s3://your-company-data/
  ├── banking_data/
  │   ├── customers/
  │   ├── transactions/
  │   └── accounts/
  └── ...

s3://your-company-athena-results/
  └── query-results/
```

### 1.2 Set up Glue Catalog Database
Create a database in AWS Glue Catalog to organize your tables:

1. Go to AWS Glue Console
2. Create a new database (e.g., "vpbank_analytics")
3. Add tables either by:
   - Using Glue Crawlers (recommended for automatic schema detection)
   - Manually creating table definitions

### 1.3 Create Athena Workgroup (Optional)
Create a workgroup for better resource management:
1. Go to Athena Console
2. Create workgroup (e.g., "vpbank-queries")
3. Configure query result location

## Step 2: Environment Configuration

### Option A: Hybrid Configuration (Recommended)
Create a `.env` file in the `querypilot2/backend/` directory with granular service configuration:

```bash
# =============================================================================
# GRANULAR SERVICE CONFIGURATION  
# =============================================================================
DATA_SOURCE=aws        # Use AWS Athena for data queries
AUTH_SOURCE=local      # Use local authentication  
FILE_STORAGE=local     # Use local file storage
USER_DB=local          # Use local PostgreSQL for user data

# Legacy settings (for backward compatibility)
ENV=local
STAGE=prod

# Core application settings
DEEPSEEK_API_KEY=your_deepseek_api_key_here
SECRET_KEY=your_jwt_secret_key_here
CLIENT_URL=http://localhost:3000

# Local database for user sessions, chat history
DATABASE_URL=postgresql+psycopg2://querypilot:querypilot@localhost:5432/querypilot

# AWS credentials (only for data access)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1

# AWS Athena configuration (for data queries)
AWS_ATHENA_DATABASE=vpbank_analytics          # Primary database (fallback)
AWS_ATHENA_RAW_DATABASE=vpbank_raw            # Raw/detailed data (optional)
AWS_ATHENA_AGG_DATABASE=vpbank_aggregated     # Aggregated data (optional)  
AWS_ATHENA_WORKGROUP=primary
AWS_ATHENA_OUTPUT_LOCATION=s3://your-company-athena-results/query-results/
AWS_ATHENA_TIMEOUT=300
```

### Option B: Full AWS Configuration
For complete AWS integration, use:

```bash
# =============================================================================
# FULL AWS CONFIGURATION
# =============================================================================
DATA_SOURCE=aws        # Use AWS Athena for data queries
AUTH_SOURCE=aws        # Use AWS Cognito for authentication  
FILE_STORAGE=aws       # Use AWS S3 for file storage
USER_DB=aws            # Use AWS RDS for user data

# Legacy settings
ENV=aws
STAGE=prod

# Required secrets
DEEPSEEK_API_KEY=your_deepseek_api_key_here
SECRET_KEY=your_jwt_secret_key_here
CLIENT_URL=http://localhost:3000

# PostgreSQL Database (for user sessions, chat history, etc.)
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/querypilot

# AWS Credentials
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1

# AWS S3 Configuration
AWS_S3_BUCKET_NAME=your-company-data
AWS_S3_BUCKET_URL=https://your-company-data.s3.amazonaws.com

# AWS Athena Configuration
AWS_ATHENA_DATABASE=vpbank_analytics  # Your Glue Catalog database name
AWS_ATHENA_WORKGROUP=primary  # Your Athena workgroup
AWS_ATHENA_OUTPUT_LOCATION=s3://your-company-athena-results/query-results/
AWS_ATHENA_TIMEOUT=300

# AWS RDS Configuration (if using RDS for user data instead of local PostgreSQL)
AWS_RDS_HOST=your-rds-endpoint.region.rds.amazonaws.com
AWS_RDS_PORT=5432
AWS_RDS_DB_NAME=querypilot
AWS_RDS_USERNAME=your_username
AWS_RDS_PASSWORD=your_password
```

## Step 3: AWS IAM Permissions

Your AWS user/role needs the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "athena:StartQueryExecution",
                "athena:GetQueryExecution",
                "athena:GetQueryResults",
                "athena:StopQueryExecution",
                "athena:GetWorkGroup"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::your-company-data/*",
                "arn:aws:s3:::your-company-athena-results/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "glue:GetDatabase",
                "glue:GetDatabases",
                "glue:GetTable",
                "glue:GetTables",
                "glue:GetPartition",
                "glue:GetPartitions"
            ],
            "Resource": "*"
        }
    ]
}
```

## Step 4: Data Preparation

### 4.1 Organize Your Data
Structure your S3 data in a way that's optimal for Athena:

```
s3://your-company-data/
├── customers/
│   ├── year=2023/
│   │   └── customers_2023.csv
│   └── year=2024/
│       └── customers_2024.csv
├── transactions/
│   ├── year=2023/month=01/
│   │   └── transactions_202301.parquet
│   └── year=2023/month=02/
│       └── transactions_202302.parquet
```

### 4.2 Create Tables in Glue Catalog
You can create tables using AWS Glue Crawlers or manually:

#### Option A: Using Glue Crawler (Recommended)
1. Go to AWS Glue Console
2. Create a new crawler
3. Point it to your S3 data location
4. Run the crawler to automatically detect schema

#### Option B: Manual Table Creation
```sql
CREATE EXTERNAL TABLE customers (
    customer_id string,
    name string,
    email string,
    created_date date
)
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://your-company-data/customers/'
TBLPROPERTIES ('has_encrypted_data'='false');
```

## Step 5: Testing the Connection

### 5.1 Test Service Health
```bash
cd querypilot2/backend
python -c "
from src.core.sql_execution import get_sql_execution_service
service = get_sql_execution_service()
health = service.check_service_health()
print(health)
"
```

### 5.2 Test Schema Retrieval
```bash
python -c "
from src.core.sql_execution import get_sql_execution_service
service = get_sql_execution_service()
schema = service.get_database_schema()
print(schema)
"
```

### 5.3 Test Query Execution
```bash
python -c "
import asyncio
from src.core.sql_execution import get_sql_execution_service

async def test_query():
    service = get_sql_execution_service()
    result = await service.execute_query('SELECT * FROM your_table_name LIMIT 10')
    print(result)

asyncio.run(test_query())
"
```

## Step 6: Configuration Summary

### Hybrid Configuration (DATA_SOURCE=aws, others=local):
- ✅ **Data Queries**: AWS Athena queries your S3 data
- ✅ **User Management**: Local PostgreSQL database
- ✅ **Authentication**: Local JWT-based auth
- ✅ **File Storage**: Local filesystem for knowledge base uploads
- ✅ **Chat History**: Local database storage
- ✅ **Cost**: Only pay for Athena query usage

### Full AWS Configuration (all services=aws):  
- ✅ **Data Queries**: AWS Athena
- ✅ **User Management**: AWS RDS PostgreSQL
- ✅ **Authentication**: AWS Cognito
- ✅ **File Storage**: AWS S3
- ✅ **Chat History**: AWS RDS storage
- ✅ **Scalability**: Fully managed AWS infrastructure

### Multi-Database Intelligence

The system supports multiple Athena databases for different data types:

- **Raw Database** (`AWS_ATHENA_RAW_DATABASE`): Detailed, transaction-level data
- **Aggregated Database** (`AWS_ATHENA_AGG_DATABASE`): Pre-computed summaries and reports
- **Primary Database** (`AWS_ATHENA_DATABASE`): Default fallback database

**Intelligent Database Selection:**
The system automatically chooses the appropriate database based on query intent:

```
Query: "Show me individual customer transactions"
→ Routes to Raw Database (detailed data)

Query: "What's the total monthly revenue?"
→ Routes to Aggregated Database (summary data)
```

**Manual Database Selection:**
You can also specify the database explicitly in API calls:

```json
{
  "message": "Show customer segments",
  "database_type": "agg"  // "raw", "agg", or null for auto-detection
}
```

**Database Configuration:**
- `DATA_SOURCE=aws` → Uses intelligent Athena database selection
- `DATA_SOURCE=local` → Uses local SQLite database

## Common Issues and Troubleshooting

### Issue 1: Access Denied Errors
- Check IAM permissions
- Verify S3 bucket policies
- Ensure Athena workgroup has proper configurations

### Issue 2: Table Not Found
- Verify table exists in Glue Catalog
- Check database name in configuration
- Run crawler to update metadata

### Issue 3: Query Timeout
- Increase `AWS_ATHENA_TIMEOUT` value
- Optimize your queries
- Consider partitioning large datasets

### Issue 4: Invalid S3 Location
- Check S3 bucket names and paths
- Verify region consistency
- Ensure proper S3 permissions

## Performance Optimization

1. **Use Columnar Formats**: Convert CSV to Parquet for better performance
2. **Partition Data**: Partition by date, region, or other frequently filtered columns
3. **Compress Data**: Use compression (GZIP, Snappy) to reduce scan costs
4. **Optimize Queries**: Use appropriate WHERE clauses and LIMIT statements

## Cost Optimization

1. **Monitor Query Costs**: Athena charges per TB scanned
2. **Use Partitioning**: Reduces data scanned
3. **Compress Data**: Reduces storage and scan costs
4. **Set Query Limits**: Use reasonable LIMIT clauses for exploratory queries

## Next Steps

After completing this setup:
1. Test the connection using the provided scripts
2. Verify your tables are accessible
3. Update the nl2sql configuration with your database name
4. Test end-to-end query execution through the chat interface 