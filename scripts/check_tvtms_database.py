#!/usr/bin/env python3
"""
Check TVTMS Database Mappings

This script checks the database for TVTMS versification mappings and provides a summary.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.database.connection import get_db_connection
except ImportError:
    from src.database.connection import get_connection as get_db_connection

def main():
    """Check TVTMS database mappings"""
    # Load environment variables
    load_dotenv()
    
    print("Connecting to database...")
    conn = get_db_connection()
    
    if not conn:
        print("Failed to connect to database")
        return 1
    
    try:
        with conn.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'bible' 
                    AND table_name = 'versification_mappings'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                print("Table bible.versification_mappings does not exist")
                return 1
            
            # Count mappings
            cursor.execute("SELECT COUNT(*) FROM bible.versification_mappings;")
            count = cursor.fetchone()[0]
            print(f"Found {count} versification mappings in the database")
            
            # Count by mapping_type
            cursor.execute("""
                SELECT mapping_type, COUNT(*) 
                FROM bible.versification_mappings 
                GROUP BY mapping_type
                ORDER BY COUNT(*) DESC;
            """)
            mapping_types = cursor.fetchall()
            
            print("\nMapping types:")
            for mapping_type in mapping_types:
                print(f"  - {mapping_type[0]}: {mapping_type[1]} mappings")
            
            # Count by source tradition
            cursor.execute("""
                SELECT source_tradition, COUNT(*) 
                FROM bible.versification_mappings 
                GROUP BY source_tradition
                ORDER BY COUNT(*) DESC
                LIMIT 10;
            """)
            traditions = cursor.fetchall()
            
            print("\nTop 10 source traditions:")
            for tradition in traditions:
                print(f"  - {tradition[0]}: {tradition[1]} mappings")
            
            # Sample data
            cursor.execute("""
                SELECT id, source_tradition, source_book, source_chapter, source_verse,
                       target_book, target_chapter, target_verse, mapping_type
                FROM bible.versification_mappings
                LIMIT 5;
            """)
            samples = cursor.fetchall()
            
            print("\nSample mappings:")
            for sample in samples:
                print(f"  ID {sample[0]}: {sample[1]} {sample[2]}.{sample[3]}:{sample[4]} → {sample[5]}.{sample[6]}:{sample[7]} ({sample[8]})")
            
    except Exception as e:
        print(f"Error checking database: {str(e)}")
        conn.close()
        return 1
    
    finally:
        conn.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 