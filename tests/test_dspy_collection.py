#!/usr/bin/env python
"""
Test script to verify DSPy training data collection is triggered automatically.
"""

import os
import sys
import logging
import json
import psycopg2
from datetime import datetime
import hashlib
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dspy_collection_test.log', 'w')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent
STATE_FILE_PATH = PROJECT_ROOT / "data" / "processed" / "dspy_training_data" / ".state.json"

def get_db_connection():
    """Create a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname="bible_db",
            user="postgres",
            password="postgres",
            host="localhost"
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def load_current_state():
    """Load the current DSPy state file."""
    try:
        if not os.path.exists(STATE_FILE_PATH):
            logger.warning(f"State file not found at {STATE_FILE_PATH}")
            return None
            
        with open(STATE_FILE_PATH, 'r') as f:
            state_data = json.load(f)
            
        logger.info(f"Current state hash: {state_data.get('hash', 'N/A')}")
        logger.info(f"Last updated: {state_data.get('last_updated', 'N/A')}")
        
        return state_data
    except Exception as e:
        logger.error(f"Error loading state file: {e}")
        return None

def make_test_change():
    """Make a small change to a verse to trigger collection."""
    conn = None
    try:
        logger.info("Making test change to trigger DSPy collection...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First, get the current text of John 3:16
        cursor.execute(
            """
            SELECT verse_text FROM bible.verses 
            WHERE book_name = 'John' AND chapter_num = 3 AND verse_num = 16 AND translation_source = 'KJV'
            """
        )
        current_text = cursor.fetchone()
        
        if not current_text:
            logger.error("Test verse not found (John 3:16 KJV)")
            return False
            
        # Add a timestamp to make a small change
        new_text = f"{current_text[0]} [TEST {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        
        # Update the verse
        cursor.execute(
            """
            UPDATE bible.verses 
            SET verse_text = %s, updated_at = %s
            WHERE book_name = 'John' AND chapter_num = 3 AND verse_num = 16 AND translation_source = 'KJV'
            """,
            (new_text, datetime.now())
        )
        
        # Commit the change
        conn.commit()
        logger.info("Test change applied successfully")
        
        # Import and trigger DSPy collection
        try:
            from src.utils import dspy_collector
            logger.info("Triggering DSPy collection...")
            result = dspy_collector.trigger_after_verse_insertion(conn, 'KJV')
            logger.info(f"DSPy collection triggered, result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error triggering DSPy collection: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error making test change: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def verify_state_changed(old_state):
    """Verify that the state file has changed."""
    try:
        # Load new state
        new_state = load_current_state()
        
        if not new_state:
            logger.error("Could not load new state file")
            return False
            
        if not old_state:
            logger.warning("No old state to compare against")
            return True
            
        # Compare timestamps
        old_timestamp = old_state.get('last_updated', 'N/A')
        new_timestamp = new_state.get('last_updated', 'N/A')
        
        if old_timestamp != new_timestamp:
            logger.info(f"State file timestamp changed: {old_timestamp} -> {new_timestamp}")
            return True
        else:
            logger.warning("State file timestamp did not change")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying state change: {e}")
        return False

def main():
    """Run the DSPy collection test."""
    logger.info("Starting DSPy collection test")
    
    try:
        # Load current state
        old_state = load_current_state()
        
        # Make test change to trigger collection
        collection_triggered = make_test_change()
        
        if not collection_triggered:
            logger.error("Failed to trigger DSPy collection")
            return 1
            
        # Check for state change
        state_changed = verify_state_changed(old_state)
        
        if state_changed:
            logger.info("SUCCESS: DSPy collection system worked correctly!")
            print("\nSUCCESS: DSPy collection system worked correctly!")
            print("The system detected changes and updated the training data.")
            return 0
        else:
            logger.warning("WARNING: State file did not change after test")
            print("\nWARNING: DSPy collection system may not be working correctly.")
            print("The state file did not change after the test change.")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error in DSPy collection test: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 