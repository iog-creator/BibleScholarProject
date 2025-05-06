#!/usr/bin/env python
"""
Script to load ESV Bible data into the database.
This script processes the ESV Bible file and loads it into the database.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('esv_data_loading.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

# Import the functions from the etl module
from src.etl.etl_english_bible import parse_esv_bible_file, load_esv_bible_data, get_db_connection

def main():
    """Main function to load ESV Bible data."""
    start_time = datetime.now()
    logger.info("Starting ESV Bible data loading process")
    
    try:
        # Define the path to the ESV Bible file
        esv_file_path = os.path.join(
            "STEPBible-Data", 
            "Tagged-Bibles", 
            "TTESV - Tyndale Translation tags for ESV - TyndaleHouse.com STEPBible.org CC BY-NC.txt"
        )
        
        # Check if the file exists
        if not os.path.exists(esv_file_path):
            logger.error(f"ESV Bible file not found at {esv_file_path}")
            return 1
        
        # Parse the ESV Bible file
        logger.info(f"Parsing ESV Bible file from {esv_file_path}")
        bible_data = parse_esv_bible_file(esv_file_path)
        
        # Get database connection
        logger.info("Connecting to database")
        conn = get_db_connection()
        
        # Load the data into the database
        logger.info("Loading ESV Bible data into database")
        load_esv_bible_data(conn, bible_data)
        
        # Close the database connection
        conn.close()
        
        end_time = datetime.now()
        elapsed_time = end_time - start_time
        logger.info(f"ESV Bible data loading completed in {elapsed_time}")
        logger.info(f"Loaded {len(bible_data['verses'])} ESV verses into the database")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error during ESV Bible data loading: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 