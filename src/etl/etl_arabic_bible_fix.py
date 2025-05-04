#!/usr/bin/env python3
"""
Enhanced ETL script for processing Tagged Arabic Bible data (TTAraSVD).

This script addresses issues with the original ETL process that resulted in only 
partial loading of Arabic Bible data (44,177 words instead of expected 382,293).

The issues addressed include:
1. Database schema incompatibility (missing columns)
2. File parsing errors
3. Duplicate word handling
4. Proper processing of all book files

Usage:
python src/etl/etl_arabic_bible_fix.py
"""

import os
import sys
import logging
import argparse
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import re
import codecs
import zipfile
import tempfile
import glob
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db_connection

# Configure logging
log_dir = "logs/etl"
os.makedirs(log_dir, exist_ok=True)
log_file = f"{log_dir}/etl_arabic_bible_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('etl_arabic_bible_fix')

# Book abbreviations mapping
BOOK_ABBR_MAP = {
    # Old Testament
    'Gen': 'Genesis', 'Exo': 'Exodus', 'Lev': 'Leviticus', 'Num': 'Numbers', 'Deu': 'Deuteronomy',
    'Jos': 'Joshua', 'Jdg': 'Judges', 'Rut': 'Ruth', '1Sa': '1 Samuel', '2Sa': '2 Samuel',
    '1Ki': '1 Kings', '2Ki': '2 Kings', '1Ch': '1 Chronicles', '2Ch': '2 Chronicles',
    'Ezr': 'Ezra', 'Neh': 'Nehemiah', 'Est': 'Esther', 'Job': 'Job', 'Psa': 'Psalms',
    'Pro': 'Proverbs', 'Ecc': 'Ecclesiastes', 'Sng': 'Song of Solomon', 'Isa': 'Isaiah',
    'Jer': 'Jeremiah', 'Lam': 'Lamentations', 'Ezk': 'Ezekiel', 'Dan': 'Daniel',
    'Hos': 'Hosea', 'Jol': 'Joel', 'Amo': 'Amos', 'Oba': 'Obadiah', 'Jon': 'Jonah',
    'Mic': 'Micah', 'Nam': 'Nahum', 'Hab': 'Habakkuk', 'Zep': 'Zephaniah',
    'Hag': 'Haggai', 'Zec': 'Zechariah', 'Mal': 'Malachi',
    # New Testament
    'Mat': 'Matthew', 'Mrk': 'Mark', 'Luk': 'Luke', 'Jhn': 'John', 'Act': 'Acts',
    'Rom': 'Romans', '1Co': '1 Corinthians', '2Co': '2 Corinthians', 'Gal': 'Galatians',
    'Eph': 'Ephesians', 'Php': 'Philippians', 'Col': 'Colossians', '1Th': '1 Thessalonians',
    '2Th': '2 Thessalonians', '1Ti': '1 Timothy', '2Ti': '2 Timothy', 'Tit': 'Titus',
    'Phm': 'Philemon', 'Heb': 'Hebrews', 'Jas': 'James', '1Pe': '1 Peter', '2Pe': '2 Peter',
    '1Jn': '1 John', '2Jn': '2 John', '3Jn': '3 John', 'Jud': 'Jude', 'Rev': 'Revelation'
}

