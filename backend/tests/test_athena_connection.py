#!/usr/bin/env python3
"""
Test script for AWS Athena connection and configuration.
Run this script to verify your Athena setup before using the main application.

Usage:
    python test_athena_connection.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path for absolute imports
sys.path.append(str(Path(__file__).parent.parent))

from src.core.settings import APP_SETTINGS
from src.core.sql_execution import get_sql_execution_service


def print_separator(title: str):
    """Print a nice separator with title"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_config():
    """Print current configuration"""
    print_separator("CURRENT CONFIGURATION")
    
    print(f"Environment: {APP_SETTINGS.ENV}")
    print(f"Stage: {APP_SETTINGS.STAGE}")
    print(f"Is AWS (legacy): {APP_SETTINGS.is_aws}")
    print(f"AWS Region: {APP_SETTINGS.AWS_REGION}")
    
    # Show granular settings
    print(f"\nGranular Configuration:")
    print(f"  Data Source: {APP_SETTINGS.DATA_SOURCE} (use_aws_data: {APP_SETTINGS.use_aws_data})")
    print(f"  Auth Source: {APP_SETTINGS.AUTH_SOURCE} (use_aws_auth: {APP_SETTINGS.use_aws_auth})")
    print(f"  File Storage: {APP_SETTINGS.FILE_STORAGE} (use_aws_storage: {APP_SETTINGS.use_aws_storage})")
    print(f"  User Database: {APP_SETTINGS.USER_DB} (use_aws_user_db: {APP_SETTINGS.use_aws_user_db})")
    
    if APP_SETTINGS.use_aws_data:
        print(f"Athena Primary Database: {APP_SETTINGS.AWS_ATHENA_DATABASE}")
        print(f"Athena Raw Database: {APP_SETTINGS.AWS_ATHENA_RAW_DATABASE or 'Not configured'}")
        print(f"Athena Aggregated Database: {APP_SETTINGS.AWS_ATHENA_AGG_DATABASE or 'Not configured'}")
        print(f"Athena Workgroup: {APP_SETTINGS.AWS_ATHENA_WORKGROUP}")
        print(f"Athena Output Location: {APP_SETTINGS.AWS_ATHENA_OUTPUT_LOCATION}")
        print(f"Athena Timeout: {APP_SETTINGS.AWS_ATHENA_TIMEOUT}s")
        print(f"S3 Bucket: {APP_SETTINGS.AWS_S3_BUCKET_NAME}")
        
        # Show available databases
        available_dbs = APP_SETTINGS.get_available_athena_databases()
        print(f"\nConfigured Databases:")
        for db_type, db_name in available_dbs.items():
            print(f"  {db_type}: {db_name}")
        
        # Check for credentials (don't print actual values for security)
        print(f"\nCredentials:")
        print(f"AWS Access Key ID: {'✓ Set' if APP_SETTINGS.AWS_ACCESS_KEY_ID else '✗ Missing'}")
        print(f"AWS Secret Access Key: {'✓ Set' if APP_SETTINGS.AWS_SECRET_ACCESS_KEY else '✗ Missing'}")
    else:
        print("Data source configured for local SQLite")


def test_service_initialization():
    """Test if SQL execution service can be initialized"""
    print_separator("SERVICE INITIALIZATION TEST")
    
    try:
        service = get_sql_execution_service()
        if service:
            print("✓ SQL execution service initialized successfully")
            return service
        else:
            print("✗ Failed to initialize SQL execution service")
            return None
    except Exception as e:
        print(f"✗ Error initializing service: {e}")
        return None


