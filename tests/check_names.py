#!/usr/bin/env python3
"""
Script to verify the proper names data loaded in the database.

This script performs validation and analysis of the proper names data loaded by etl_proper_names.py.
It checks data integrity, provides statistics, and displays sample entries to verify proper loading.

Features:
- Counts total records and entries by type (documentation/name)
- Displays sample documentation entries
- Shows sample name entries with the most references
- Identifies entries with special markers (ambiguous, descendant, ancestor)
- Uses dict_row for more readable output

Database Schema Used:
-------------------
Table: bible.proper_names
- id: SERIAL PRIMARY KEY
- name_text: TEXT NOT NULL
- name_text_searchable: TEXT GENERATED
- meta_data: JSONB NOT NULL

Sample Queries:
-------------
1. Total record count
2. Type distribution (documentation vs name entries)
3. Sample documentation entries
4. Sample name entries with the most references
5. Entries with special markers

Usage:
    python check_names.py

Environment Variables:
--------------------
- POSTGRES_HOST: Database host (default: localhost)
- POSTGRES_PORT: Database port (default: 5432)
- POSTGRES_DB: Database name (default: bible_db)
- POSTGRES_USER: Database user (default: postgres)
- POSTGRES_PASSWORD: Database password

Dependencies:
------------
- psycopg
- python-dotenv
- logging
"""

import psycopg
from psycopg.rows import dict_row
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a database connection with proper error handling."""
    return psycopg.connect(
        dbname="bible_db",
        user="postgres",
        password="postgres",
        host="localhost",
        application_name='bible_data_check',
        row_factory=dict_row
    )

def main():
    """Check the loaded proper names data."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get total count
                cur.execute("SELECT COUNT(*) as total FROM bible.proper_names")
                total = cur.fetchone()['total']
                logger.info(f"Total records: {total}")
                
                # Get counts by type
                cur.execute("""
                    SELECT meta_data->>'type' as entry_type, COUNT(*) as count 
                    FROM bible.proper_names 
                    GROUP BY meta_data->>'type'
                """)
                type_counts = cur.fetchall()
                logger.info("\nCounts by type:")
                for row in type_counts:
                    logger.info(f"  {row['entry_type']}: {row['count']}")
                    
                # Sample documentation entries
                logger.info("\nSample documentation entries:")
                cur.execute("""
                    SELECT name_text, meta_data 
                    FROM bible.proper_names 
                    WHERE meta_data->>'type' = 'documentation'
                    LIMIT 3
                """)
                for row in cur.fetchall():
                    logger.info(f"\nDocumentation entry:")
                    logger.info(f"Text: {row['name_text']}")
                    logger.info(f"Metadata: {json.dumps(row['meta_data'], indent=2)}")
                    
                # Sample name entries with most references
                logger.info("\nSample name entries with most references:")
                cur.execute("""
                    SELECT name_text, meta_data,
                           jsonb_array_length(meta_data->'references') as ref_count
                    FROM bible.proper_names 
                    WHERE meta_data->>'type' = 'name'
                    ORDER BY jsonb_array_length(meta_data->'references') DESC
                    LIMIT 3
                """)
                for row in cur.fetchall():
                    logger.info(f"\nName entry:")
                    logger.info(f"Name: {row['name_text']}")
                    logger.info(f"Reference count: {row['ref_count']}")
                    logger.info(f"Metadata: {json.dumps(row['meta_data'], indent=2)}")
                    
                # Check for any entries with markers
                logger.info("\nSample entries with special markers:")
                cur.execute("""
                    SELECT name_text, meta_data 
                    FROM bible.proper_names 
                    WHERE jsonb_array_length(meta_data->'markers') > 0
                    LIMIT 3
                """)
                for row in cur.fetchall():
                    logger.info(f"\nMarked entry:")
                    logger.info(f"Name: {row['name_text']}")
                    logger.info(f"Markers: {json.dumps(row['meta_data']['markers'], indent=2)}")
                    
    except Exception as e:
        logger.error(f"Error checking data: {str(e)}")
        raise

if __name__ == "__main__":
    main() 