def create_tables(conn):
    """Create the necessary tables for Arabic Bible data with all required columns."""
    with conn.cursor() as cur:
        # Create table for Arabic Bible verses with correct schema
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bible.arabic_verses (
                id SERIAL PRIMARY KEY,
                book_name TEXT NOT NULL,
                chapter_num INTEGER NOT NULL,
                verse_num INTEGER NOT NULL,
                verse_text TEXT NOT NULL,
                translation_source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (book_name, chapter_num, verse_num, translation_source)
            )
        """)
        
        # Check if arabic_words table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'bible' AND table_name = 'arabic_words'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if table_exists:
            # Drop the existing table to fix schema issues
            logger.info("Dropping existing arabic_words table to fix schema")
            cur.execute("DROP TABLE IF EXISTS bible.arabic_words CASCADE")
        
        # Create the arabic_words table with all necessary columns
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bible.arabic_words (
                id SERIAL PRIMARY KEY,
                verse_id INTEGER REFERENCES bible.arabic_verses(id) ON DELETE CASCADE,
                word_position INTEGER NOT NULL,
                arabic_word TEXT NOT NULL,
                strongs_id TEXT,
                greek_word TEXT,
                hebrew_word TEXT,
                latin_word TEXT,
                transliteration TEXT,
                gloss TEXT,
                morphology TEXT,
                greek_word_position TEXT,
                lexicon TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (verse_id, word_position, arabic_word)
            )
        """)
        
        # Create necessary indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_arabic_verses_reference ON bible.arabic_verses(book_name, chapter_num, verse_num);
            CREATE INDEX IF NOT EXISTS idx_arabic_verses_book ON bible.arabic_verses(book_name);
            CREATE INDEX IF NOT EXISTS idx_arabic_words_verse_id ON bible.arabic_words(verse_id);
            CREATE INDEX IF NOT EXISTS idx_arabic_words_strongs ON bible.arabic_words(strongs_id);
        """)
        
        conn.commit()
        logger.info("Arabic Bible tables and indexes created or updated with correct schema")

def open_file_with_zip_support(file_path):
    """Open a file with zip support if it's a zip file, and provide proper encoding support."""
    try:
        # Check if the file is a zip file
        if file_path.lower().endswith('.zip'):
            logger.info(f"Processing zip file: {file_path}")
            # Create a temporary directory to extract the zip file
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Extract the files to the temporary directory
                    zip_ref.extractall(temp_dir)
                    # Get the extracted files
                    extracted_files = os.listdir(temp_dir)
                    # Assuming there's only one text file in the zip
                    for extracted_file in extracted_files:
                        if extracted_file.lower().endswith('.txt'):
                            extracted_path = os.path.join(temp_dir, extracted_file)
                            logger.info(f"Found text file in zip: {extracted_file}")
                            # Try multiple encodings
                            for encoding in ['utf-8-sig', 'utf-8', 'cp1256', 'iso-8859-6']:
                                try:
                                    with codecs.open(extracted_path, 'r', encoding=encoding, errors='replace') as file:
                                        content = file.read()
                                        logger.info(f"Successfully read file with encoding: {encoding}")
                                        return content
                                except UnicodeDecodeError:
                                    continue
            # If no text files found or reading failed, return empty string
            return ""
        else:
            # Regular text file, try multiple encodings
            for encoding in ['utf-8-sig', 'utf-8', 'cp1256', 'iso-8859-6']:
                try:
                    with codecs.open(file_path, 'r', encoding=encoding, errors='replace') as file:
                        content = file.read()
                        logger.info(f"Successfully read file with encoding: {encoding}")
                        return content
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, try a last resort with errors='replace'
            with codecs.open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                logger.warning(f"Using fallback encoding with replacement for file: {file_path}")
                return file.read()
    except Exception as e:
        logger.error(f"Error opening file {file_path}: {str(e)}")
        return ""

