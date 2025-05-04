"""
Database utilities for the STEPBible Explorer project.

This module contains utility functions for database operations.
"""
import logging
import psycopg2
from psycopg2 import sql

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Create a new database connection.
    This is the main function used by API modules to get a database connection.
    
    Returns:
        connection: PostgreSQL database connection
    """
    return get_connection_from_env()

def get_connection_from_env():
    """
    Create a database connection using environment variables.
    
    Requires DB_HOST, DB_NAME, DB_USER, and DB_PASSWORD in environment.
    
    Returns:
        connection: PostgreSQL database connection
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "bible_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )
    return conn

def execute_query(conn, query, params=None, fetch=True):
    """
    Execute a SQL query with proper error handling.
    
    Args:
        conn: Database connection
        query (str): SQL query
        params (tuple, optional): Query parameters
        fetch (bool): Whether to fetch results
        
    Returns:
        list: Query results (if fetch=True), otherwise None
    """
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if fetch:
            return cursor.fetchall()
        return None
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def batch_insert(conn, table_name, columns, data, batch_size=1000):
    """
    Insert data in batches for better performance.
    
    Args:
        conn: Database connection
        table_name (str): Table to insert into
        columns (list): Column names
        data (list): List of tuples containing row data
        batch_size (int): Number of rows per batch
        
    Returns:
        int: Number of rows inserted
    """
    cursor = conn.cursor()
    total_inserted = 0
    
    # Create the query
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join([sql.Identifier(col).as_string(conn) for col in columns])
    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    
    try:
        # Process in batches
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            cursor.executemany(query, batch)
            conn.commit()
            total_inserted += len(batch)
            logger.info(f"Inserted {len(batch)} rows into {table_name} (total: {total_inserted})")
    
    except Exception as e:
        logger.error(f"Error during batch insert: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        
    return total_inserted 