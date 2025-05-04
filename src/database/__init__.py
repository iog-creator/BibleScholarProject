"""
Database module for the STEPBible Explorer application.

This module provides database connection and utilities.
"""

import os
import psycopg
from psycopg.rows import dict_row
from pathlib import Path

__version__ = '0.1.0'

def get_db_connection(dbname="bible_db"):
    """Get a connection to the database."""
    return psycopg.connect(
        dbname=dbname,
        user="postgres",
        password="postgres",
        host="localhost",
        row_factory=dict_row
    )

def init_db(drop_existing=False):
    """Initialize the database with schema."""
    # Connect to default database first
    conn = get_db_connection("postgres")
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            # Terminate all connections to the database
            cur.execute("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'bible_db'
                AND pid <> pg_backend_pid()
            """)
            
            # Drop database if it exists and drop_existing is True
            if drop_existing:
                cur.execute("DROP DATABASE IF EXISTS bible_db")
            
            # Create database if it doesn't exist
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'bible_db'")
            if not cur.fetchone():
                cur.execute("CREATE DATABASE bible_db")
    finally:
        conn.close()
    
    # Now connect to our database and create schema
    conn = get_db_connection("bible_db")
    try:
        with conn.cursor() as cur:
            # Read and execute the schema file
            schema_path = Path(__file__).parent.parent.parent / 'sql' / 'unified_schema.sql'
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            cur.execute(schema_sql)
            conn.commit()
    finally:
        conn.close()

from .connection import get_db_connection, get_connection_string

__all__ = ['get_db_connection', 'get_connection_string'] 