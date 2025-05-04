"""
Database connection utilities for the STEPBible Explorer application.
"""

import os
import logging
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_connection.log'),
        logging.StreamHandler()
    ]
)
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
        
        logger.info(f"Connecting to database: {db_name} on {db_host}:{db_port} as user {db_user}")
        
        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        
        logger.info("Database connection successful")
        
        # Ensure the bible schema exists
        with conn.cursor() as cursor:
            # Check if the schema exists first
            cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'bible');")
            schema_exists = cursor.fetchone()[0]
            
            if not schema_exists:
                logger.info("Creating 'bible' schema as it does not exist")
                cursor.execute("CREATE SCHEMA bible;")
                conn.commit()
            else:
                logger.info("'bible' schema already exists")
                
            # Check if required tables exist
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'bible' 
                AND table_name IN ('hebrew_ot_words', 'hebrew_entries', 'verses');
            """)
            table_count = cursor.fetchone()[0]
            
            if table_count < 3:
                logger.warning(f"Some required tables are missing. Found {table_count}/3 core tables.")
                
                # List the tables that exist
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'bible'
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()
                logger.info(f"Existing tables in 'bible' schema: {', '.join([t[0] for t in tables])}")
        
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

def check_table_exists(conn, schema_name, table_name):
    """
    Check if a specific table exists in the database.
    
    Args:
        conn: Database connection
        schema_name: Schema name
        table_name: Table name
        
    Returns:
        bool: True if the table exists, False otherwise
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = %s
                );
            """, (schema_name, table_name))
            exists = cursor.fetchone()[0]
            logger.debug(f"Table {schema_name}.{table_name} exists: {exists}")
            return exists
    except Exception as e:
        logger.error(f"Error checking if table {schema_name}.{table_name} exists: {e}")
        return False 