#!/usr/bin/env python
"""
Script to list all tables in the bible database schema with their column information.
This script is used to identify data available for training or validation.

Usage:
    python scripts/list_db_tables.py [--schema bible] [--verbose]
"""

import argparse
import logging
import os
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/database_inspection.log", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import secure database connection
try:
    from src.database.secure_connection import get_secure_connection
    logger.info("Using secure_connection for database access")
except ImportError:
    logger.warning("Could not import secure_connection, falling back to direct connection")
    
    def get_secure_connection(mode='read'):
        """Fallback connection method"""
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "bible_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "")
        )

def get_tables(schema: str = 'bible') -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all tables and their columns in the specified schema.
    
    Args:
        schema: Database schema to inspect (default: 'bible')
        
    Returns:
        Dictionary mapping table names to their column information
    """
    conn = get_secure_connection(mode='read')
    tables_info = {}
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # Get all tables in the schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
                ORDER BY table_name
            """, (schema,))
            
            tables = cursor.fetchall()
            
            # Get column information for each table
            for table_row in tables:
                table_name = table_row[0]
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table_name))
                
                columns = cursor.fetchall()
                tables_info[table_name] = [
                    {'name': col['column_name'], 
                     'type': col['data_type'], 
                     'nullable': col['is_nullable']} 
                    for col in columns
                ]
                
                # Get row count for each table
                cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
                row_count = cursor.fetchone()[0]
                tables_info[table_name].append({'row_count': row_count})
    except Exception as e:
        logger.error(f"Error retrieving database information: {str(e)}")
    finally:
        conn.close()
        
    return tables_info

def print_tables_info(tables_info: Dict[str, List[Dict[str, Any]]], verbose: bool = False) -> None:
    """
    Print information about tables and their columns.
    
    Args:
        tables_info: Dictionary with table information
        verbose: Whether to print detailed column information
    """
    if not tables_info:
        logger.error("No tables found or error occurred")
        return
        
    print(f"\n{'=' * 60}")
    print(f"BIBLE DATABASE TABLES")
    print(f"{'=' * 60}")
    
    for table_name, columns_info in tables_info.items():
        # Extract row count
        row_count = next((item['row_count'] for item in columns_info if 'row_count' in item), 0)
        # Filter out the row count entry
        columns = [col for col in columns_info if 'row_count' not in col]
        
        print(f"\n{table_name} ({row_count} rows)")
        print(f"{'-' * 40}")
        
        if verbose:
            for col in columns:
                nullable = "NULL" if col['nullable'] == 'YES' else "NOT NULL"
                print(f"  {col['name']} ({col['type']}) {nullable}")
        else:
            print(f"  Columns: {', '.join(col['name'] for col in columns)}")
            
    print(f"\n{'=' * 60}")
    print(f"Total tables: {len(tables_info)}")
    print(f"{'=' * 60}")

def main():
    parser = argparse.ArgumentParser(description="List tables in the bible database schema")
    parser.add_argument('--schema', default='bible', help='Database schema to inspect')
    parser.add_argument('--verbose', action='store_true', help='Show detailed column information')
    args = parser.parse_args()
    
    tables_info = get_tables(args.schema)
    print_tables_info(tables_info, args.verbose)
    
if __name__ == "__main__":
    main() 