def parse_arabic_bible_file(file_path, is_old_testament=False):
    """
    Enhanced parsing of TTAraSVD file to extract Arabic Bible text with Strong's numbers.
    
    Args:
        file_path: Path to the TTAraSVD file
        is_old_testament: Boolean flag indicating if this is OT or NT data
        
    Returns:
        A dictionary with verse data and word data
    """
    bible_data = {
        'verses': [],
        'words': []
    }
    
    try:
        # Extract filename for better logging
        filename = os.path.basename(file_path)
        logger.info(f"Parsing file: {filename}")
        
        content = open_file_with_zip_support(file_path)
        if not content:
            logger.error(f"Empty content for file: {file_path}")
            return bible_data
            
        # Split content into lines
        lines = content.split('\n')
        
        current_book = None
        current_chapter = None
        current_verse = None
        verse_id_map = {}  # Maps verse reference to verse ID for word linkage
        
        in_verse_section = False
        current_verse_ref = None
        current_verse_text = ""
        verse_words = []
        
        line_index = 0
        
        # Debug info
        if len(lines) < 10:
            logger.warning(f"File seems too short: {file_path}, only {len(lines)} lines")
            logger.warning(f"Sample content: {lines[:5]}")
            
        while line_index < len(lines):
            line = lines[line_index].strip()
            line_index += 1
            
            # Skip empty lines
            if not line:
                continue
                
            # Skip header and lines before actual verse data
            if line.startswith("TTArabicSVD") or line.startswith("======="):
                continue
            
            # Check if this is a verse reference line (like "3Jn.1.1")
            verse_ref_match = re.match(r'^([A-Za-z0-9]{3})\.(\d+)\.(\d+)(?:\s*)?$', line)
            if verse_ref_match:
                # If we were processing a previous verse, save it
                if current_verse_ref and current_book and current_chapter and current_verse:
                    # Add verse to data
                    verse_id = len(bible_data['verses']) + 1
                    bible_data['verses'].append({
                        'book_name': current_book,
                        'chapter_num': current_chapter,
                        'verse_num': current_verse,
                        'verse_text': current_verse_text,
                        'translation_source': 'TTAraSVD'
                    })
                    
                    # Store verse ID for word linkage
                    verse_id_map[current_verse_ref] = verse_id
                    
                    # Process words for this verse
                    for word in verse_words:
                        word['verse_id'] = verse_id
                        bible_data['words'].append(word)
                
                # Parse new verse reference
                current_verse_ref = line.strip()
                book_abbr, chapter, verse = verse_ref_match.groups()
                # Convert book abbreviation to full name
                current_book = BOOK_ABBR_MAP.get(book_abbr, book_abbr)
                current_chapter = int(chapter)
                current_verse = int(verse)
                current_verse_text = ""
                verse_words = []
                
                # Next line may be "========"
                if line_index < len(lines) and "=====" in lines[line_index].strip():
                    line_index += 1
                
                in_verse_section = True
                
            # Check if this is the table header line (Ara W#, Arabic, Strongs, etc.)
            elif line.startswith("Ara W#") and in_verse_section:
                # Skip this header line
                continue
            
            # Parse word data rows
            elif in_verse_section and line and ("#" in line.split('\t')[0] if '\t' in line else False):
                columns = line.split('\t')
                if len(columns) >= 3:  # Need at least position, word and Strong's
                    try:
                        # Extract word position from first column (e.g., "#01")
                        word_pos_match = re.match(r'^#(\d+)(?:\s*-\s*#\d+)?', columns[0])
                        if word_pos_match:
                            word_pos = int(word_pos_match.group(1))
                            
                            # Extract Arabic word
                            arabic_word = columns[1].strip()
                            
                            # Extract Strong's ID
                            strongs_id = columns[2].strip() if len(columns) > 2 and columns[2].strip() else None
                            
                            # Build word record with all available data
                            word_data = {
                                'verse_id': None,  # Will be set when verse is processed
                                'word_position': word_pos,
                                'arabic_word': arabic_word,
                                'strongs_id': strongs_id
                            }
                            
                            # Add optional fields if available
                            optional_fields = [
                                (3, 'greek_word'),
                                (4, 'lexicon'),
                                (5, 'gloss'),
                                (6, 'transliteration'),
                                (7, 'morphology'),
                                (8, 'greek_word_position')
                            ]
                            
                            for idx, field_name in optional_fields:
                                if len(columns) > idx and columns[idx].strip():
                                    word_data[field_name] = columns[idx].strip()
                            
                            # Add to the current verse's words
                            verse_words.append(word_data)
                            
                            # Add words to verse text (for display purposes)
                            if current_verse_text:
                                current_verse_text += " "
                            current_verse_text += arabic_word
                    except Exception as e:
                        logger.error(f"Error parsing word data in {filename}, line {line_index}: {str(e)}")
                        logger.error(f"Line content: {line}")
            
            # Check for verse ending (next verse reference)
            if line_index < len(lines) and re.match(r'^[A-Za-z0-9]{3}\.\d+\.\d+', lines[line_index].strip()):
                in_verse_section = False
        
        # Don't forget to process the last verse
        if current_verse_ref and current_book and current_chapter and current_verse:
            verse_id = len(bible_data['verses']) + 1
            bible_data['verses'].append({
                'book_name': current_book,
                'chapter_num': current_chapter,
                'verse_num': current_verse,
                'verse_text': current_verse_text,
                'translation_source': 'TTAraSVD'
            })
            
            verse_id_map[current_verse_ref] = verse_id
            
            for word in verse_words:
                word['verse_id'] = verse_id
                bible_data['words'].append(word)
        
        logger.info(f"Parsed {len(bible_data['verses'])} verses and {len(bible_data['words'])} words from {filename}")
        
        # Additional validation
        if len(bible_data['verses']) == 0 or len(bible_data['words']) == 0:
            logger.warning(f"File parsed without extracting any data: {file_path}")
        
    except Exception as e:
        logger.error(f"Error parsing Arabic Bible file {file_path}: {str(e)}")
    
    return bible_data

