#!/usr/bin/env python3
"""
ETL script for processing Hebrew Old Testament tagged Bible text from TAHOT files.
This script extracts and loads Hebrew text, verses, and word-level tagging
with morphology and Strong's number references.

Note on Strong's ID handling:
- Hebrew Strong's IDs are embedded in grammar_code field in format {HNNNN} or {HNNNNx}
- This script extracts them during processing but keeps the original grammar_code intact
- A post-processing step implemented in fix_hebrew_strongs_ids.py is used to:
  1. Extract Strong's IDs from grammar_code to strongs_id field for consistency with Greek
  2. Handle extended Strong's IDs (with letter suffixes) properly
  3. Map to appropriate lexicon entries
  4. Preserve special codes (H9xxx) and hybrid codes
- See docs/hebrew_strongs_documentation.md for detailed information
"""

import os
import sys
import logging
import argparse
import re
from datetime import datetime
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from src.utils.file_utils import append_dspy_training_example

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.connection import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_hebrew_ot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('etl_hebrew_ot')

def create_tables(conn):
    """Create the necessary tables for Hebrew OT text if they don't exist."""
    try:
        with conn.cursor() as cur:
            # Ensure the verses table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bible.verses (
                    id SERIAL PRIMARY KEY,
                    book_name TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    verse_num INTEGER NOT NULL,
                    verse_text TEXT NOT NULL,
                    translation_source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (book_name, chapter_num, verse_num, translation_source)
                )
            """)
            
            # Create table for Hebrew OT words (similar to greek_nt_words)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bible.hebrew_ot_words (
                    id SERIAL PRIMARY KEY,
                    book_name TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    verse_num INTEGER NOT NULL,
                    word_num INTEGER NOT NULL,
                    word_text TEXT NOT NULL,
                    strongs_id TEXT,
                    grammar_code TEXT,
                    word_transliteration TEXT,
                    translation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (book_name, chapter_num, verse_num, word_num)
                )
            """)
            
            # Create verse/word linking table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bible.verse_word_links (
                    id SERIAL PRIMARY KEY,
                    verse_id INTEGER NOT NULL REFERENCES bible.verses(id),
                    word_id INTEGER NOT NULL,
                    word_type TEXT NOT NULL, -- 'hebrew' or 'greek'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (verse_id, word_id, word_type)
                )
            """)
            
            # Create indexes for efficient queries
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_verses_reference 
                ON bible.verses (book_name, chapter_num, verse_num)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_hebrew_ot_words_reference 
                ON bible.hebrew_ot_words (book_name, chapter_num, verse_num)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_hebrew_ot_words_strongs 
                ON bible.hebrew_ot_words (strongs_id)
            """)
            
            conn.commit()
            logger.info("Hebrew OT tables created or already exist")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating tables: {e}")
        raise

