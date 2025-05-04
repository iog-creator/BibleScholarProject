#!/usr/bin/env python3
"""
ETL script for processing Greek morphology codes from the TEGMC file.
This script extracts and loads morphology code definitions into the database
for lookup and reference in tagged text processing.
"""

import os
import sys
import logging
import argparse
import psycopg2
from dotenv import load_dotenv
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_greek_morphology.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('etl_greek_morphology')

def create_tables(conn):
    """Create the necessary tables for Greek morphology codes if they don't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bible.greek_morphology_codes (
                id SERIAL PRIMARY KEY,
                code TEXT NOT NULL,
                code_type TEXT NOT NULL,
                description TEXT NOT NULL,
                explanation TEXT,
                example TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (code, code_type)
            )
        """)
        
        # Create indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_greek_morphology_code
            ON bible.greek_morphology_codes (code)
        """)
        
        conn.commit()
        logger.info("Greek morphology tables created or already exist")

def parse_morphology_file(file_path):
    """
    Parse the TEGMC file to extract morphology codes and their explanations.
    
    The file has specific sections for brief and full morphology codes.
    Each code entry in the full section is delimited by a '$' character.
    
    Returns a list of dictionaries with the parsed data.
    """
    morphology_data = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Split by lines to find section markers
            lines = content.split('\n')
            
            # Identify sections
            brief_section_start = -1
            full_section_start = -1
            
            for i, line in enumerate(lines):
                if "BRIEF LEXICAL MORPHOLOGY CODES:" in line:
                    brief_section_start = i
                elif "FULL MORPHOLOGY CODES:" in line:
                    full_section_start = i
            
            # Keep track of unique codes to avoid duplicates
            unique_codes = {}
            
            # Process brief codes section if found
            brief_codes = []
            if brief_section_start >= 0:
                logger.info(f"Found brief codes section at line {brief_section_start}")
                # Start processing a few lines after the header to skip explanatory text
                i = brief_section_start + 5
                while i < len(lines) and (full_section_start == -1 or i < full_section_start):
                    line = lines[i].strip()
                    # Better pattern matching for brief codes
                    if re.match(r'^(G:|A:|H:|N:|V-|N-|A-|P-|G\.|A\.|N\.)', line):
                        parts = line.split('\t')
                        if len(parts) >= 1:
                            code = parts[0].strip()
                            # Create a unique key for code/type combination
                            unique_key = f"{code}|brief"
                            
                            # Skip if we've already seen this code
                            if unique_key in unique_codes:
                                i += 1
                                continue
                                
                            example = parts[1].strip() if len(parts) > 1 else ""
                            description = parts[2].strip() if len(parts) > 2 else ""
                            
                            # Add to unique codes dict
                            unique_codes[unique_key] = True
                            
                            brief_codes.append({
                                'code': code,
                                'code_type': 'brief',
                                'description': description,
                                'explanation': None,
                                'example': example
                            })
                    i += 1
                
                logger.info(f"Parsed {len(brief_codes)} brief codes")
            
            # Process full codes section if found
            full_codes = []
            if full_section_start >= 0:
                logger.info(f"Found full codes section at line {full_section_start}")
                
                # Implementation of a state machine approach to parse the full morphology codes
                STATE_LOOKING_FOR_DELIMITER = 0  # Looking for $ delimiter
                STATE_READING_CODE = 1          # Reading the code line (first line)
                STATE_READING_DESCRIPTION = 2   # Reading the description (second line)
                STATE_READING_EXPLANATION = 3   # Reading the explanation (third line) 
                STATE_READING_EXAMPLE = 4       # Reading the example (fourth line)
                
                state = STATE_LOOKING_FOR_DELIMITER
                current_code = {}
                
                for i in range(full_section_start, len(lines)):
                    line = lines[i].strip()
                    
                    if state == STATE_LOOKING_FOR_DELIMITER:
                        if line == '$':
                            # Start of a new code entry
                            state = STATE_READING_CODE
                            current_code = {
                                'code': '',
                                'code_type': 'full',
                                'description': '',
                                'explanation': '',
                                'example': ''
                            }
                    
                    elif state == STATE_READING_CODE:
                        if line:  # Non-empty line
                            # Extract the code from the line
                            # The code is typically the first "word" before whitespace or Function=
                            code_match = re.match(r'^([^\s]+)', line)
                            if code_match:
                                code = code_match.group(1).strip()
                                current_code['code'] = code
                                
                                # Add the rest of the line as function description
                                rest_of_line = line[len(code):].strip()
                                if rest_of_line:
                                    current_code['description'] = rest_of_line
                                
                                state = STATE_READING_DESCRIPTION
                            else:
                                # If we couldn't extract a code, reset to looking for delimiter
                                state = STATE_LOOKING_FOR_DELIMITER
                    
                    elif state == STATE_READING_DESCRIPTION:
                        if line:  # Non-empty line
                            # If the description is already set from the code line, use this as explanation
                            if current_code['description']:
                                current_code['explanation'] = line
                                state = STATE_READING_EXAMPLE
                            else:
                                current_code['description'] = line
                                state = STATE_READING_EXPLANATION
                        else:
                            # Skip empty lines
                            pass
                    
                    elif state == STATE_READING_EXPLANATION:
                        if line:  # Non-empty line
                            current_code['explanation'] = line
                            state = STATE_READING_EXAMPLE
                        else:
                            # If there's no explanation, move to example
                            state = STATE_READING_EXAMPLE
                    
                    elif state == STATE_READING_EXAMPLE:
                        if line:  # Non-empty line
                            current_code['example'] = line
                            
                            # Create a unique key for code/type combination
                            unique_key = f"{current_code['code']}|full"
                            
                            # Add the code if it's not a duplicate
                            if unique_key not in unique_codes:
                                unique_codes[unique_key] = True
                                full_codes.append(current_code)
                                logger.debug(f"Added full code: {current_code['code']}")
                            
                            # Reset state to look for the next delimiter
                            state = STATE_LOOKING_FOR_DELIMITER
                        else:
                            # If we've reached the end of the entry without an example
                            # Add the code entry anyway if we have at least a code and description
                            if current_code['code'] and (current_code['description'] or current_code['explanation']):
                                unique_key = f"{current_code['code']}|full"
                                if unique_key not in unique_codes:
                                    unique_codes[unique_key] = True
                                    full_codes.append(current_code)
                                    logger.debug(f"Added full code without example: {current_code['code']}")
                            
                            # Reset state to look for the next delimiter
                            state = STATE_LOOKING_FOR_DELIMITER
                
                logger.info(f"Parsed {len(full_codes)} full codes")
            
            # Combine both code types
            morphology_data = brief_codes + full_codes
            logger.info(f"Total morphology codes parsed: {len(morphology_data)}")
            
    except Exception as e:
        logger.error(f"Error parsing morphology file: {e}")
        raise
    
    return morphology_data

def load_morphology_data(db_connection, morphology_data):
    """
    Load the parsed morphology data into the database.
    """
    try:
        cur = db_connection.cursor()
        
        # Check if there are existing entries
        cur.execute("SELECT COUNT(*) FROM bible.greek_morphology_codes")
        count = cur.fetchone()[0]
        
        if count > 0:
            logger.info(f"Found {count} existing Greek morphology codes. Truncating table to update with new data.")
            # Truncate the table to replace with new data
            cur.execute("TRUNCATE TABLE bible.greek_morphology_codes RESTART IDENTITY CASCADE")
            db_connection.commit()
        
        # Insert the new morphology data
        inserted_count = 0
        for item in morphology_data:
            cur.execute("""
                INSERT INTO bible.greek_morphology_codes
                (code, code_type, description, explanation, example)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                item['code'],
                item['code_type'],
                item['description'],
                item['explanation'],
                item['example']
            ))
            inserted_count += 1
        
        db_connection.commit()
        logger.info(f"Inserted {inserted_count} Greek morphology codes")
        
    except Exception as e:
        db_connection.rollback()
        logger.error(f"Error loading Greek morphology data: {e}")
        raise e

def main(file_path):
    """Main ETL process for Greek morphology codes."""
    logger.info(f"Starting Greek morphology ETL process with file: {file_path}")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Get database connection
        db_connection = get_db_connection()
        
        # Create the tables if they don't exist
        create_tables(db_connection)
        
        # Parse the morphology file
        morphology_data = parse_morphology_file(file_path)
        
        # Load the data into the database
        load_morphology_data(db_connection, morphology_data)
        
        logger.info("Greek morphology ETL process completed successfully")
        
    except Exception as e:
        logger.error(f"Error in Greek morphology ETL process: {e}")
        sys.exit(1)
    finally:
        if 'db_connection' in locals() and db_connection is not None:
            db_connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Greek morphology codes from TEGMC file')
    parser.add_argument('--file', type=str, required=True, help='Path to the TEGMC file')
    args = parser.parse_args()
    
    main(args.file) 