def load_arabic_bible_data(db_connection, bible_data):
    """
    Load the parsed Arabic Bible data into the database with improved handling for duplicates.
    """
    try:
        cur = db_connection.cursor()
        
        # Check if there are existing entries
        cur.execute("SELECT COUNT(*) FROM bible.arabic_verses")
        existing_verse_count = cur.fetchone()[0]
        
        logger.info(f"Found {existing_verse_count} existing Arabic Bible verses.")
        
        # Create a mapping between (book, chapter, verse) and database IDs
        verse_id_map = {}
        if existing_verse_count > 0:
            cur.execute("""
                SELECT id, book_name, chapter_num, verse_num 
                FROM bible.arabic_verses
            """)
            for row in cur.fetchall():
                verse_id, book, chapter, verse = row
                verse_id_map[(book, chapter, verse)] = verse_id
        
        # Keep track of stats
        verses_inserted = 0
        verses_skipped = 0
        words_inserted = 0
        words_skipped = 0
        
        # Insert verses using ON CONFLICT DO NOTHING to avoid duplicates
        for verse in bible_data['verses']:
            verse_key = (verse['book_name'], verse['chapter_num'], verse['verse_num'])
            
            if verse_key in verse_id_map:
                # Skip insertion but store ID for word references
                verse_id = verse_id_map[verse_key]
                verses_skipped += 1
            else:
                # Insert the verse
                cur.execute("""
                    INSERT INTO bible.arabic_verses
                    (book_name, chapter_num, verse_num, verse_text, translation_source)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (book_name, chapter_num, verse_num, translation_source) DO NOTHING
                    RETURNING id
                """, (
                    verse['book_name'],
                    verse['chapter_num'],
                    verse['verse_num'],
                    verse['verse_text'],
                    verse['translation_source']
                ))
                
                result = cur.fetchone()
                if result:
                    verse_id = result[0]
                    verse_id_map[verse_key] = verse_id
                    verses_inserted += 1
                else:
                    # The verse might have been inserted in a concurrent operation
                    # Get the existing ID
                    cur.execute("""
                        SELECT id FROM bible.arabic_verses 
                        WHERE book_name = %s AND chapter_num = %s AND verse_num = %s AND translation_source = %s
                    """, (verse['book_name'], verse['chapter_num'], verse['verse_num'], verse['translation_source']))
                    verse_id = cur.fetchone()[0]
                    verse_id_map[verse_key] = verse_id
                    verses_skipped += 1
            
            # Commit every 500 verses
            if (verses_inserted + verses_skipped) % 500 == 0:
                db_connection.commit()
                logger.info(f"Processed {verses_inserted + verses_skipped} verses so far (inserted: {verses_inserted}, skipped: {verses_skipped})")
        
        # Commit remaining verses
        db_connection.commit()
        logger.info(f"Inserted {verses_inserted} verses, skipped {verses_skipped} existing verses")
        
        # Prepare for batch inserts of words
        BATCH_SIZE = 1000
        word_batch = []
        
        # Process words
        for i, word in enumerate(bible_data['words']):
            # Get the verse ID for this word
            verse_id = None
            verse_info = next((v for v in bible_data['verses'] if v.get('id', 0) == word['verse_id']), None)
            
            if verse_info:
                verse_key = (verse_info['book_name'], verse_info['chapter_num'], verse_info['verse_num'])
                verse_id = verse_id_map.get(verse_key)
            
            if not verse_id:
                # Try to find the verse ID based on the original verse_id
                original_index = word['verse_id'] - 1  # Convert to 0-indexed
                if 0 <= original_index < len(bible_data['verses']):
                    verse_info = bible_data['verses'][original_index]
                    verse_key = (verse_info['book_name'], verse_info['chapter_num'], verse_info['verse_num'])
                    verse_id = verse_id_map.get(verse_key)
            
            if not verse_id:
                logger.warning(f"Could not find verse ID for word: {word}")
                continue
            
            # Prepare the parameters for this word
            params = {
                'verse_id': verse_id,
                'word_position': word['word_position'],
                'arabic_word': word['arabic_word'],
                'strongs_id': word.get('strongs_id')
            }
            
            # Add optional fields if they exist
            optional_fields = [
                'greek_word', 'hebrew_word', 'latin_word', 'transliteration', 
                'gloss', 'morphology', 'greek_word_position', 'lexicon'
            ]
            
            for field in optional_fields:
                if field in word and word[field]:
                    params[field] = word[field]
            
            # Add to batch
            word_batch.append(params)
            
            # Process batch if it reaches the batch size
            if len(word_batch) >= BATCH_SIZE:
                inserted, skipped = insert_word_batch(cur, word_batch)
                words_inserted += inserted
                words_skipped += skipped
                word_batch = []  # Clear batch
                
                # Commit batch
                db_connection.commit()
                logger.info(f"Processed {words_inserted + words_skipped} words so far (inserted: {words_inserted}, skipped: {words_skipped})")
        
        # Process any remaining words in the batch
        if word_batch:
            inserted, skipped = insert_word_batch(cur, word_batch)
            words_inserted += inserted
            words_skipped += skipped
            db_connection.commit()
        
        logger.info(f"Inserted {words_inserted} words, skipped {words_skipped} existing words")
        
    except Exception as e:
        db_connection.rollback()
        logger.error(f"Error loading Arabic Bible data: {str(e)}")
        raise