def parse_line(line):
    """
    Parse a line from the TAHOT file. Each line contains tagged Hebrew word data.
    
    A typical line has the format:
    Ref#WordNum=WordType    HebrewWord    Transliteration    Strong's    Morphology    Translation
    
    The reference can have multiple formats as described in the file header:
    1. Regular: Gen.1.1#01=L
    2. With parentheses for alternate versification: Deu.29.1(28.69)#01=L
    3. With text type indicators: L (Leningrad), Q (Qere), K (Ketiv), R (Restored), X (LXX)
    4. With variant indicators in brackets: Q(K), L(abh), etc.
    
    Returns a tuple of (verse_ref, word_data) if successful, None otherwise.
    
    Notes on Strong's ID handling:
    - The Strong's ID field often doesn't contain the actual Strong's ID
    - Instead, the Strong's ID is embedded in the grammar_code field like {@H1234 HN-m}
    - We extract this during ETL and store it in strongs_id field for consistency with Greek
    - Both the original grammar_code and extracted strongs_id are preserved
    """
    try:
        # Split the line by tabs
        parts = line.split('\t')
        
        if len(parts) < 5:
            return None
        
        # Parse the reference part (first element)
        ref_part = parts[0].strip()
        
        # Skip header lines or lines with format descriptions
        if ref_part.startswith('Eng (Heb) Ref & Type') or ref_part.startswith('#'):
            return None
        
        # Complex regex to handle all reference formats:
        # - Book.Chapter.Verse with optional parenthesized alternate versification
        # - Word number after # 
        # - Optional text type (L, Q, K, R, X) after =
        # - Optional variant indicators in parentheses
        ref_match = re.match(r'^([1-3]?[A-Za-z]+)\.(\d+)\.(\d+)(?:\([^)]*\))?#(\d+)(?:=([A-Za-z]+))?(?:\([^)]*\))?$', ref_part)
        
        if not ref_match:
            return None
        
        book, chapter, verse, word_num = ref_match.groups()[0:4]
        verse_ref = f"{book}.{chapter}.{verse}"
        
        # Extract the word data (handle varying numbers of fields)
        hebrew_word = parts[1].strip() if len(parts) > 1 else ""
        transliteration = parts[2].strip() if len(parts) > 2 else ""
        strongs = parts[3].strip() if len(parts) > 3 else ""
        grammar = parts[4].strip() if len(parts) > 4 else ""
        translation = parts[5].strip() if len(parts) > 5 else ""
        
        # Extract strongs_id from grammar_code if it exists in the format {HNNNN}
        # This is a preliminary extraction - the final extraction is done in fix_hebrew_strongs_ids.py
        extracted_strongs_id = None
        if grammar and '{H' in grammar:
            match = re.search(r'\{(H\d+[a-zA-Z]?)\}', grammar)
            if match:
                extracted_strongs_id = match.group(1)
        
        word_data = {
            'word_num': int(word_num),
            'word_text': hebrew_word,
            'transliteration': transliteration,
            # Use the extracted Strong's ID if available, otherwise use the provided one
            # Note: Many grammar_code values contain the actual Strong's ID in format {HNNNN}
            'strongs_id': extracted_strongs_id if extracted_strongs_id else (strongs if strongs and strongs != '-' else None),
            'grammar_code': grammar if grammar and grammar != '-' else None,
            'translation': translation if translation and translation != '-' else None
        }
        
        return (verse_ref, word_data)
    except Exception as e:
        logger.warning(f"Error parsing line: {line}. Error: {e}")
        return None

def parse_tahot_file(file_path):
    """
    Parse the TAHOT file to extract verses and Hebrew words with tagging.
    
    TAHOT format has detailed header with formatting descriptions followed by data.
    Each verse has both word-per-line and interlinear format records.
    Lines starting with "Eng (Heb) Ref & Type" contain the actual word data.
    
    Returns a dictionary with verses and words.
    """
    verses = {}
    words = []
    current_verse_ref = None
    
    try:
        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    # Read a sample to test encoding
                    sample = file.read(1000)
                    file.seek(0)
                    
                    line_count = 0
                    valid_line_count = 0
                    in_data_section = False
                    
                    for line in file:
                        line_count += 1
                        line = line.strip()
                        
                        # Skip empty lines and comments
                        if not line:
                            continue
                            
                        # Look for data section markers
                        if line.startswith('Eng (Heb) Ref & Type'):
                            in_data_section = True
                            continue
                            
                        # Skip lines until we reach the data section
                        if not in_data_section and not line.startswith('Gen.1.'):
                            continue
                            
                        # Also skip lines starting with # (commentary/heading lines)
                        if line.startswith('#'):
                            continue
                            
                        # Try to parse the line
                        result = parse_line(line)
                        
                        if result:
                            valid_line_count += 1
                            verse_ref, word_data = result
                            
                            # If this is a new verse, initialize it
                            if verse_ref not in verses:
                                parts = verse_ref.split('.')
                                book_name = parts[0]
                                chapter_num = int(parts[1])
                                verse_num = int(parts[2])
                                
                                verses[verse_ref] = {
                                    'book_name': book_name,
                                    'chapter_num': chapter_num,
                                    'verse_num': verse_num,
                                    'verse_text': '',
                                    'translation_source': 'TAHOT',
                                    'words': []
                                }
                            
                            # Add the word data to both collections
                            word_data['book_name'] = verses[verse_ref]['book_name']
                            word_data['chapter_num'] = verses[verse_ref]['chapter_num']
                            word_data['verse_num'] = verses[verse_ref]['verse_num']
                            
                            verses[verse_ref]['words'].append(word_data)
                            words.append(word_data)
                            
                            # Update the verse text by appending the Hebrew word
                            if verses[verse_ref]['verse_text']:
                                verses[verse_ref]['verse_text'] += ' ' + word_data['word_text']
                            else:
                                verses[verse_ref]['verse_text'] = word_data['word_text']
                        elif line.startswith(('Gen.', 'Exo.', 'Lev.', 'Num.', 'Deu.')):
                            logger.warning(f"Skipping line with invalid reference format: {line}")
                    
                    logger.info(f"Processed {line_count} lines from file with {valid_line_count} valid lines")
                    break  # If we got here without exception, we found the right encoding
            except UnicodeDecodeError:
                continue  # Try the next encoding
            except Exception as e:
                logger.error(f"Error reading file with encoding {encoding}: {e}")
                raise
                
        if not verses:
            logger.error(f"Failed to parse any verses from {file_path}")
        
        logger.info(f"Parsed {len(verses)} verses and {len(words)} Hebrew words from TAHOT file")
        return {'verses': verses, 'words': words}
        
    except Exception as e:
        logger.error(f"Error parsing TAHOT file: {e}")
        raise

