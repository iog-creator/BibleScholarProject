#!/usr/bin/env python3
"""
DSPy Data Collection Utility

This module provides utilities to automatically collect DSPy training data
based on changes to the Bible database. It tracks database states to determine
when regeneration is needed and provides hooks for scripts to trigger collection.
"""

import os
import sys
import json
import logging
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/dspy_collector.log', 'a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DSPY_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "generate_dspy_training_data.py"
STATE_FILE_PATH = PROJECT_ROOT / "data" / "processed" / "dspy_training_data" / ".state.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "dspy_training_data"

def get_db_state_hash(conn):
    """
    Generate a hash that represents the current state of relevant database tables.
    
    Args:
        conn: Database connection object
        
    Returns:
        str: Hash representing current database state
    """
    try:
        cursor = conn.cursor()
        
        # Get translation verse counts
        cursor.execute("""
            SELECT translation_source, COUNT(*) 
            FROM bible.verses 
            GROUP BY translation_source
            ORDER BY translation_source
        """)
        translation_counts = cursor.fetchall()
        
        # Get theological term counts
        cursor.execute("""
            SELECT strongs_id, COUNT(*) 
            FROM bible.hebrew_ot_words
            WHERE strongs_id IN ('H430', 'H3068', 'H113', 'H2617', 'H539')
            GROUP BY strongs_id
            ORDER BY strongs_id
        """)
        theological_counts = cursor.fetchall()
        
        # Combine data for hashing
        state_data = {
            "translation_counts": translation_counts,
            "theological_counts": theological_counts,
            "timestamp": datetime.now().isoformat()
        }
        
        # Generate hash
        state_str = json.dumps(state_data, sort_keys=True)
        state_hash = hashlib.sha256(state_str.encode()).hexdigest()
        
        return state_hash, state_data
    
    except Exception as e:
        logger.error(f"Error getting database state: {e}")
        return None, None

def save_state(state_hash, state_data):
    """Save the current state hash to a file."""
    os.makedirs(os.path.dirname(STATE_FILE_PATH), exist_ok=True)
    
    try:
        with open(STATE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump({
                "hash": state_hash,
                "data": state_data,
                "last_updated": datetime.now().isoformat()
            }, f, indent=2)
        logger.info(f"Saved database state hash: {state_hash}")
        return True
    except Exception as e:
        logger.error(f"Error saving state file: {e}")
        return False

def load_state():
    """Load the previous state hash from file."""
    if not os.path.exists(STATE_FILE_PATH):
        logger.info("No previous state file found")
        return None, None
    
    try:
        with open(STATE_FILE_PATH, 'r', encoding='utf-8') as f:
            state_info = json.load(f)
        return state_info.get("hash"), state_info.get("data")
    except Exception as e:
        logger.error(f"Error loading state file: {e}")
        return None, None

def run_dspy_generation(force=False):
    """
    Run the DSPy training data generation script.
    
    Args:
        force: If True, force regeneration regardless of state
        
    Returns:
        bool: Success or failure
    """
    try:
        # Call the script
        logger.info(f"Running DSPy generation script: {DSPY_SCRIPT_PATH}")
        
        # Run the script as a subprocess
        result = subprocess.run(
            [sys.executable, str(DSPY_SCRIPT_PATH)],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log output
        logger.info(f"DSPy generation completed successfully")
        logger.debug(f"Script output: {result.stdout}")
        
        if result.stderr:
            logger.warning(f"Script warnings/errors: {result.stderr}")
        
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running DSPy generation script: {e}")
        logger.error(f"Script output: {e.stdout}")
        logger.error(f"Script errors: {e.stderr}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error running DSPy generation: {e}")
        return False

def check_and_trigger_generation(conn, force=False, translation_source=None):
    """
    Check if we need to regenerate DSPy training data and trigger if needed.
    
    Args:
        conn: Database connection
        force: Force regeneration regardless of state
        translation_source: The translation being modified (for logging)
        
    Returns:
        bool: Whether generation was triggered
    """
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # If force is True, skip state check
    if force:
        logger.info("Forcing DSPy training data regeneration")
        success = run_dspy_generation(force=True)
        if success:
            # Get and save new state after generation
            new_hash, new_data = get_db_state_hash(conn)
            if new_hash:
                save_state(new_hash, new_data)
        return success
    
    # Get current database state
    current_hash, current_data = get_db_state_hash(conn)
    if not current_hash:
        logger.error("Failed to get current database state")
        return False
    
    # Load previous state
    previous_hash, previous_data = load_state()
    
    # Determine if regeneration is needed
    regeneration_needed = False
    
    if not previous_hash:
        logger.info("No previous state found, initial generation needed")
        regeneration_needed = True
    elif previous_hash != current_hash:
        logger.info(f"Database state changed, regeneration needed")
        logger.info(f"Previous hash: {previous_hash}")
        logger.info(f"Current hash: {current_hash}")
        
        # Log what changed if we have the data
        if previous_data and current_data:
            prev_trans = dict(previous_data.get("translation_counts", []))
            curr_trans = dict(current_data.get("translation_counts", []))
            
            for trans, count in curr_trans.items():
                if trans not in prev_trans:
                    logger.info(f"New translation added: {trans} with {count} verses")
                elif prev_trans[trans] != count:
                    logger.info(f"Translation {trans} count changed: {prev_trans[trans]} -> {count}")
        
        regeneration_needed = True
    else:
        logger.info(f"Database state unchanged, no regeneration needed")
        if translation_source:
            logger.info(f"Note: Changes to {translation_source} did not affect overall database state hash")
    
    # Run generation if needed
    if regeneration_needed:
        success = run_dspy_generation()
        if success:
            # Save new state after successful generation
            save_state(current_hash, current_data)
        return success
    
    return False

def trigger_after_verse_insertion(conn, translation_source):
    """
    Hook to trigger after verse insertion.
    
    Args:
        conn: Database connection
        translation_source: The translation that was inserted
    """
    logger.info(f"Verse insertion hook triggered for {translation_source}")
    return check_and_trigger_generation(conn, translation_source=translation_source)

def trigger_after_etl_process(conn, process_name):
    """
    Hook to trigger after an ETL process completes.
    
    Args:
        conn: Database connection
        process_name: Name of the ETL process
    """
    logger.info(f"ETL process hook triggered for {process_name}")
    return check_and_trigger_generation(conn)

def trigger_after_morphology_update(conn):
    """
    Hook to trigger after morphology data is updated.
    
    Args:
        conn: Database connection
    """
    logger.info("Morphology update hook triggered")
    return check_and_trigger_generation(conn)

def force_regeneration(conn=None):
    """
    Force regeneration of all DSPy training data.
    
    Args:
        conn: Database connection (optional)
    """
    if conn:
        return check_and_trigger_generation(conn, force=True)
    else:
        return run_dspy_generation(force=True) 