def insert_word_batch(cursor, word_batch):
    """
    Insert a batch of words with proper handling of duplicates.
    Returns (inserted_count, skipped_count)
    """
    inserted = 0
    skipped = 0
    
    for word in word_batch:
        # Dynamically build columns and values for the INSERT
        columns = []
        values = []
        placeholders = []
        
        for i, (key, value) in enumerate(word.items()):
            columns.append(key)
            values.append(value)
            placeholders.append(f"%s")
        
        # Build the SQL statement with ON CONFLICT
        sql = f"""
            INSERT INTO bible.arabic_words
            ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            ON CONFLICT (verse_id, word_position, arabic_word) DO NOTHING
        """
        
        try:
            cursor.execute(sql, values)
            if cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            logger.warning(f"Error inserting word: {str(e)}")
            logger.warning(f"Word data: {word}")
            skipped += 1
    
    return inserted, skipped

def process_directory(db_connection, directory_path):
    """
    Process all Arabic Bible files in a directory.
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        logger.error(f"Directory not found: {directory_path}")
        return
    
    # Find all text files in the directory
    files = glob.glob(os.path.join(directory_path, "*.txt"))
    
    if not files:
        logger.error(f"No text files found in directory: {directory_path}")
        return
    
    logger.info(f"Found {len(files)} files in directory: {directory_path}")
    
    # Sort files to ensure consistent processing order
    files.sort()
    
    # Process each file
    all_data = {
        'verses': [],
        'words': []
    }
    
    for file_path in files:
        # Determine if this is OT or NT
        filename = os.path.basename(file_path)
        is_old_testament = 'OT_' in filename
        
        # Parse the file
        bible_data = parse_arabic_bible_file(file_path, is_old_testament)
        
        # Add to cumulative data
        all_data['verses'].extend(bible_data['verses'])
        all_data['words'].extend(bible_data['words'])
        
        # Log progress
        logger.info(f"Total verses so far: {len(all_data['verses'])}, words: {len(all_data['words'])}")
    
    # Load the data
    load_arabic_bible_data(db_connection, all_data)

def main():
    """Main enhanced ETL process for Arabic Bible data."""
    logger.info(f"Starting enhanced Arabic Bible ETL process")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Get database connection
        db_connection = get_db_connection()
        
        # Create the tables with updated schema
        create_tables(db_connection)
        
        # Process each directory
        directories = [
            "data/Tagged-Bibles/Arabic Bibles/Translation Tags Individual Books"
        ]
        
        for directory in directories:
            process_directory(db_connection, directory)
        
        # Final database check
        cur = db_connection.cursor()
        cur.execute("SELECT COUNT(*) FROM bible.arabic_verses")
        verse_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM bible.arabic_words")
        word_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT book_name) FROM bible.arabic_verses")
        book_count = cur.fetchone()[0]
        
        logger.info(f"Final ETL results:")
        logger.info(f"  Books: {book_count}")
        logger.info(f"  Verses: {verse_count}")
        logger.info(f"  Words: {word_count}")
        
        # Compare with expected counts
        expected_verses = 31091
        expected_words = 382293
        
        verse_ratio = verse_count / expected_verses if expected_verses > 0 else 0
        word_ratio = word_count / expected_words if expected_words > 0 else 0
        
        logger.info(f"  Verse completeness: {verse_ratio:.2%} ({verse_count}/{expected_verses})")
        logger.info(f"  Word completeness: {word_ratio:.2%} ({word_count}/{expected_words})")
        
        if word_count < expected_words:
            logger.warning(f"Word count is still below expected ({word_count} < {expected_words})")
        
        logger.info("Enhanced Arabic Bible ETL process completed successfully")
        
    except Exception as e:
        logger.error(f"Error in enhanced Arabic Bible ETL process: {str(e)}")
        sys.exit(1)
    finally:
        if 'db_connection' in locals() and db_connection is not None:
            db_connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Enhanced process for TTAraSVD (Translation Tags for Arabic SVD) Bible data')
    args = parser.parse_args()
    
    main() 