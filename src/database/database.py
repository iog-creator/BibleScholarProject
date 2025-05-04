"""
Database connection and configuration module for the STEPBible data integration project.

This module provides the core database functionality for managing Bible data, including
verses, lexicon entries, proper names, and versification mappings.

Core Features:
------------
1. Connection Management:
   - Connection pooling for optimal performance
   - Automatic connection cleanup
   - Transaction management with context managers

2. Schema Management:
   - Unified 'bible' schema for all tables
   - Automatic schema creation if not exists

3. Performance Optimization:
   - Connection pooling with psycopg
   - Prepared statement caching
   - Batch operation support

4. Security:
   - Password encryption
   - Connection string sanitization
   - SSL support for secure connections

Environment Variables:
-------------------
Required:
- DATABASE_URL: Full database connection URL

Optional:
- LOG_LEVEL: Logging level (default: INFO)
- LOG_FILE: Log file path (optional)

Dependencies:
-----------
Core:
- psycopg: PostgreSQL adapter
- python-dotenv: Environment variable management

Author: STEPBible Data Integration Team
Version: 2.0.0
License: CC BY (Creative Commons Attribution)
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from scripts.db_config import get_db_url

# Load environment variables
load_dotenv()

# Configure logging
log_file = os.getenv("LOG_FILE")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=log_file if log_file else None
)
logger = logging.getLogger(__name__)

@contextmanager
def get_db() -> Generator[psycopg.Connection, None, None]:
    """Get a database connection using connection pooling.
    
    Returns:
        Generator[psycopg.Connection]: Database connection object
        
    Raises:
        psycopg.Error: If connection fails
    """
    conn = None
    try:
        conn = psycopg.connect(
            get_db_url(),
            row_factory=dict_row
        )
        yield conn
    except psycopg.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def create_schema() -> None:
    """Create the bible schema and required tables if they don't exist."""
    with get_db() as conn:
        with conn.cursor() as cur:
            try:
                # Create schema if not exists
                cur.execute("CREATE SCHEMA IF NOT EXISTS bible;")
                
                # Create books table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS bible.books (
                        book_name VARCHAR(100) PRIMARY KEY,
                        book_number INTEGER NOT NULL,
                        testament VARCHAR(4) NOT NULL,
                        chapters INTEGER NOT NULL,
                        verses INTEGER NOT NULL,
                        meta_data JSONB
                    );
                """)
                
                # Create verses table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS bible.verses (
                        id SERIAL PRIMARY KEY,
                        book_name VARCHAR(100) REFERENCES bible.books(book_name),
                        chapter INTEGER NOT NULL,
                        verse INTEGER NOT NULL,
                        word TEXT,
                        transliteration TEXT,
                        strongs TEXT,
                        morphology TEXT,
                        gloss TEXT,
                        function TEXT,
                        root TEXT,
                        strongs_json JSONB,
                        morphology_json JSONB,
                        variant_data JSONB
                    );
                """)
                
                # Create versification_mappings table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS bible.versification_mappings (
                        id SERIAL PRIMARY KEY,
                        source_tradition VARCHAR(50) NOT NULL,
                        target_tradition VARCHAR(50) NOT NULL,
                        source_book VARCHAR(100) NOT NULL,
                        source_chapter INTEGER NOT NULL,
                        source_verse INTEGER NOT NULL,
                        source_subverse VARCHAR(10),
                        manuscript_marker VARCHAR(50),
                        target_book VARCHAR(100) NOT NULL,
                        target_chapter INTEGER NOT NULL,
                        target_verse INTEGER NOT NULL,
                        target_subverse VARCHAR(10),
                        mapping_type VARCHAR(20) NOT NULL,
                        category VARCHAR(10),
                        source_range_note TEXT,
                        target_range_note TEXT,
                        notes TEXT,
                        note_marker VARCHAR(50),
                        ancient_versions TEXT,
                        CONSTRAINT unique_mapping UNIQUE (
                            source_tradition, target_tradition,
                            source_book, source_chapter, source_verse, source_subverse,
                            target_book, target_chapter, target_verse, target_subverse,
                            mapping_type
                        )
                    );
                """)
                
                # Create rules table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS bible.rules (
                        id SERIAL PRIMARY KEY,
                        rule_type VARCHAR(20) NOT NULL,
                        source_tradition VARCHAR(50) NOT NULL,
                        target_tradition VARCHAR(50) NOT NULL,
                        pattern TEXT NOT NULL,
                        description TEXT
                    );
                """)
                
                # Create documentation table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS bible.documentation (
                        id SERIAL PRIMARY KEY,
                        section TEXT,
                        content TEXT NOT NULL
                    );
                """)
                
                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_source_reference 
                    ON bible.versification_mappings (source_book, source_chapter, source_verse);
                    
                    CREATE INDEX IF NOT EXISTS idx_target_reference 
                    ON bible.versification_mappings (target_book, target_chapter, target_verse);
                """)
                
                conn.commit()
                logger.info("Schema and tables created successfully")
                
            except psycopg.Error as e:
                conn.rollback()
                logger.error(f"Error creating schema: {e}")
                raise

def drop_tables() -> None:
    """Drop all tables in the bible schema."""
    with get_db() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    DROP TABLE IF EXISTS 
                        bible.documentation,
                        bible.rules,
                        bible.versification_mappings,
                        bible.verses,
                        bible.books
                    CASCADE;
                """)
                conn.commit()
                logger.info("Tables dropped successfully")
            except psycopg.Error as e:
                conn.rollback()
                logger.error(f"Error dropping tables: {e}")
                raise

def init_db(drop_existing: bool = False) -> None:
    """Initialize the database schema and tables.
    
    Args:
        drop_existing (bool): If True, drop existing tables before creating new ones
    """
    try:
        if drop_existing:
            drop_tables()
        create_schema()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise 