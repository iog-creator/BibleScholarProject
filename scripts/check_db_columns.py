#!/usr/bin/env python3
"""
Script to check database columns for the BibleScholarProject.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import local modules
from src.database.connection import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('check_db_columns')

def check_table_columns(conn, schema_name, table_name):
    """Check columns for a specific table."""
    try:
        with conn.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = %s
                );
            """, (schema_name, table_name))
            exists = cursor.fetchone()[0]
            
            if not exists:
                logger.error(f"Table {schema_name}.{table_name} does not exist")
                return
            
            # Get column information
            cursor.execute("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns 
                WHERE table_schema = %s 
                AND table_name = %s
                ORDER BY ordinal_position;
            """, (schema_name, table_name))
            
            columns = cursor.fetchall()
            
            logger.info(f"Columns for {schema_name}.{table_name}:")
            for column in columns:
                column_name, data_type, max_length = column
                length_info = f"({max_length})" if max_length else ""
                logger.info(f"  {column_name}: {data_type}{length_info}")
            
            return columns
    except Exception as e:
        logger.error(f"Error checking columns for {schema_name}.{table_name}: {e}")
        return None

def check_hebrew_tables(conn):
    """Check Hebrew-related tables."""
    logger.info("=== Checking Hebrew Tables ===")
    
    # Check hebrew_entries
    check_table_columns(conn, 'bible', 'hebrew_entries')
    
    # Check hebrew_ot_words
    check_table_columns(conn, 'bible', 'hebrew_ot_words')
    
    # Get sample data from hebrew_entries
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT strongs_id, CASE WHEN hebrew_word IS NULL THEN 'NULL' ELSE 'NOT NULL' END as hebrew_word
                FROM bible.hebrew_entries
                WHERE strongs_id IN ('H430', 'H3068', 'H113', 'H2617', 'H539')
                ORDER BY strongs_id
            """)
            
            critical_terms = cursor.fetchall()
            logger.info("Critical Hebrew terms in hebrew_entries:")
            for term in critical_terms:
                logger.info(f"  {term[0]}: hebrew_word is {term[1]}")
            
            # Check for column name differences
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'bible' 
                    AND table_name = 'hebrew_entries'
                    AND column_name = 'word_text'
                );
            """)
            has_word_text = cursor.fetchone()[0]
            
            if has_word_text:
                logger.info("Column 'word_text' exists in hebrew_entries table")
            else:
                logger.info("Column 'word_text' does NOT exist in hebrew_entries table")
                
    except Exception as e:
        logger.error(f"Error checking Hebrew entries: {e}")

def main():
    """Main function to check database columns."""
    logger.info("Starting database column check")
    
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return 1
        
        try:
            # Check tables
            check_hebrew_tables(conn)
            
            logger.info("Database column check completed successfully")
            return 0
        
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"Error during database column check: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 