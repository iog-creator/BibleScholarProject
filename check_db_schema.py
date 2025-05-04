#!/usr/bin/env python3
"""
Script to check the database schema and identify table structures.
"""

import os
import logging
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Create and return a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'bible_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def get_schema_info():
    """
    Retrieve information about the database schema.
    """
    conn = None
    try:
        logger.info("Connecting to database...")
        conn = get_db_connection()
        
        if conn is None:
            logger.error("Failed to connect to database")
            return
            
        logger.info("Checking schema structure...")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get list of tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'bible' 
                ORDER BY table_name
            """)
            
            tables = cur.fetchall()
            logger.info(f"Found {len(tables)} tables in schema 'bible':")
            
            # For each table, get column information
            for table in tables:
                table_name = table['table_name']
                logger.info(f"\n=== Table: {table_name} ===")
                
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'bible' AND table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = cur.fetchall()
                logger.info(f"Found {len(columns)} columns:")
                
                for column in columns:
                    nullable = "NULL" if column['is_nullable'] == 'YES' else "NOT NULL"
                    logger.info(f"  - {column['column_name']} ({column['data_type']}) {nullable}")
                
                # Get indexes for this table
                cur.execute("""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'bible' AND tablename = %s
                """, (table_name,))
                
                indexes = cur.fetchall()
                if indexes:
                    logger.info(f"Found {len(indexes)} indexes:")
                    for idx in indexes:
                        logger.info(f"  - {idx['indexname']}: {idx['indexdef']}")
                else:
                    logger.info("No indexes found.")
            
            # Get schema size information
            cur.execute("""
                SELECT 
                    relname as table_name,
                    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
                    pg_size_pretty(pg_relation_size(relid)) as data_size,
                    pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as external_size
                FROM pg_catalog.pg_statio_user_tables
                WHERE schemaname = 'bible'
                ORDER BY pg_total_relation_size(relid) DESC
            """)
            
            sizes = cur.fetchall()
            logger.info("\n=== Table Sizes ===")
            for size in sizes:
                logger.info(f"  - {size['table_name']}: Total={size['total_size']}, Data={size['data_size']}, External={size['external_size']}")
                
    except Exception as e:
        logger.error(f"Error checking schema: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    get_schema_info() 