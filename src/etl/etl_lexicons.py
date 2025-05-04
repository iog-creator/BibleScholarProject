#!/usr/bin/env python3
"""
ETL script for STEPBible lexicons.
This script parses the TBESH (Hebrew) and TBESG (Greek) lexicon files
and loads them into the bible.hebrew_entries and bible.greek_entries tables.
"""

import os
import re
import logging
import argparse
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
from src.utils.file_utils import append_dspy_training_example

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_lexicons.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('etl_lexicons')

# Load environment variables
load_dotenv()

# Database connection
def get_db_connection():
    """
    Create and return a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'bible_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
        conn.autocommit = False
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def parse_hebrew_lexicon(file_path):
    """
    Parse the TBESH (Hebrew) lexicon file and extract lexicon entries.
    
    Args:
        file_path: Path to the TBESH lexicon file
        
    Returns:
        List of dictionaries containing Hebrew lexicon entries
    """
    entries = []
    header_passed = False
    entry_pattern = re.compile(r'^(H\d+)\s+(.*?)\s*=\s*(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)$', re.DOTALL)
    
    try:
        logger.debug(f"Opening Hebrew lexicon file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            # Print first few lines for debugging
            first_lines = [next(file) for _ in range(50)]
            logger.debug(f"First few lines of the file:\n{''.join(first_lines)}")
            file.seek(0)  # Reset file pointer
            
            for line_num, line in enumerate(file, 1):
                # Skip header lines
                if not header_passed:
                    if line.strip() == "" and line_num > 30:
                        header_passed = True
                        logger.debug(f"Header passed at line {line_num}")
                    continue
                
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Debug: print processed lines
                if line_num % 1000 == 0 or line_num < 50:
                    logger.debug(f"Processing line {line_num}: {line.strip()}")
                
                # Parse the tab-separated fields
                parts = line.strip().split('\t')
                if len(parts) < 5:  # Make sure we have at least the basic fields
                    logger.warning(f"Line {line_num}: Insufficient fields: {line.strip()}")
                    continue
                
                try:
                    # Extract the fields
                    strongs_id = parts[0].strip()
                    extended_strongs = parts[1].strip().split('=')[0].strip() if len(parts) > 1 else None
                    hebrew_word = parts[4].strip() if len(parts) > 4 else ""
                    transliteration = parts[5].strip() if len(parts) > 5 else ""
                    pos = parts[6].strip() if len(parts) > 6 else ""
                    gloss = parts[7].strip() if len(parts) > 7 else ""
                    definition = parts[8].strip() if len(parts) > 8 else ""
                    
                    # Only process Hebrew entries (starting with H)
                    if not strongs_id.startswith('H'):
                        logger.warning(f"Line {line_num}: Not a Hebrew entry: {strongs_id}")
                        continue
                    
                    # Create dictionary for the entry
                    entry = {
                        'strongs_id': strongs_id,
                        'extended_strongs': extended_strongs,
                        'hebrew_word': hebrew_word,
                        'transliteration': transliteration,
                        'pos': pos,
                        'gloss': gloss,
                        'definition': definition
                    }
                    
                    # Debug: print sample entries
                    if len(entries) < 5:
                        logger.debug(f"Sample Hebrew entry: {entry}")
                        
                    entries.append(entry)
                    
                    if len(entries) % 1000 == 0:
                        logger.info(f"Processed {len(entries)} Hebrew entries")
                        
                    # Append training example
                    context = line.strip()
                    labels = {
                        'lemma': hebrew_word,
                        'strongs_id': strongs_id,
                        'gloss': gloss,
                        'definition': definition,
                    }
                    metadata = {'entry_type': 'hebrew'}
                    append_dspy_training_example('data/processed/dspy_training_data/lexicon_lookup.jsonl', context, labels, metadata)
                    
                except Exception as e:
                    logger.error(f"Error parsing line {line_num}: {e}\nLine: {line.strip()}")
                    continue
                    
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        
    logger.info(f"Total Hebrew entries processed: {len(entries)}")
    return entries

def parse_greek_lexicon(file_path):
    """
    Parse the TBESG (Greek) lexicon file and extract lexicon entries.
    
    Args:
        file_path: Path to the TBESG lexicon file
        
    Returns:
        List of dictionaries containing Greek lexicon entries
    """
    entries = []
    header_passed = False
    
    try:
        logger.debug(f"Opening Greek lexicon file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            # Print first few lines for debugging
            first_lines = [next(file) for _ in range(50)]
            logger.debug(f"First few lines of the file:\n{''.join(first_lines)}")
            file.seek(0)  # Reset file pointer
            
            for line_num, line in enumerate(file, 1):
                # Skip header lines
                if not header_passed:
                    if line.strip() == "" and line_num > 30:
                        header_passed = True
                        logger.debug(f"Header passed at line {line_num}")
                    continue
                
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Debug: print processed lines
                if line_num % 1000 == 0 or line_num < 50:
                    logger.debug(f"Processing line {line_num}: {line.strip()}")
                
                # Parse the tab-separated fields
                parts = line.strip().split('\t')
                if len(parts) < 5:  # Make sure we have at least the basic fields
                    logger.warning(f"Line {line_num}: Insufficient fields: {line.strip()}")
                    continue
                
                try:
                    # Extract the fields
                    strongs_id = parts[0].strip()
                    extended_strongs = parts[1].strip().split('=')[0].strip() if len(parts) > 1 else None
                    greek_word = parts[4].strip() if len(parts) > 4 else ""
                    transliteration = parts[5].strip() if len(parts) > 5 else ""
                    pos = parts[6].strip() if len(parts) > 6 else ""
                    gloss = parts[7].strip() if len(parts) > 7 else ""
                    definition = parts[8].strip() if len(parts) > 8 else ""
                    
                    # Only process Greek entries (starting with G)
                    if not strongs_id.startswith('G'):
                        logger.warning(f"Line {line_num}: Not a Greek entry: {strongs_id}")
                        continue
                    
                    # Create dictionary for the entry
                    entry = {
                        'strongs_id': strongs_id,
                        'extended_strongs': extended_strongs,
                        'greek_word': greek_word,
                        'transliteration': transliteration,
                        'pos': pos,
                        'gloss': gloss,
                        'definition': definition
                    }
                    
                    # Debug: print sample entries
                    if len(entries) < 5:
                        logger.debug(f"Sample Greek entry: {entry}")
                    
                    entries.append(entry)
                    
                    if len(entries) % 1000 == 0:
                        logger.info(f"Processed {len(entries)} Greek entries")
                        
                    # Append training example
                    context = line.strip()
                    labels = {
                        'lemma': greek_word,
                        'strongs_id': strongs_id,
                        'gloss': gloss,
                        'definition': definition,
                    }
                    metadata = {'entry_type': 'greek'}
                    append_dspy_training_example('data/processed/dspy_training_data/lexicon_lookup.jsonl', context, labels, metadata)
                    
                except Exception as e:
                    logger.error(f"Error parsing line {line_num}: {e}\nLine: {line.strip()}")
                    continue
                    
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        
    logger.info(f"Total Greek entries processed: {len(entries)}")
    return entries

def extract_word_relationships(hebrew_entries, greek_entries):
    """
    Extract word relationships from the lexicon entries.
    
    Args:
        hebrew_entries: List of Hebrew lexicon entries
        greek_entries: List of Greek lexicon entries
        
    Returns:
        List of word relationship dictionaries
    """
    relationships = []
    
    # Process Hebrew entries
    for entry in hebrew_entries:
        strongs_id = entry['strongs_id']
        parts = entry.get('extended_strongs', '').split('=')
        
        if len(parts) > 1 and parts[1].strip():
            relationship_info = parts[1].strip()
            # Look for related words
            if relationship_info.startswith('the Hebrew of'):
                target_match = re.search(r'(G\d+)', relationship_info)
                if target_match:
                    target_id = target_match.group(1)
                    relationships.append({
                        'source_id': strongs_id,
                        'target_id': target_id,
                        'relationship_type': 'hebrew_of_greek'
                    })
    
    # Process Greek entries
    for entry in greek_entries:
        strongs_id = entry['strongs_id']
        parts = entry.get('extended_strongs', '').split('=')
        
        if len(parts) > 1 and parts[1].strip():
            relationship_info = parts[1].strip()
            # Look for related words
            if relationship_info.startswith('the Greek of'):
                target_match = re.search(r'(H\d+)', relationship_info)
                if target_match:
                    target_id = target_match.group(1)
                    relationships.append({
                        'source_id': strongs_id,
                        'target_id': target_id,
                        'relationship_type': 'greek_of_hebrew'
                    })
    
    logger.info(f"Total word relationships extracted: {len(relationships)}")
    return relationships

def load_hebrew_entries(entries, conn):
    """
    Load Hebrew lexicon entries into the database.
    
    Args:
        entries: List of Hebrew lexicon entries
        conn: Database connection
    """
    try:
        with conn.cursor() as cur:
            # Insert Hebrew entries
            query = """
            INSERT INTO bible.hebrew_entries (
                strongs_id, extended_strongs, hebrew_word, transliteration, 
                pos, gloss, definition
            ) VALUES (
                %(strongs_id)s, %(extended_strongs)s, %(hebrew_word)s, %(transliteration)s,
                %(pos)s, %(gloss)s, %(definition)s
            ) ON CONFLICT (strongs_id) DO UPDATE SET
                extended_strongs = EXCLUDED.extended_strongs,
                hebrew_word = EXCLUDED.hebrew_word,
                transliteration = EXCLUDED.transliteration,
                pos = EXCLUDED.pos,
                gloss = EXCLUDED.gloss,
                definition = EXCLUDED.definition,
                updated_at = CURRENT_TIMESTAMP
            """
            execute_batch(cur, query, entries, page_size=1000)
            
        conn.commit()
        logger.info(f"Successfully loaded {len(entries)} Hebrew entries")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading Hebrew entries: {e}")
        raise

def load_greek_entries(entries, conn):
    """
    Load Greek lexicon entries into the database.
    
    Args:
        entries: List of Greek lexicon entries
        conn: Database connection
    """
    try:
        with conn.cursor() as cur:
            # Insert Greek entries
            query = """
            INSERT INTO bible.greek_entries (
                strongs_id, extended_strongs, greek_word, transliteration, 
                pos, gloss, definition
            ) VALUES (
                %(strongs_id)s, %(extended_strongs)s, %(greek_word)s, %(transliteration)s,
                %(pos)s, %(gloss)s, %(definition)s
            ) ON CONFLICT (strongs_id) DO UPDATE SET
                extended_strongs = EXCLUDED.extended_strongs,
                greek_word = EXCLUDED.greek_word,
                transliteration = EXCLUDED.transliteration,
                pos = EXCLUDED.pos,
                gloss = EXCLUDED.gloss,
                definition = EXCLUDED.definition,
                updated_at = CURRENT_TIMESTAMP
            """
            execute_batch(cur, query, entries, page_size=1000)
            
        conn.commit()
        logger.info(f"Successfully loaded {len(entries)} Greek entries")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading Greek entries: {e}")
        raise

def load_word_relationships(relationships, conn):
    """
    Load word relationships into the database.
    
    Args:
        relationships: List of word relationship dictionaries
        conn: Database connection
    """
    try:
        with conn.cursor() as cur:
            # Insert word relationships
            query = """
            INSERT INTO bible.word_relationships (
                source_id, target_id, relationship_type
            ) VALUES (
                %(source_id)s, %(target_id)s, %(relationship_type)s
            ) ON CONFLICT ON CONSTRAINT unique_word_relationship DO UPDATE SET
                updated_at = CURRENT_TIMESTAMP
            """
            execute_batch(cur, query, relationships, page_size=1000)
            
        conn.commit()
        logger.info(f"Successfully loaded {len(relationships)} word relationships")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading word relationships: {e}")
        raise

def main():
    """
    Main function to run the ETL process.
    """
    parser = argparse.ArgumentParser(description='ETL process for STEPBible lexicon data')
    parser.add_argument('--hebrew', required=True, help='Path to the TBESH Hebrew lexicon file')
    parser.add_argument('--greek', required=True, help='Path to the TBESG Greek lexicon file')
    args = parser.parse_args()
    
    try:
        logger.info("Starting lexicon ETL process")
        
        # Verify files exist
        for file_path in [args.hebrew, args.greek]:
            if not os.path.isfile(file_path):
                logger.error(f"File not found: {file_path}")
                return 1
            logger.info(f"File exists: {file_path}")
        
        # Parse lexicon files
        logger.info(f"Parsing Hebrew lexicon from {args.hebrew}")
        hebrew_entries = parse_hebrew_lexicon(args.hebrew)
        
        logger.info(f"Parsing Greek lexicon from {args.greek}")
        greek_entries = parse_greek_lexicon(args.greek)
        
        # Extract word relationships
        logger.info("Extracting word relationships")
        relationships = extract_word_relationships(hebrew_entries, greek_entries)
        
        # Load data into the database
        conn = get_db_connection()
        try:
            logger.info("Loading Hebrew entries into the database")
            load_hebrew_entries(hebrew_entries, conn)
            
            logger.info("Loading Greek entries into the database")
            load_greek_entries(greek_entries, conn)
            
            logger.info("Loading word relationships into the database")
            load_word_relationships(relationships, conn)
            
            logger.info("Lexicon ETL process completed successfully")
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in lexicon ETL process: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main()) 
