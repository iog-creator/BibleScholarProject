#!/usr/bin/env python3
"""
ETL script for processing the TFLSJ (Translators Formatted full LSJ Bible lexicon) data.
This script extracts and loads the comprehensive LSJ Greek lexicon data into the database.
"""

import os
import sys
import logging
import argparse
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import re
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_lsj_lexicon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('etl_lsj_lexicon')

def create_tables(conn):
    """Create the necessary tables for LSJ lexicon data if they don't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bible.lsj_entries (
                id SERIAL PRIMARY KEY,
                strongs_id TEXT NOT NULL,
                greek_word TEXT NOT NULL,
                transliteration TEXT,
                gloss TEXT,
                definition TEXT,
                extended_definition TEXT,
                related_words JSONB,
                verse_references JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (strongs_id)
            )
        """)
        
        # Create indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_lsj_strongs ON bible.lsj_entries(strongs_id);
            CREATE INDEX IF NOT EXISTS idx_lsj_greek_word ON bible.lsj_entries(greek_word);
            CREATE INDEX IF NOT EXISTS idx_lsj_gloss ON bible.lsj_entries USING gin (to_tsvector('english', gloss));
            CREATE INDEX IF NOT EXISTS idx_lsj_definition ON bible.lsj_entries USING gin (to_tsvector('english', definition));
        """)
        
        conn.commit()
        logger.info("LSJ lexicon tables and indexes created or verified")

def parse_lsj_file(file_path):
    """
    Parse the TFLSJ file to extract LSJ lexicon data.
    
    Returns a list of dictionaries with the parsed data.
    """
    lexicon_data = []
    unique_strongs_ids = set()  # Track unique Strong's IDs to avoid duplicates
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Split the content by Strong's entries (typically marked by G#### at start of line)
            # This regex looks for lines starting with 'G' followed by 1 or more digits
            entries = re.split(r'\n(?=G\d+)', content)
            
            for entry in entries:
                if not entry.strip():
                    continue
                
                # Extract Strong's ID
                strongs_match = re.match(r'(G\d+[A-Za-z]*)', entry)
                if not strongs_match:
                    continue
                
                strongs_id = strongs_match.group(1)
                
                # Skip if we've already processed this Strong's ID
                if strongs_id in unique_strongs_ids:
                    logger.debug(f"Skipping duplicate Strong's ID: {strongs_id}")
                    continue
                
                # Add this Strong's ID to our tracking set
                unique_strongs_ids.add(strongs_id)
                
                # Extract Greek word - typically follows the Strong's ID
                greek_word_match = re.search(r'(G\d+[A-Za-z]*)\s+([^\s]+)', entry)
                greek_word = greek_word_match.group(2) if greek_word_match else ""
                
                # Extract transliteration
                transliteration_match = re.search(r'\(([^)]+)\)', entry)
                transliteration = transliteration_match.group(1) if transliteration_match else ""
                
                # Extract gloss - short definition
                gloss_match = re.search(r'=\s*(.+?)\n', entry)
                gloss = gloss_match.group(1) if gloss_match else ""
                
                # Extract main definition
                # This is more complex as it spans multiple lines, we'll take everything after
                # the gloss line until we hit sections like "References:" or another pattern
                lines = entry.split('\n')
                definition_lines = []
                extended_definition_lines = []
                collecting_definition = False
                collecting_extended = False
                
                for line in lines:
                    # Skip the first line with Strong's ID
                    if line.startswith(strongs_id):
                        continue
                    
                    # Skip the gloss line
                    if line.startswith('='):
                        collecting_definition = True
                        continue
                    
                    # Check for section markers
                    if re.match(r'References:|Related:|Etymology:|Usage:', line):
                        collecting_definition = False
                        collecting_extended = False
                        continue
                    
                    # Collect the definition
                    if collecting_definition and line.strip():
                        # If line starts with a number or letter+), it's part of extended definition
                        if re.match(r'^\s*(\d+[\.\)]|[a-zA-Z][\.\)])', line):
                            collecting_definition = False
                            collecting_extended = True
                            extended_definition_lines.append(line.strip())
                        else:
                            definition_lines.append(line.strip())
                    elif collecting_extended and line.strip():
                        extended_definition_lines.append(line.strip())
                
                definition = ' '.join(definition_lines).strip()
                extended_definition = ' '.join(extended_definition_lines).strip()
                
                # Extract related words
                related_words = {}
                related_section_match = re.search(r'Related:(.*?)(?=\n\S|\Z)', entry, re.DOTALL)
                if related_section_match:
                    related_text = related_section_match.group(1).strip()
                    # Parse related words - typically formatted as "G#### = word"
                    for related_match in re.finditer(r'(G\d+[A-Za-z]*)\s*=\s*([^,\n]+)', related_text):
                        related_id = related_match.group(1)
                        related_word = related_match.group(2).strip()
                        related_words[related_id] = related_word
                
                # Extract references
                references = {}
                refs_section_match = re.search(r'References:(.*?)(?=\n\S|\Z)', entry, re.DOTALL)
                if refs_section_match:
                    refs_text = refs_section_match.group(1).strip()
                    # Parse references - typically formatted as "Book.chapter.verse"
                    for ref_match in re.finditer(r'([A-Za-z]+\.\d+\.\d+)', refs_text):
                        ref = ref_match.group(1)
                        if ref not in references:
                            references[ref] = 1
                        else:
                            references[ref] += 1
                
                lexicon_data.append({
                    'strongs_id': strongs_id,
                    'greek_word': greek_word,
                    'transliteration': transliteration,
                    'gloss': gloss,
                    'definition': definition,
                    'extended_definition': extended_definition,
                    'related_words': json.dumps(related_words),
                    'references': json.dumps(references)
                })
                
                logger.debug(f"Processed entry for {strongs_id}: {greek_word}")
            
            logger.info(f"Parsed {len(lexicon_data)} LSJ lexicon entries")
            
    except Exception as e:
        logger.error(f"Error parsing LSJ lexicon file: {e}")
        raise
    
    return lexicon_data

def load_lexicon_data(db_connection, lexicon_data):
    """
    Load the parsed LSJ lexicon data into the database.
    """
    try:
        cur = db_connection.cursor()
        
        # Check if there are existing entries
        cur.execute("SELECT COUNT(*) FROM bible.lsj_entries")
        count = cur.fetchone()[0]
        
        if count > 0:
            logger.info(f"Found {count} existing LSJ entries. Truncating table to update with new data.")
            # Truncate the table to replace with new data
            cur.execute("TRUNCATE TABLE bible.lsj_entries RESTART IDENTITY CASCADE")
            db_connection.commit()
        
        # Insert the new lexicon data
        inserted_count = 0
        for item in lexicon_data:
            cur.execute("""
                INSERT INTO bible.lsj_entries
                (strongs_id, greek_word, transliteration, gloss, definition, 
                 extended_definition, related_words, verse_references)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                item['strongs_id'],
                item['greek_word'],
                item['transliteration'],
                item['gloss'],
                item['definition'],
                item['extended_definition'],
                item['related_words'],
                item['references']
            ))
            inserted_count += 1
            
            # Commit in batches to avoid large transactions
            if inserted_count % 500 == 0:
                db_connection.commit()
                logger.info(f"Inserted {inserted_count} LSJ entries so far")
        
        db_connection.commit()
        logger.info(f"Inserted {inserted_count} total LSJ lexicon entries")
        
    except Exception as e:
        db_connection.rollback()
        logger.error(f"Error loading LSJ lexicon data: {e}")
        raise e