def load_hebrew_ot_data(db_conn, data):
    """
    Load Hebrew OT data into the database.
    """
    try:
        cursor = db_conn.cursor()
        
        # Insert verses
        verse_values = []
        for verse_ref, verse_data in data['verses'].items():
            verse_values.append((
                verse_data['book_name'],
                verse_data['chapter_num'],
                verse_data['verse_num'],
                verse_data['verse_text'],
                verse_data['translation_source']
            ))
        
        # Execute the insert with explicit ON CONFLICT clause matching our constraint
        logger.info(f"Executing SQL for verse insertion with {len(verse_values)} verses")
        execute_values(
            cursor,
            """
            INSERT INTO bible.verses (book_name, chapter_num, verse_num, verse_text, translation_source)
            VALUES %s
            ON CONFLICT (book_name, chapter_num, verse_num) 
            DO UPDATE SET verse_text = EXCLUDED.verse_text
            """,
            verse_values
        )
        
        # Get valid Strong's IDs from the hebrew_entries table
        cursor.execute("SELECT strongs_id FROM bible.hebrew_entries")
        valid_strongs_ids = set(row[0] for row in cursor.fetchall())
        logger.info(f"Found {len(valid_strongs_ids)} valid Strong's IDs in hebrew_entries table")
        
        # Handle possible duplicate word references by keeping only the last occurrence
        # Use a dictionary keyed by (book_name, chapter_num, verse_num, word_num)
        unique_words = {}
        for word in data['words']:
            key = (word['book_name'], word['chapter_num'], word['verse_num'], word['word_num'])
            # The last occurrence will overwrite any previous ones
            unique_words[key] = word
        
        logger.info(f"Reduced {len(data['words'])} words to {len(unique_words)} unique words after de-duplication")
        
        # Process each unique word
        word_values = []
        strong_pattern = re.compile(r'H\d+[A-Z]?')  # Pattern to extract basic Strong's ID
        
        for word_key, word in unique_words.items():
            # Extract a valid Strong's ID if possible, otherwise set to NULL
            strongs_id = None
            
            # First check if a Strong's ID is directly available
            if word['strongs_id']:
                # Try to extract a basic Strong's ID (e.g., H1234A from composite values)
                match = strong_pattern.search(word['strongs_id'])
                if match:
                    extracted_id = match.group(0)
                    if extracted_id in valid_strongs_ids:
                        strongs_id = extracted_id
                    else:
                        # Try without potential suffix
                        base_id = re.match(r'(H\d+)', extracted_id)
                        if base_id and base_id.group(1) in valid_strongs_ids:
                            strongs_id = base_id.group(1)
            
            # If no Strong's ID found directly, try to extract from grammar_code
            if not strongs_id and word['grammar_code']:
                # Check for patterns like {H1234} or {H1234A}
                grammar_strong_match = re.search(r'\{(H\d+[A-Za-z]?)\}', word['grammar_code'])
                if grammar_strong_match:
                    grammar_strongs_id = grammar_strong_match.group(1)
                    
                    # Try exact match first
                    if grammar_strongs_id in valid_strongs_ids:
                        strongs_id = grammar_strongs_id
                    else:
                        # Try case-insensitive match
                        grammar_strongs_id_lower = grammar_strongs_id.lower()
                        for valid_id in valid_strongs_ids:
                            if valid_id.lower() == grammar_strongs_id_lower:
                                strongs_id = valid_id
                                break
                                
                        # If still not found, try base ID without extension
                        if not strongs_id:
                            # Strip any letter suffix (like "A" from "H1234A")
                            base_id = re.match(r'(H\d+)[A-Za-z]?', grammar_strongs_id)
                            if base_id and base_id.group(1) in valid_strongs_ids:
                                strongs_id = base_id.group(1)
                            else:
                                # Use the extracted ID but note it may not be in the lexicon
                                logger.warning(f"Strong's ID {grammar_strongs_id} from grammar_code not found in lexicon")
                                # Default to just using the ID without any letter suffix
                                if base_id:
                                    strongs_id = base_id.group(1)
            
            # Truncate values that might exceed column length
            grammar_code = word['grammar_code']
            if grammar_code and len(grammar_code) > 20:
                grammar_code = grammar_code[:20]
            
            # Make sure transliteration is mapped correctly
            word_values.append((
                word['book_name'],
                word['chapter_num'],
                word['verse_num'],
                word['word_num'],
                word['word_text'],
                strongs_id,  # Use the extracted and validated Strong's ID or None
                grammar_code,
                word['transliteration'],  # Will be inserted into word_transliteration column
                word['translation']
            ))
        
        # Debug the SQL before executing
        logger.info(f"Executing SQL for word insertion with {len(word_values)} words")
        
        # Execute the insert with explicit column mapping
        execute_values(
            cursor,
            """
            INSERT INTO bible.hebrew_ot_words 
            (book_name, chapter_num, verse_num, word_num, word_text, strongs_id, grammar_code, word_transliteration, translation)
            VALUES %s
            ON CONFLICT (book_name, chapter_num, verse_num, word_num)
            DO UPDATE SET 
                word_text = EXCLUDED.word_text,
                strongs_id = EXCLUDED.strongs_id,
                grammar_code = EXCLUDED.grammar_code,
                word_transliteration = EXCLUDED.word_transliteration,
                translation = EXCLUDED.translation
            """,
            word_values
        )
        
        db_conn.commit()
        logger.info(f"Successfully loaded {len(data['verses'])} verses and {len(word_values)} words into the database")
    except Exception as e:
        db_conn.rollback()
        logger.error(f"Error loading Hebrew OT data: {e}")
        raise

def main(file_paths):
    """Main ETL process for Hebrew OT text."""
    logger.info(f"Starting Hebrew OT ETL process with files: {', '.join(file_paths)}")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return
        
        # Create tables
        create_tables(conn)
        
        # Process each file
        for file_path in file_paths:
            logger.info(f"Processing file: {file_path}")
            
            # Parse the TAHOT file
            parsed_data = parse_tahot_file(file_path)
            
            # Load data into database
            load_hebrew_ot_data(conn, parsed_data)
            
            logger.info(f"Completed processing file: {file_path}")
        
        logger.info("Hebrew OT ETL process completed successfully")
    
    except Exception as e:
        logger.error(f"Error in Hebrew OT ETL process: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process Hebrew OT tagged texts')
    parser.add_argument('--files', nargs='+', required=True, help='Paths to TAHOT files')
    args = parser.parse_args()
    
    main(args.files) 