#!/usr/bin/env python3
"""
Test script to verify database connection and insertion capabilities.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from project modules
from src.database.connection import get_engine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection and perform a basic insert."""
    try:
        # Get database engine
        engine = get_engine()
        logger.info("Successfully connected to database")
        
        # Test creating schema and table if they don't exist
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE SCHEMA IF NOT EXISTS bible;
                
                CREATE TABLE IF NOT EXISTS bible.versification_mappings (
                    id SERIAL PRIMARY KEY,
                    source_tradition VARCHAR(50),
                    target_tradition VARCHAR(50),
                    source_book VARCHAR(10),
                    source_chapter VARCHAR(10),
                    source_verse INTEGER,
                    source_subverse VARCHAR(5),
                    manuscript_marker VARCHAR(50),
                    target_book VARCHAR(10),
                    target_chapter VARCHAR(10),
                    target_verse INTEGER,
                    target_subverse VARCHAR(5),
                    mapping_type VARCHAR(20)
                );
            """))
            conn.commit()
            logger.info("Schema and table created/verified")
        
        # Insert a test record
        with engine.begin() as conn:
            # Test edge cases for integration tests
            test_mappings = [
                {
                    'source_tradition': 'test',
                    'target_tradition': 'test',
                    'source_book': 'Psa',
                    'source_chapter': '3',
                    'source_verse': 0,
                    'source_subverse': None,
                    'manuscript_marker': None,
                    'target_book': 'Psa',
                    'target_chapter': '3',
                    'target_verse': 0,
                    'target_subverse': None,
                    'mapping_type': 'Test'
                },
                {
                    'source_tradition': 'test',
                    'target_tradition': 'test',
                    'source_book': '3Jo',
                    'source_chapter': '1',
                    'source_verse': 15,
                    'source_subverse': None,
                    'manuscript_marker': None,
                    'target_book': '3Jo',
                    'target_chapter': '1',
                    'target_verse': 15,
                    'target_subverse': None,
                    'mapping_type': 'Test'
                },
                {
                    'source_tradition': 'test',
                    'target_tradition': 'test',
                    'source_book': 'Rev',
                    'source_chapter': '12',
                    'source_verse': 18,
                    'source_subverse': None,
                    'manuscript_marker': None,
                    'target_book': 'Rev',
                    'target_chapter': '12',
                    'target_verse': 18,
                    'target_subverse': None,
                    'mapping_type': 'Test'
                },
                {
                    'source_tradition': 'test',
                    'target_tradition': 'test',
                    'source_book': 'Act',
                    'source_chapter': '19',
                    'source_verse': 41,
                    'source_subverse': None,
                    'manuscript_marker': None,
                    'target_book': 'Act',
                    'target_chapter': '19',
                    'target_verse': 41,
                    'target_subverse': None,
                    'mapping_type': 'Test'
                }
            ]
            
            # Clear existing test records
            conn.execute(text("DELETE FROM bible.versification_mappings WHERE source_tradition = 'test'"))
            
            # Insert test records
            for mapping in test_mappings:
                conn.execute(
                    text("""
                    INSERT INTO bible.versification_mappings 
                    (source_tradition, target_tradition, source_book, source_chapter, 
                     source_verse, source_subverse, manuscript_marker, target_book, 
                     target_chapter, target_verse, target_subverse, mapping_type)
                    VALUES 
                    (:source_tradition, :target_tradition, :source_book, :source_chapter, 
                     :source_verse, :source_subverse, :manuscript_marker, :target_book, 
                     :target_chapter, :target_verse, :target_subverse, :mapping_type)
                    """),
                    mapping
                )
            
            logger.info(f"Successfully inserted {len(test_mappings)} test records")
        
        # Verify records were inserted
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM bible.versification_mappings WHERE source_tradition = 'test'"))
            count = result.scalar()
            logger.info(f"Found {count} test records in database")
            
            # Show the records
            result = conn.execute(text("SELECT * FROM bible.versification_mappings WHERE source_tradition = 'test'"))
            for row in result:
                logger.info(f"Test record: {row}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        logger.info("Database test completed successfully")
        sys.exit(0)
    else:
        logger.error("Database test failed")
        sys.exit(1) 