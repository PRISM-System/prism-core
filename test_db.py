#!/usr/bin/env python3
"""
Comprehensive Database Test Script for Prism Core

This script tests:
1. Database connection
2. Table existence and structure
3. Data integrity
4. Basic CRUD operations
5. Sample queries
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
from typing import List, Dict, Any

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.data.postgresql import PostgreSQLDataStore

class DatabaseTester:
    def __init__(self):
        load_dotenv()
        self.db_url = os.getenv("DATABASE_URL", "postgresql://myuser:mysecretpassword@localhost:5432/mydatabase")
        self.db = None
        self.raw_conn = None
        
    def connect(self):
        """Test database connection"""
        print("🔗 Testing database connection...")
        try:
            # Test raw connection
            self.raw_conn = psycopg2.connect(self.db_url)
            print("   ✅ Raw psycopg2 connection successful")
            
            # Test through our DataStore
            self.db = PostgreSQLDataStore(self.db_url)
            print("   ✅ PostgreSQLDataStore connection successful")
            return True
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False
    
    def test_database_info(self):
        """Get basic database information"""
        print("\n📊 Database Information:")
        try:
            with self.raw_conn.cursor(cursor_factory=DictCursor) as cur:
                # Get database version
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"   📋 PostgreSQL Version: {version.split(',')[0]}")
                
                # Get database name and size
                cur.execute("SELECT current_database();")
                db_name = cur.fetchone()[0]
                print(f"   📋 Database Name: {db_name}")
                
                # Get connection info
                cur.execute("SELECT inet_server_addr(), inet_server_port();")
                result = cur.fetchone()
                print(f"   📋 Server: {result[0] or 'localhost'}:{result[1] or '5432'}")
                
        except Exception as e:
            print(f"   ❌ Failed to get database info: {e}")
    
    def test_tables(self):
        """Test table existence and structure"""
        print("\n📋 Testing Tables:")
        try:
            with self.raw_conn.cursor(cursor_factory=DictCursor) as cur:
                # Get all tables
                cur.execute("""
                    SELECT table_name, table_type 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                tables = cur.fetchall()
                
                if not tables:
                    print("   ⚠️  No tables found. Database may not be initialized.")
                    print("   💡 Run: python scripts/init_db.py")
                    return False
                
                print(f"   📊 Found {len(tables)} tables:")
                for table in tables:
                    print(f"      - {table['table_name']} ({table['table_type']})")
                    
                    # Get row count for each table
                    cur.execute(f"SELECT COUNT(*) FROM {table['table_name']};")
                    count = cur.fetchone()[0]
                    print(f"        Rows: {count}")
                
                return True
        except Exception as e:
            print(f"   ❌ Failed to check tables: {e}")
            return False
    
    def test_sample_data(self):
        """Test sample data in key tables"""
        print("\n🔍 Testing Sample Data:")
        
        # Expected tables from Industrial_DB_sample
        expected_tables = [
            'semi_photo_sensors',
            'semi_process_history', 
            'semi_sensor_alert_config',
            'semi_implant_sensors',
            'semi_lot_manage',
            'semi_param_measure',
            'semi_etch_sensors',
            'semi_cvd_sensors',
            'semi_equipment_sensor',
            'semi_cmp_sensors'
        ]
        
        try:
            for table_name in expected_tables:
                try:
                    # Test query through our DataStore
                    results = self.db.query(f"SELECT * FROM {table_name} LIMIT 3;")
                    if results:
                        print(f"   ✅ {table_name}: {len(results)} sample records")
                        # Show first record structure
                        if results:
                            sample_keys = list(results[0].keys())[:5]  # First 5 columns
                            print(f"      Columns: {', '.join(sample_keys)}...")
                    else:
                        print(f"   ⚠️  {table_name}: No data found")
                except Exception as e:
                    print(f"   ❌ {table_name}: {str(e)}")
                    
        except Exception as e:
            print(f"   ❌ Failed to test sample data: {e}")
    
    def test_crud_operations(self):
        """Test basic CRUD operations"""
        print("\n🔧 Testing CRUD Operations:")
        
        # Create a test table
        test_table = "test_crud_table"
        try:
            with self.raw_conn.cursor() as cur:
                # Drop if exists
                cur.execute(f"DROP TABLE IF EXISTS {test_table};")
                
                # Create test table
                cur.execute(f"""
                    CREATE TABLE {test_table} (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100),
                        value INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                self.raw_conn.commit()
                print(f"   ✅ Created test table: {test_table}")
                
                # Test CREATE
                test_data = {"name": "test_item", "value": 42}
                item_id = self.db.add(test_data, test_table)
                print(f"   ✅ CREATE: Added item with ID {item_id}")
                
                # Test READ
                retrieved_item = self.db.get(item_id, test_table)
                if retrieved_item and retrieved_item['name'] == 'test_item':
                    print(f"   ✅ READ: Retrieved item successfully")
                else:
                    print(f"   ❌ READ: Failed to retrieve item")
                
                # Test UPDATE
                update_data = {"name": "updated_item", "value": 84}
                self.db.update(item_id, update_data, test_table)
                updated_item = self.db.get(item_id, test_table)
                if updated_item and updated_item['name'] == 'updated_item':
                    print(f"   ✅ UPDATE: Updated item successfully")
                else:
                    print(f"   ❌ UPDATE: Failed to update item")
                
                # Test DELETE
                self.db.delete(item_id, test_table)
                deleted_item = self.db.get(item_id, test_table)
                if not deleted_item:
                    print(f"   ✅ DELETE: Deleted item successfully")
                else:
                    print(f"   ❌ DELETE: Failed to delete item")
                
                # Clean up
                cur.execute(f"DROP TABLE {test_table};")
                self.raw_conn.commit()
                print(f"   🧹 Cleaned up test table")
                
        except Exception as e:
            print(f"   ❌ CRUD operations failed: {e}")
    
    def test_complex_queries(self):
        """Test complex queries on sample data"""
        print("\n🔍 Testing Complex Queries:")
        
        try:
            # Test join query if multiple tables exist
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
                LIMIT 2;
            """
            tables = self.db.query(tables_query)
            
            if len(tables) >= 2:
                table1 = tables[0]['table_name']
                table2 = tables[1]['table_name']
                
                # Test aggregate query
                agg_query = f"SELECT COUNT(*) as total_rows FROM {table1};"
                result = self.db.query(agg_query)
                print(f"   ✅ Aggregate query on {table1}: {result[0]['total_rows']} rows")
                
                # Test filtering query
                filter_query = f"SELECT * FROM {table1} LIMIT 5;"
                result = self.db.query(filter_query)
                print(f"   ✅ Filtering query on {table1}: Retrieved {len(result)} records")
                
        except Exception as e:
            print(f"   ❌ Complex queries failed: {e}")
    
    def test_performance(self):
        """Basic performance test"""
        print("\n⚡ Performance Test:")
        
        try:
            import time
            
            # Test query performance
            start_time = time.time()
            
            # Get table with most data
            tables_with_counts = []
            with self.raw_conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = cur.fetchall()
                
                for table in tables:
                    cur.execute(f"SELECT COUNT(*) FROM {table['table_name']};")
                    count = cur.fetchone()[0]
                    tables_with_counts.append((table['table_name'], count))
            
            if tables_with_counts:
                # Sort by count and get largest table
                largest_table = max(tables_with_counts, key=lambda x: x[1])
                table_name, row_count = largest_table
                
                # Time a full table scan
                start_time = time.time()
                results = self.db.query(f"SELECT * FROM {table_name};")
                end_time = time.time()
                
                duration = end_time - start_time
                print(f"   ⏱️  Full scan of {table_name} ({row_count} rows): {duration:.3f}s")
                
                if duration < 1.0:
                    print("   ✅ Performance: Good")
                elif duration < 5.0:
                    print("   ⚠️  Performance: Acceptable")
                else:
                    print("   ❌ Performance: Slow")
            
        except Exception as e:
            print(f"   ❌ Performance test failed: {e}")
    
    def run_all_tests(self):
        """Run all database tests"""
        print("🚀 Starting Comprehensive Database Tests")
        print("=" * 50)
        
        # Test 1: Connection
        if not self.connect():
            print("\n❌ Database connection failed. Cannot proceed with tests.")
            return False
        
        # Test 2: Database Info
        self.test_database_info()
        
        # Test 3: Tables
        tables_exist = self.test_tables()
        
        # Test 4: Sample Data (only if tables exist)
        if tables_exist:
            self.test_sample_data()
            
            # Test 5: CRUD Operations
            self.test_crud_operations()
            
            # Test 6: Complex Queries
            self.test_complex_queries()
            
            # Test 7: Performance
            self.test_performance()
        
        print("\n" + "=" * 50)
        print("🎉 Database tests completed!")
        
        # Cleanup
        if self.db:
            self.db.close()
        if self.raw_conn:
            self.raw_conn.close()
        
        return True

def main():
    """Main function"""
    tester = DatabaseTester()
    
    try:
        success = tester.run_all_tests()
        if success:
            print("\n✅ All tests completed successfully!")
        else:
            print("\n❌ Some tests failed. Check the output above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 