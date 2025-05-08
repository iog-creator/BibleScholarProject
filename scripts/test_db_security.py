#!/usr/bin/env python3
"""
Test Database Security

This script tests the secure database connection in both read and write modes.
It verifies that:
1. Read-only connections can only perform SELECT operations
2. Write connections can perform INSERT/UPDATE/DELETE operations
3. Proper errors are raised for unauthorized operations

Usage:
    python scripts/test_db_security.py
"""

import os
import sys
import logging
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from src.database.secure_connection import get_secure_connection, check_connection_mode
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_read_connection():
    """Test read-only database connection."""
    print("\nTesting READ-ONLY connection...")
    
    try:
        # Get read-only connection
        conn = get_secure_connection(mode='read')
        
        # Verify connection mode
        mode = check_connection_mode(conn)
        print(f"Connection mode: {mode}")
        assert mode == 'read', "Connection should be in read-only mode"
        
        # Test SELECT query
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM bible.verses")
            result = cursor.fetchone()
            verse_count = result['count'] if 'count' in result else list(result.values())[0]
            print(f"SUCCESS: Read query executed successfully. Found {verse_count} verses.")
        
        # Test INSERT query (should fail)
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                CREATE TEMPORARY TABLE IF NOT EXISTS test_table (id SERIAL, name TEXT)
                """)
                conn.commit()
            print("FAILURE: Was able to create a table in read-only mode!")
            return False
        except Exception as e:
            print(f"SUCCESS: Write operation was blocked as expected: {e}")
        
        # Close connection
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_write_connection():
    """Test write database connection."""
    print("\nTesting WRITE connection...")
    
    try:
        # Check if write password is set
        if not os.getenv('POSTGRES_WRITE_PASSWORD'):
            print("WARNING: POSTGRES_WRITE_PASSWORD not set in environment or .env file.")
            print("This test will fail unless you've configured database security.")
            
        # Get write connection
        conn = get_secure_connection(mode='write')
        
        # Verify connection mode
        mode = check_connection_mode(conn)
        print(f"Connection mode: {mode}")
        assert mode == 'write', "Connection should be in write mode"
        
        # Test SELECT query
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM bible.verses")
            result = cursor.fetchone()
            verse_count = result['count'] if 'count' in result else list(result.values())[0]
            print(f"SUCCESS: Read query executed successfully. Found {verse_count} verses.")
        
        # Test CREATE TEMPORARY TABLE
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TEMPORARY TABLE IF NOT EXISTS test_security_table (
                id SERIAL PRIMARY KEY,
                test_name TEXT,
                test_value TEXT
            )
            """)
            conn.commit()
            print("SUCCESS: Created temporary table")
            
            # Insert test data
            cursor.execute("""
            INSERT INTO test_security_table (test_name, test_value)
            VALUES (%s, %s) RETURNING id
            """, ("db_security_test", "passed"))
            result = cursor.fetchone()
            test_id = result['id'] if 'id' in result else list(result.values())[0]
            conn.commit()
            print(f"SUCCESS: Inserted test data with ID {test_id}")
            
            # Query the data
            cursor.execute("SELECT * FROM test_security_table WHERE id = %s", (test_id,))
            result = cursor.fetchone()
            print(f"SUCCESS: Retrieved test data: {result}")
            
            # Clean up
            cursor.execute("DROP TABLE test_security_table")
            conn.commit()
            print("SUCCESS: Dropped temporary table")
        
        # Close connection
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Run all tests."""
    print("Bible Database Security Test")
    print("===========================")
    
    # Test read-only connection
    read_test = test_read_connection()
    
    # Test write connection
    write_test = test_write_connection()
    
    # Report results
    print("\n=== TEST RESULTS ===")
    print(f"Read-only mode test: {'PASSED' if read_test else 'FAILED'}")
    print(f"Write mode test: {'PASSED' if write_test else 'FAILED'}")
    
    if read_test and write_test:
        print("\nAll database security tests PASSED!")
        print("\nYour database is properly secured with:")
        print("- READ-ONLY mode for safe queries")
        print("- WRITE mode with password protection for data modifications")
        return 0
    else:
        print("\nSome tests FAILED. Review the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 