def test_service_health(service):
    """Test service health check"""
    print_separator("SERVICE HEALTH CHECK")
    
    try:
        health = service.check_service_health()
        print(f"Health Status: {health.get('status', 'unknown')}")
        
        if health.get('status') == 'healthy':
            print("✓ Service is healthy")
            if 'database' in health:
                print(f"Database: {health['database']}")
            if 'workgroup' in health:
                print(f"Workgroup: {health['workgroup']}")
            if 'tables_count' in health:
                print(f"Tables found: {health['tables_count']}")
                if health.get('tables'):
                    print("Available tables:")
                    for table in health['tables'][:10]:  # Show first 10 tables
                        print(f"  - {table}")
                    if len(health['tables']) > 10:
                        print(f"  ... and {len(health['tables']) - 10} more")
        else:
            print("✗ Service health check failed")
            if 'error' in health:
                print(f"Error: {health['error']}")
                
        return health.get('status') == 'healthy'
    except Exception as e:
        print(f"✗ Error during health check: {e}")
        return False


def test_schema_retrieval(service):
    """Test database schema retrieval"""
    print_separator("SCHEMA RETRIEVAL TEST")
    
    if not APP_SETTINGS.use_aws_data:
        try:
            schema = service.get_database_schema()
            
            if 'error' in schema:
                print(f"✗ Error retrieving schema: {schema['error']}")
                return False
                
            print("✓ Schema retrieved successfully")
            print(f"Database: {schema.get('database', 'unknown')}")
            return True
        except Exception as e:
            print(f"✗ Error retrieving schema: {e}")
            return False
    
    # For AWS, test multiple databases
    try:
        all_schemas = service.get_all_database_schemas()
        
        if 'error' in all_schemas:
            print(f"✗ Error retrieving schemas: {all_schemas['error']}")
            return False
            
        print("✓ Multiple database schemas retrieved successfully")
        
        databases = all_schemas.get('databases', {})
        available_types = all_schemas.get('available_types', [])
        
        print(f"Available database types: {', '.join(available_types)}")
        
        for db_type, schema in databases.items():
            if 'error' in schema:
                print(f"\n❌ {db_type}: {schema['error']}")
                continue
                
            print(f"\n✓ {db_type} database: {schema.get('database', 'unknown')}")
            tables = schema.get('tables', [])
            print(f"  Tables found: {len(tables)}")
            
            # Show first few tables
            for i, table in enumerate(tables[:3]):
                table_name = table.get('name', 'unknown')
                columns = table.get('columns', [])
                print(f"  - {table_name} ({len(columns)} columns)")
            
            if len(tables) > 3:
                print(f"  ... and {len(tables) - 3} more tables")
            
        return True
    except Exception as e:
        print(f"✗ Error retrieving schema: {e}")
        return False