def main(file_paths):
    """Main ETL process for LSJ lexicon data."""
    logger.info(f"Starting LSJ lexicon ETL process with files: {file_paths}")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Get database connection
        db_connection = get_db_connection()
        
        # Create the tables if they don't exist
        create_tables(db_connection)
        
        # Parse and load each file
        all_lexicon_data = []
        # Track processed Strong's IDs across all files
        processed_strongs_ids = set()
        
        for file_path in file_paths:
            logger.info(f"Processing file: {file_path}")
            lexicon_data = parse_lsj_file(file_path)
            
            # Filter out entries with duplicate Strong's IDs
            new_entries = []
            for entry in lexicon_data:
                strongs_id = entry['strongs_id']
                if strongs_id not in processed_strongs_ids:
                    processed_strongs_ids.add(strongs_id)
                    new_entries.append(entry)
                else:
                    logger.debug(f"Skipping duplicate Strong's ID {strongs_id} from file {file_path}")
            
            logger.info(f"Added {len(new_entries)} unique entries from {file_path}")
            all_lexicon_data.extend(new_entries)
        
        # Load the data into the database
        load_lexicon_data(db_connection, all_lexicon_data)
        
        logger.info("LSJ lexicon ETL process completed successfully")
        
    except Exception as e:
        logger.error(f"Error in LSJ lexicon ETL process: {e}")
        sys.exit(1)
    finally:
        if 'db_connection' in locals() and db_connection is not None:
            db_connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process TFLSJ (Translators Formatted full LSJ Bible lexicon) data')
    parser.add_argument('--files', type=str, nargs='+', required=True, 
                        help='Paths to the TFLSJ files (can specify multiple files)')
    args = parser.parse_args()
    
    main(args.files) 