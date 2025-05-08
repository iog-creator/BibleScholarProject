"""
Secure database connection utilities with read/write mode support.
Prevents accidental data modification through role-based permissions.
"""

import os
import logging
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/database_connection.log", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_secure_connection(mode='read'):
    """
    Get a database connection with appropriate permissions.
    
    Args:
        mode: Connection mode ('read' or 'write')
            - 'read': Read-only connection, no modifications allowed
            - 'write': Full access, requires BIBLE_DB_WRITE_PASSWORD
    
    Returns:
        psycopg2.connection: Database connection with appropriate permissions
    
    Raises:
        ValueError: If invalid mode or missing write password for write mode
    """
    if mode not in ('read', 'write'):
        raise ValueError("Mode must be 'read' or 'write'")
    
    # Get base connection parameters
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'bible_db')
    
    if mode == 'read':
        # Read-only connection
        db_user = os.getenv('POSTGRES_READ_USER', os.getenv('POSTGRES_USER', 'postgres'))
        db_password = os.getenv('POSTGRES_READ_PASSWORD', os.getenv('POSTGRES_PASSWORD', ''))
        logger.info(f"Connecting to database in READ-ONLY mode as {db_user}")
    else:
        # Write connection - requires specific password
        db_user = os.getenv('POSTGRES_WRITE_USER', os.getenv('POSTGRES_USER', 'postgres'))
        db_password = os.getenv('POSTGRES_WRITE_PASSWORD')
        
        if not db_password:
            raise ValueError(
                "Write mode requires POSTGRES_WRITE_PASSWORD environment variable. "
                "Set this in .env file or environment."
            )
        logger.info(f"Connecting to database with WRITE permissions as {db_user}")
    
    # Create connection with appropriate user
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
            cursor_factory=RealDictCursor
        )
        
        # Set session to read-only if mode is read
        if mode == 'read':
            with conn.cursor() as cursor:
                cursor.execute("SET default_transaction_read_only = true;")
                cursor.execute("SET statement_timeout = '30s';")  # Limit query runtime
            conn.commit()
        
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

@contextmanager
def secure_connection(mode='read'):
    """
    Context manager for secure database connection.
    
    Args:
        mode: Connection mode ('read' or 'write')
    
    Yields:
        psycopg2.connection: Database connection with appropriate permissions
    """
    conn = None
    try:
        conn = get_secure_connection(mode)
        yield conn
    finally:
        if conn:
            conn.close()
            logger.debug(f"Closed {mode} mode database connection")

def setup_database_roles(admin_username, admin_password):
    """
    Set up database roles and permissions for secure access.
    Must be run by a database administrator.
    
    Args:
        admin_username: Administrator username
        admin_password: Administrator password
    
    Returns:
        bool: True if setup was successful, False otherwise
    """
    # Get connection parameters
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'bible_db')
    
    read_user = os.getenv('POSTGRES_READ_USER', 'bible_reader')
    read_password = os.getenv('POSTGRES_READ_PASSWORD', 'bible_read')
    write_user = os.getenv('POSTGRES_WRITE_USER', 'bible_writer')
    write_password = os.getenv('POSTGRES_WRITE_PASSWORD', 'bible_write')
    
    try:
        # Connect as admin
        admin_conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=admin_username,
            password=admin_password
        )
        admin_conn.autocommit = True
        
        with admin_conn.cursor() as cursor:
            # Create reader role if it doesn't exist
            cursor.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{read_user}') THEN
                    CREATE ROLE {read_user} LOGIN PASSWORD %s;
                ELSE
                    ALTER ROLE {read_user} PASSWORD %s;
                END IF;
            END
            $$;
            """, (read_password, read_password))
            
            # Create writer role if it doesn't exist
            cursor.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{write_user}') THEN
                    CREATE ROLE {write_user} LOGIN PASSWORD %s;
                ELSE
                    ALTER ROLE {write_user} PASSWORD %s;
                END IF;
            END
            $$;
            """, (write_password, write_password))
            
            # Grant appropriate permissions
            cursor.execute(f"""
            -- Ensure bible schema exists
            CREATE SCHEMA IF NOT EXISTS bible;
            
            -- Grant read-only permissions
            GRANT USAGE ON SCHEMA bible TO {read_user};
            GRANT SELECT ON ALL TABLES IN SCHEMA bible TO {read_user};
            ALTER DEFAULT PRIVILEGES IN SCHEMA bible GRANT SELECT ON TABLES TO {read_user};
            
            -- Grant write permissions
            GRANT USAGE ON SCHEMA bible TO {write_user};
            GRANT ALL PRIVILEGES ON SCHEMA bible TO {write_user};
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA bible TO {write_user};
            GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA bible TO {write_user};
            ALTER DEFAULT PRIVILEGES IN SCHEMA bible 
                GRANT ALL PRIVILEGES ON TABLES TO {write_user};
            ALTER DEFAULT PRIVILEGES IN SCHEMA bible 
                GRANT ALL PRIVILEGES ON SEQUENCES TO {write_user};
            """)
        
        admin_conn.close()
        logger.info("Database roles and permissions set up successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error setting up database roles: {e}")
        return False

def check_connection_mode(conn):
    """
    Check if a connection is in read-only or write mode.
    
    Args:
        conn: Database connection
        
    Returns:
        str: 'read' if read-only, 'write' if writable
    """
    with conn.cursor() as cursor:
        cursor.execute("SHOW default_transaction_read_only;")
        read_only = cursor.fetchone()['default_transaction_read_only']
        
        if read_only.lower() == 'on':
            return 'read'
        else:
            return 'write' 