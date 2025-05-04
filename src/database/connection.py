"""
Database connection utilities for the STEPBible Explorer application.
"""

import os
import logging
import psycopg2
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Get a connection to the PostgreSQL database.
    
    Returns:
        psycopg2.connection: Connection object or None if connection fails
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Get connection parameters from environment variables
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'bible_db')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        
        # Ensure the bible schema exists
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE SCHEMA IF NOT EXISTS bible;
            """)
            conn.commit()
        
        return conn
    
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def get_connection_string():
    """
    Get the PostgreSQL connection string based on environment variables.
    
    Returns:
        str: The connection string
    """
    # Load environment variables
    load_dotenv()
    
    # Get connection parameters from environment variables
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'bible_db')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}" 