async def test_sample_query(service):
    """Test executing a sample query"""
    print_separator("SAMPLE QUERY TEST")
    
    if not APP_SETTINGS.use_aws_data:
        # Simple test for SQLite
        try:
            schema = service.get_database_schema()
            tables = schema.get('tables', {})
            
            if not tables:
                print("✗ No tables found - cannot test query execution")
                return False
                
            # Get first table name
            if isinstance(tables, dict):
                table_name = list(tables.keys())[0]
            else:
                print("✗ Unexpected schema format")
                return False
                
            print(f"Testing query on table: {table_name}")
            
            # Try a simple SELECT query
            test_query = f"SELECT * FROM {table_name} LIMIT 5"
            print(f"Query: {test_query}")
            
            result = await service.execute_query(test_query)
            
            if result.get('status') == 'success':
                print("✓ Query executed successfully")
                print(f"Execution time: {result.get('execution_time', 0):.2f}s")
                print(f"Rows returned: {result.get('row_count', 0)}")
                return True
            else:
                print("✗ Query execution failed")
                print(f"Error: {result.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"✗ Error executing test query: {e}")
            return False
    
    # Test multiple databases for AWS
    try:
        all_schemas = service.get_all_database_schemas()
        databases = all_schemas.get('databases', {})
        
        if not databases:
            print("✗ No databases found - cannot test query execution")
            return False
        
        success_count = 0
        total_tests = 0
        
        for db_type, schema in databases.items():
            if 'error' in schema:
                print(f"⚠️ Skipping {db_type} database due to schema error")
                continue
                
            tables = schema.get('tables', [])
            if not tables:
                print(f"⚠️ No tables in {db_type} database")
                continue
            
            table_name = tables[0].get('name', 'unknown')
            print(f"\nTesting {db_type} database on table: {table_name}")
            
            # Try a simple SELECT query
            test_query = f"SELECT * FROM {table_name} LIMIT 3"
            print(f"Query: {test_query}")
            
            total_tests += 1
            
            try:
                result = await service.execute_query(test_query, db_type if db_type != "default" else None)
                
                if result.get('status') == 'success':
                    print(f"✓ {db_type} query executed successfully")
                    print(f"  Database: {result.get('database', 'unknown')}")
                    print(f"  Execution time: {result.get('execution_time', 0):.2f}s")
                    print(f"  Rows returned: {result.get('row_count', 0)}")
                    
                    if 'data_scanned_bytes' in result:
                        data_scanned_mb = result['data_scanned_bytes'] / (1024 * 1024)
                        print(f"  Data scanned: {data_scanned_mb:.2f} MB")
                    
                    success_count += 1
                else:
                    print(f"✗ {db_type} query execution failed")
                    print(f"  Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"✗ Error executing {db_type} query: {e}")
        
        print(f"\nQuery Test Summary: {success_count}/{total_tests} databases tested successfully")
        return success_count > 0
            
    except Exception as e:
        print(f"✗ Error executing test queries: {e}")
        return False


def print_recommendations():
    """Print recommendations based on test results"""
    print_separator("RECOMMENDATIONS")
    
    if not APP_SETTINGS.use_aws_data:
        print("📝 You're currently configured for local SQLite data source.")
        print("   To use AWS Athena for data queries:")
        print("   1. Set DATA_SOURCE=aws in your .env file")
        print("   2. Configure all AWS_* environment variables for Athena")
        print("   3. Keep other services local by setting AUTH_SOURCE=local, FILE_STORAGE=local, USER_DB=local")
        print("   4. Run this test again")
        return
        
    print("📝 AWS Athena Configuration Tips:")
    print("   1. Ensure your S3 data is in a format Athena supports (CSV, JSON, Parquet, ORC)")
    print("   2. Use AWS Glue Crawlers to automatically detect schema for complex data")
    print("   3. Consider partitioning large datasets for better performance")
    print("   4. Use columnar formats (Parquet) for better query performance")
    print("   5. Monitor query costs - Athena charges per TB of data scanned")
    
    print("\n🔧 If you encounter issues:")
    print("   1. Check your AWS IAM permissions")
    print("   2. Verify S3 bucket permissions")
    print("   3. Ensure Athena workgroup is properly configured")
    print("   4. Check that your Glue Catalog database and tables exist")


async def main():
    """Main test function"""
    print("🔍 AWS Athena Connection Test")
    print("This script will test your Athena configuration and connection.")
    
    # Print current configuration
    print_config()
    
    # Test service initialization
    service = test_service_initialization()
    if not service:
        print("\n❌ Cannot proceed with tests - service initialization failed")
        print_recommendations()
        return
    
    # Test service health
    health_ok = test_service_health(service)
    
    # Test schema retrieval
    schema_ok = test_schema_retrieval(service)
    
    # Test sample query (only if previous tests passed)
    query_ok = False
    if health_ok and schema_ok:
        query_ok = await test_sample_query(service)
    
    # Print summary
    print_separator("TEST SUMMARY")
    print(f"Service Initialization: {'✓' if service else '✗'}")
    print(f"Health Check: {'✓' if health_ok else '✗'}")
    print(f"Schema Retrieval: {'✓' if schema_ok else '✗'}")
    print(f"Sample Query: {'✓' if query_ok else '✗'}")
    
    if all([service, health_ok, schema_ok, query_ok]):
        print("\n🎉 All tests passed! Your Athena connection is working correctly.")
        print("You can now use the main application to query your data.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above and your configuration.")
        
    print_recommendations()


if __name__ == "__main__":
    # Check if .env file exists
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        print("⚠️ No .env file found. Please create one with your AWS configuration.")
        print("Refer to AWS_ATHENA_SETUP.md for detailed instructions.")
        sys.exit(1)
        
    asyncio.run(main()) 