"""
Database configuration module.
Provides connection parameters and engine configuration for SQLAlchemy.
"""

import os
from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_params() -> Dict[str, str]:
    """
    Returns a dictionary containing database connection parameters.
    Reads from environment variables with fallbacks to default values.
    """
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'database': os.getenv('POSTGRES_DB', 'bible_db'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'port': os.getenv('POSTGRES_PORT', '5432')
    }

def get_db_url() -> URL:
    """
    Creates a SQLAlchemy URL object for database connection.
    """
    params = get_db_params()
    return URL.create(
        drivername="postgresql+psycopg2",
        username=params['user'],
        password=params['password'],
        host=params['host'],
        port=params['port'],
        database=params['database']
    )

def create_engine_with_retries(max_retries: int = 3, **kwargs: Any):
    """
    Creates a SQLAlchemy engine with retry logic and proper pooling configuration.
    
    Args:
        max_retries: Maximum number of connection retries
        **kwargs: Additional arguments passed to create_engine
    
    Returns:
        SQLAlchemy Engine instance
    """
    url = get_db_url()
    
    # Default engine configuration
    engine_config = {
        # Connection pooling settings
        'poolclass': QueuePool,
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 1800,  # Recycle connections after 30 minutes
        
        # Query execution settings
        'pool_pre_ping': True,  # Enable connection health checks
        'echo': False,  # Set to True for SQL query logging
        
        # PostgreSQL specific settings
        'connect_args': {
            'application_name': 'bible_etl',
            'client_encoding': 'utf8',
            'options': '-c search_path=bible,public',
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
    }
    
    # Update with any additional configuration
    engine_config.update(kwargs)
    
    return create_engine(url, **engine_config) 