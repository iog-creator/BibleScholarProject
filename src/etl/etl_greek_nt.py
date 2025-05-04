#!/usr/bin/env python3
"""
ETL script for processing Greek New Testament tagged Bible text from TAGNT files.
This script extracts and loads Greek text, verses, and word-level tagging
with morphology and Strong's number references.
"""

import os
import sys
import logging
import argparse
import re
import codecs
from datetime import datetime
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from src.utils.file_utils import append_dspy_training_example

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.connection import get_db_connection

# Configure logging with proper Unicode handling
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_greek_nt.log', encoding='utf-8'),
        # Don't use StreamHandler for console output with Greek chars in Windows
        # logging.StreamHandler()
    ]
)
logger = logging.getLogger('etl_greek_nt')

def create_tables(conn):
    """Create the necessary tables for Greek NT text if they don't exist."""
    try:
        with conn.cursor() as cur:
            # Ensure the schema exists
            cur.execute("CREATE SCHEMA IF NOT EXISTS bible")
            
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
            
            # Create table for Greek NT words
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bible.greek_nt_words (
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
                CREATE INDEX IF NOT EXISTS idx_greek_nt_words_reference 
                ON bible.greek_nt_words (book_name, chapter_num, verse_num)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_greek_nt_words_strongs 
                ON bible.greek_nt_words (strongs_id)
            """)
            
            conn.commit()
            logger.info("Greek NT tables created or already exist")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating tables: {e}")
        raise

def parse_line(line):
    """
    Parse a line from the TAGNT file. Each line contains tagged Greek word data.
    
    A typical line has the format:
    Ref#WordNum=WordType    GreekWord    Transliteration    Strong's    Morphology    Translation
    
    The reference can have multiple formats:
    1. Regular: Mat.1.1#01=TT
    2. With parentheses for alternate versification: Mat.15.6(15.5)#01=k
    3. With square brackets for alternate versification: Mat.17.15[17.14]#01=NKO
    4. With text type indicators
    
    Returns a tuple of (verse_ref, word_data) if successful, None otherwise.
    """
    try:
        # Split the line by tabs
        parts = line.split('\t')
        
        if len(parts) < 5:
            return None
        
        # Parse the reference part (first element)
        ref_part = parts[0].strip()
        
        # Skip header lines or lines with format descriptions
        if ref_part.startswith('Eng (Grk) Ref & Type') or ref_part.startswith('#'):
            return None
        
        # Enhanced regex to handle more versification formats:
        # - Regular verse format (Mat.1.1)
        # - Parentheses format (Mat.15.6(15.5))
        # - Square brackets format (Mat.17.15[17.14])
        # - Curly braces format (Rom.16.25{14.24})
        ref_match = re.match(r'^([1-3]?[A-Za-z]+)\.(\d+)\.(\d+)(?:[\(\[\{][^\)\]\}]*[\)\]\}])?#(\d+)', ref_part)
        
        if not ref_match:
            # Log problematic line to a dedicated file
            with open('etl_greek_nt_parsing.log', 'a', encoding='utf-8') as f:
                f.write(f"Skipping line with invalid reference format: {line}\n")
            return None
        
        book, chapter, verse, word_num = ref_match.groups()[0:4]
        verse_ref = f"{book}.{chapter}.{verse}"
        
        # Extract the word data (handle varying numbers of fields)
        greek_word = parts[1].strip() if len(parts) > 1 else ""
        transliteration = parts[2].strip() if len(parts) > 2 else ""
        strongs = parts[3].strip() if len(parts) > 3 else ""
        grammar = parts[4].strip() if len(parts) > 4 else ""
        translation = parts[5].strip() if len(parts) > 5 else ""
        
        word_data = {
            'word_num': int(word_num),
            'word_text': greek_word,
            'transliteration': transliteration,
            'strongs_id': strongs if strongs and strongs != '-' else None,
            'grammar_code': grammar if grammar and grammar != '-' else None,
            'translation': translation if translation and translation != '-' else None
        }
        
        return (verse_ref, word_data)
    except Exception as e:
        # Log to file, not console
        with open('etl_greek_nt_parsing.log', 'a', encoding='utf-8') as f:
            f.write(f"Error parsing line: {line}. Error: {e}\n")
        return None

def parse_tagnt_file(file_path):
    """
    Parse the TAGNT file to extract verses and Greek words with tagging.
    
    TAGNT format has detailed header with formatting descriptions followed by data.
    Each verse has both word-per-line and interlinear format records.
    Lines starting with "Eng (Grk) Ref & Type" contain the actual word data.
    
    Returns a dictionary with verses and words.
    """
    verses = {}
    words = []
    current_verse_ref = None
    
    # All NT book abbreviations - expanded to include all possible variants
    nt_books = {
        # Gospels
        'Mat.', 'Mar.', 'Mrk.', 'Mark.', 'Luk.', 'Luke.', 'Jhn.', 'John.',
        # Acts 
        'Act.', 'Acts.',
        # Pauline Epistles
        'Rom.', 'Romans.',
        '1Co.', '1Cor.', '2Co.', '2Cor.',
        'Gal.', 'Galatians.',
        'Eph.', 'Ephesians.',
        'Php.', 'Phil.', 'Philippians.',
        'Col.', 'Colossians.',
        '1Th.', '1Thes.', '1Thess.', '2Th.', '2Thes.', '2Thess.',
        '1Ti.', '1Tim.', '2Ti.', '2Tim.',
        'Tit.', 'Titus.', 'Phm.', 'Phlm.', 'Philemon.',
        'Heb.', 'Hebrews.',
        # General Epistles
        'Jas.', 'James.',
        '1Pe.', '1Pet.', '2Pe.', '2Pet.',
        '1Jn.', '1John.', '2Jn.', '2John.', '3Jn.', '3John.',
        'Jud.', 'Jude.',
        # Revelation
        'Rev.', 'Revelation.'
    }
    
    # Create a set for faster lookups
    nt_book_set = set(nt_books)
    
    # Setup debugging log with UTF-8 encoding
    with open('tagnt_debug.log', 'w', encoding='utf-8') as debug_log:
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'iso-8859-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    # Use codecs to handle encoding issues better
                    with codecs.open(file_path, 'r', encoding=encoding, errors='replace') as file:
                        # Read a sample to test encoding
                        sample = file.read(1000)
                        file.seek(0)
                        
                        line_count = 0
                        valid_line_count = 0
                        in_data_section = False
                        data_start_line = 0
                        
                        for line in file:
                            line_count += 1
                            line = line.strip()
                            
                            # Skip empty lines
                            if not line:
                                continue
                            
                            # Debug line type if it contains a book reference
                            for book_prefix in nt_book_set:
                                if line.startswith(book_prefix):
                                    debug_log.write(f"Line {line_count}: Found book reference: {line[:40]}...\n")
                                    break
                            
                            # Any line starting with a book reference is considered part of the data section
                            if any(line.startswith(book) for book in nt_book_set) and not in_data_section:
                                in_data_section = True
                                data_start_line = line_count
                                debug_log.write(f"Line {line_count}: Found data section marker: {line[:40]}...\n")
                            
                            # Only process lines that start with a book reference
                            if not any(line.startswith(book) for book in nt_book_set):
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
                                        'translation_source': 'TAGNT',
                                        'words': []
                                    }
                                
                                # Add the word data to both collections
                                word_data['book_name'] = verses[verse_ref]['book_name']
                                word_data['chapter_num'] = verses[verse_ref]['chapter_num']
                                word_data['verse_num'] = verses[verse_ref]['verse_num']
                                
                                verses[verse_ref]['words'].append(word_data)
                                words.append(word_data)
                                
                                # Update the verse text by appending the Greek word
                                if verses[verse_ref]['verse_text']:
                                    verses[verse_ref]['verse_text'] += ' ' + word_data['word_text']
                                else:
                                    verses[verse_ref]['verse_text'] = word_data['word_text']
                            else:
                                # If parse_line returns None for a line that looks like it should be valid,
                                # log it for debugging
                                if any(line.startswith(book) for book in nt_book_set):
                                    debug_log.write(f"Line {line_count}: Failed to parse valid-looking line: {line[:50]}...\n")
                            
                        logger.info(f"Processed {line_count} lines from file with {valid_line_count} valid lines")
                        logger.info(f"Data section started at line {data_start_line}")
                        
                        if valid_line_count > 0:
                            break  # If we got here without exception and found data, we found the right encoding
                except UnicodeDecodeError:
                    logger.warning(f"Encoding {encoding} failed, trying next encoding")
                    continue  # Try the next encoding
                except Exception as e:
                    logger.error(f"Error reading file with encoding {encoding}: {e}")
                    raise
                    
            if not verses:
                logger.error(f"Failed to parse any verses from {file_path}")
            
            logger.info(f"Parsed {len(verses)} verses and {len(words)} Greek words from TAGNT file")
            return {'verses': verses, 'words': words}
            
        except Exception as e:
            logger.error(f"Error parsing TAGNT file: {e}")
            raise

def load_greek_nt_data(db_conn, data):
    """
    Load Greek NT data into the database.
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
        
        if verse_values:
            logger.info(f"Executing SQL for verse insertion with {len(verse_values)} verses")
            
            # Process each verse separately with individual INSERT or UPDATE operations
            for verse in verse_values:
                book_name, chapter_num, verse_num, verse_text, translation_source = verse
                
                # Check if verse exists
                cursor.execute("""
                    SELECT id FROM bible.verses 
                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s AND translation_source = %s
                """, (book_name, chapter_num, verse_num, translation_source))
                
                result = cursor.fetchone()
                
                if result:
                    # Update existing verse
                    cursor.execute("""
                        UPDATE bible.verses 
                        SET verse_text = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE book_name = %s AND chapter_num = %s AND verse_num = %s AND translation_source = %s
                    """, (verse_text, book_name, chapter_num, verse_num, translation_source))
                else:
                    # Insert new verse
                    cursor.execute("""
                        INSERT INTO bible.verses 
                        (book_name, chapter_num, verse_num, verse_text, translation_source)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (book_name, chapter_num, verse_num, verse_text, translation_source))
        
        # Get valid Strong's IDs from the greek_entries table
        cursor.execute("SELECT strongs_id FROM bible.greek_entries")
        valid_strongs_ids = set(row[0] for row in cursor.fetchall())
        logger.info(f"Found {len(valid_strongs_ids)} valid Strong's IDs in greek_entries table")
        
        # Handle possible duplicate word references by keeping only the last occurrence
        # Use a dictionary keyed by (book_name, chapter_num, verse_num, word_num)
        unique_words = {}
        for word in data['words']:
            key = (word['book_name'], word['chapter_num'], word['verse_num'], word['word_num'])
            # The last occurrence will overwrite any previous ones
            unique_words[key] = word
        
        logger.info(f"Reduced {len(data['words'])} words to {len(unique_words)} unique words after de-duplication")
        
        # Process each unique word
        word_count = 0
        strong_pattern = re.compile(r'G\d+[A-Z]?')  # Pattern to extract basic Strong's ID
        
        for word_key, word in unique_words.items():
            # Extract a valid Strong's ID if possible, otherwise set to NULL
            strongs_id = None
            if word['strongs_id']:
                # Try to extract a basic Strong's ID (e.g., G1234A from composite values)
                match = strong_pattern.search(word['strongs_id'])
                if match:
                    extracted_id = match.group(0)
                    if extracted_id in valid_strongs_ids:
                        strongs_id = extracted_id
                    else:
                        # Try without potential suffix
                        base_id = re.match(r'(G\d+)', extracted_id)
                        if base_id and base_id.group(1) in valid_strongs_ids:
                            strongs_id = base_id.group(1)
            
            # Truncate values that might exceed column length
            grammar_code = word['grammar_code']
            if grammar_code and len(grammar_code) > 20:
                grammar_code = grammar_code[:20]
            
            # Check if word exists
            cursor.execute("""
                SELECT id FROM bible.greek_nt_words 
                WHERE book_name = %s AND chapter_num = %s AND verse_num = %s AND word_num = %s
            """, (word['book_name'], word['chapter_num'], word['verse_num'], word['word_num']))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing word
                cursor.execute("""
                    UPDATE bible.greek_nt_words 
                    SET 
                        word_text = %s,
                        strongs_id = %s,
                        grammar_code = %s,
                        word_transliteration = %s,
                        translation = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s AND word_num = %s
                """, (
                    word['word_text'],
                    strongs_id,
                    grammar_code,
                    word['transliteration'],
                    word['translation'],
                    word['book_name'],
                    word['chapter_num'],
                    word['verse_num'],
                    word['word_num']
                ))
            else:
                # Insert new word
                cursor.execute("""
                    INSERT INTO bible.greek_nt_words 
                    (book_name, chapter_num, verse_num, word_num, word_text, strongs_id, grammar_code, word_transliteration, translation)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    word['book_name'],
                    word['chapter_num'],
                    word['verse_num'],
                    word['word_num'],
                    word['word_text'],
                    strongs_id,
                    grammar_code,
                    word['transliteration'],
                    word['translation']
                ))
            
            word_count += 1
            
            # Commit in batches to avoid long-running transactions
            if word_count % 1000 == 0:
                db_conn.commit()
                logger.info(f"Processed {word_count} of {len(unique_words)} words...")
            
            # Append training example
            context = f"{word['book_name']} {word['chapter_num']}:{word['verse_num']} {word['word_text']}"
            labels = {
                'strongs_id': word['strongs_id'],
                'lemma': word['word_text'],
                'morphology': word['grammar_code'],
            }
            metadata = {'verse_ref': word['book_name'] + '.' + str(word['chapter_num']) + '.' + str(word['verse_num']), 'word_num': word['word_num']}
            append_dspy_training_example('data/processed/dspy_training_data/greek_nt_tagging.jsonl', context, labels, metadata)
        
        # Final commit
        db_conn.commit()
        logger.info(f"Successfully loaded {len(data['verses'])} verses and {word_count} words into the database")
    except Exception as e:
        db_conn.rollback()
        logger.error(f"Error loading Greek NT data: {e}")
        raise

def main(file_paths):
    """Main ETL process for Greek NT text."""
    logger.info(f"Starting Greek NT ETL process with files: {', '.join(file_paths)}")
    
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
            
            # Parse the TAGNT file
            parsed_data = parse_tagnt_file(file_path)
            
            # Load data into database
            load_greek_nt_data(conn, parsed_data)
            
            logger.info(f"Completed processing file: {file_path}")
        
        logger.info("Greek NT ETL process completed successfully")
    
    except Exception as e:
        logger.error(f"Error in Greek NT ETL process: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process Greek NT tagged texts')
    parser.add_argument('--files', nargs='+', required=True, help='Paths to TAGNT files')
    args = parser.parse_args()
    
    main(args.files) 