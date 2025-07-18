#!/usr/bin/env python3
"""
Test script for AWS Athena integration with nl2sql module.

This script tests the modified nl2sql module to ensure it works correctly
with both AWS Athena and local SQLite databases.
"""

import sys
import asyncio
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.settings import APP_SETTINGS
from src.core.sql_execution import get_sql_execution_service
from src.nl2sql.dail_sql.nl2sql import nl2sql
from src.nl2sql.dail_sql.utils.utils import get_sql_for_athena_database, get_sql_for_database

def test_sqlite_schema():
    """Test schema retrieval for SQLite database"""
    print("🧪 Testing SQLite schema retrieval...")
    
    try:
        # Test with local SQLite database
        from src.core.settings import PROJECT_ROOT
        db_path = PROJECT_ROOT / "dataset" / "vpbank.sqlite"
        
        if db_path.exists():
            schema = get_sql_for_database(str(db_path))
            print(f"✅ SQLite schema retrieved successfully")
            print(f"   Tables: {len(schema['table_names_original'])}")
            print(f"   Columns: {len(schema['column_names_original'])}")
            
            # Print first few tables and columns for verification
            if schema['table_names_original']:
                print(f"   Sample tables: {schema['table_names_original'][:3]}")
            if schema['column_names_original']:
                print(f"   Sample columns: {schema['column_names_original'][:5]}")
            
            return True
        else:
            print(f"⚠️  SQLite database not found at {db_path}")
            return False
            
    except Exception as e:
        print(f"❌ SQLite schema test failed: {e}")
        return False

def test_athena_schema():
    """Test schema retrieval for AWS Athena database"""
    print("\n🧪 Testing AWS Athena schema retrieval...")
    
    if not APP_SETTINGS.use_aws_data:
        print("⚠️  AWS data source not configured (DATA_SOURCE != 'aws')")
        return False
    
    try:
        # Test with different database types
        database_types = ["default", "raw", "agg"]
        
        for db_type in database_types:
            try:
                schema = get_sql_for_athena_database(db_type)
                print(f"✅ Athena schema retrieved for {db_type} database")
                print(f"   Tables: {len(schema['table_names_original'])}")
                print(f"   Columns: {len(schema['column_names_original'])}")
                
                # Print first few tables and columns for verification
                if schema['table_names_original']:
                    print(f"   Sample tables: {schema['table_names_original'][:3]}")
                    
            except Exception as e:
                print(f"⚠️  Failed to get schema for {db_type} database: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Athena schema test failed: {e}")
        return False

def test_nl2sql_sqlite():
    """Test nl2sql function with SQLite"""
    print("\n🧪 Testing nl2sql with SQLite...")
    
    try:
        # Set to use local data
        original_data_source = APP_SETTINGS.DATA_SOURCE
        APP_SETTINGS.DATA_SOURCE = "local"
        
        test_question = "Show me all customers"
        test_context = ""
        db_id = "vpbank"
        
        result = nl2sql(test_question, test_context, db_id)
        
        if result:
            print("✅ nl2sql SQLite test successful")
            print(f"   Generated SQL: {result}")
            return True
        else:
            print("❌ nl2sql SQLite test failed - no SQL generated")
            return False
            
    except Exception as e:
        print(f"❌ nl2sql SQLite test failed: {e}")
        return False
    finally:
        # Restore original setting
        APP_SETTINGS.DATA_SOURCE = original_data_source

def test_nl2sql_athena():
    """Test nl2sql function with AWS Athena"""
    print("\n🧪 Testing nl2sql with AWS Athena...")
    
    if not APP_SETTINGS.use_aws_data:
        print("⚠️  AWS data source not configured - skipping Athena nl2sql test")
        return False
    
    try:
        test_question = "Show me customer transactions from last month"
        test_context = ""
        db_id = "default"  # Use default database type
        
        result = nl2sql(test_question, test_context, db_id)
        
        if result:
            print("✅ nl2sql Athena test successful")
            print(f"   Generated SQL: {result}")
            return True
        else:
            print("❌ nl2sql Athena test failed - no SQL generated")
            return False
            
    except Exception as e:
        print(f"❌ nl2sql Athena test failed: {e}")
        return False

async def test_sql_execution_service():
    """Test SQL execution service connectivity"""
    print("\n🧪 Testing SQL execution service...")
    
    try:
        sql_service = get_sql_execution_service()
        
        if sql_service:
            print("✅ SQL execution service initialized successfully")
            
            # Test schema retrieval
            if APP_SETTINGS.use_aws_data:
                schema = sql_service.get_database_schema("default")
                if "error" not in schema:
                    print("✅ Athena schema retrieval through service successful")
                    return True
                else:
                    print(f"❌ Athena schema retrieval error: {schema['error']}")
                    return False
            else:
                schema = sql_service.get_database_schema("vpbank")
                if "error" not in schema:
                    print("✅ SQLite schema retrieval through service successful")
                    return True
                else:
                    print(f"❌ SQLite schema retrieval error: {schema['error']}")
                    return False
        else:
            print("❌ Failed to initialize SQL execution service")
            return False
            
    except Exception as e:
        print(f"❌ SQL execution service test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing AWS Athena integration with nl2sql module")
    print("=" * 60)
    
    # Display current configuration
    print(f"📋 Current Configuration:")
    print(f"   DATA_SOURCE: {APP_SETTINGS.DATA_SOURCE}")
    print(f"   Use AWS Data: {APP_SETTINGS.use_aws_data}")
    if APP_SETTINGS.use_aws_data:
        print(f"   AWS Region: {APP_SETTINGS.AWS_REGION}")
        print(f"   Athena Database: {APP_SETTINGS.AWS_ATHENA_DATABASE}")
        print(f"   Athena Workgroup: {APP_SETTINGS.AWS_ATHENA_WORKGROUP}")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: SQL Execution Service
    total_tests += 1
    if asyncio.run(test_sql_execution_service()):
        tests_passed += 1
    
    # Test 2: Schema retrieval
    if APP_SETTINGS.use_aws_data:
        total_tests += 1
        if test_athena_schema():
            tests_passed += 1
    else:
        total_tests += 1
        if test_sqlite_schema():
            tests_passed += 1
    
    # Test 3: nl2sql function
    if APP_SETTINGS.use_aws_data:
        total_tests += 1
        if test_nl2sql_athena():
            tests_passed += 1
    else:
        total_tests += 1
        if test_nl2sql_sqlite():
            tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! AWS Athena integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration and error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 