#!/usr/bin/env python3
"""
ETL script for processing Tagged Arabic Bible data (TTAraSVD).
This script extracts and loads Arabic Bible text with Strong's numbers and morphology tags.
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

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_arabic_bible.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('etl_arabic_bible')

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
    """Create the necessary tables for Arabic Bible data if they don't exist."""
    with conn.cursor() as cur:
        # Create table for Arabic Bible verses
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bible.arabic_verses (
                id SERIAL PRIMARY KEY,
                book_name TEXT NOT NULL,
                chapter_num INTEGER NOT NULL,
                verse_num INTEGER NOT NULL,
                verse_text TEXT NOT NULL,
                translation_source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (book_name, chapter_num, verse_num, translation_source)
            )
        """)
        
        # Create table for Arabic Bible words with Strong's numbers
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bible.arabic_words (
                id SERIAL PRIMARY KEY,
                verse_id INTEGER REFERENCES bible.arabic_verses(id),
                word_position INTEGER NOT NULL,
                arabic_word TEXT NOT NULL,
                latin_word TEXT,
                strongs_id TEXT,
                morphology TEXT,
                greek_word TEXT,
                transliteration TEXT,
                gloss TEXT,
                greek_word_position TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (verse_id, word_position)
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
        logger.info("Arabic Bible tables and indexes created or verified")

def open_file_with_zip_support(file_path):
    """Open a file with zip support if it's a zip file."""
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
                        # Return the file content
                        with codecs.open(extracted_path, 'r', encoding='utf-8-sig', errors='replace') as file:
                            return file.read()
        # If no text files found, return empty string
        return ""
    else:
        # Regular text file, open directly
        with codecs.open(file_path, 'r', encoding='utf-8-sig', errors='replace') as file:
            return file.read()

def parse_arabic_bible_file(file_path, is_old_testament=False):
    """
    Parse the TTAraSVD file to extract Arabic Bible text with Strong's numbers.
    
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
        content = open_file_with_zip_support(file_path)
        
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
        while line_index < len(lines):
            line = lines[line_index].strip()
            line_index += 1
            
            # Skip empty lines
            if not line:
                continue
                
            # Skip header and lines before actual verse data
            if line.startswith("TTArabicSVD") or line.startswith("=================="):
                continue
            
            # Check if this is a verse reference line (like "3Jn.1.1")
            if re.match(r'^[A-Za-z0-9]{3}\.\d+\.\d+$', line) or re.match(r'^[A-Za-z0-9]{3}\.\d+\.\d+\s*$', line):
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
                match = re.match(r'^([A-Za-z0-9]{3})\.(\d+)\.(\d+)', current_verse_ref)
                if match:
                    book_abbr, chapter, verse = match.groups()
                    # Convert book abbreviation to full name
                    current_book = BOOK_ABBR_MAP.get(book_abbr, book_abbr)
                    current_chapter = int(chapter)
                    current_verse = int(verse)
                    current_verse_text = ""
                    verse_words = []
                
                # Next line should be "========"
                if line_index < len(lines) and lines[line_index].strip() == "========":
                    line_index += 1
                    in_verse_section = True
                
            # Check if this is the table header line (Ara W#, Arabic, Strongs, etc.)
            elif line.startswith("Ara W#") and in_verse_section:
                # Skip this header line
                continue
            
            # Parse word data rows
            elif in_verse_section and line and "#" in line.split('\t')[0]:
                columns = line.split('\t')
                if len(columns) >= 8:  # Ensure we have enough columns
                    # Extract word position from first column (e.g., "#01")
                    word_pos_match = re.match(r'^#(\d+)(?:\s*-\s*#\d+)?', columns[0])
                    if word_pos_match:
                        word_pos = int(word_pos_match.group(1))
                        
                        # Extract Arabic word
                        arabic_word = columns[1].strip()
                        
                        # Extract Strong's ID
                        strongs_id = columns[2].strip() if len(columns) > 2 else None
                        
                        # Build word record with all available data
                        word_data = {
                            'verse_id': None,  # Will be set when verse is processed
                            'word_position': word_pos,
                            'arabic_word': arabic_word,
                            'strongs_id': strongs_id
                        }
                        
                        # Add optional fields if available
                        if len(columns) > 3:  # Greek/Hebrew word
                            word_data['greek_word'] = columns[3].strip()
                        
                        if len(columns) > 4:  # Lexicon entry
                            word_data['lexicon'] = columns[4].strip()
                        
                        if len(columns) > 5:  # Gloss
                            word_data['gloss'] = columns[5].strip()
                        
                        if len(columns) > 6:  # Transliteration
                            word_data['transliteration'] = columns[6].strip()
                        
                        if len(columns) > 7:  # Morphology
                            word_data['morphology'] = columns[7].strip()
                        
                        if len(columns) > 8:  # Greek word position
                            word_data['greek_word_position'] = columns[8].strip()
                        
                        # Add to the current verse's words
                        verse_words.append(word_data)
                        
                        # Add words to verse text (for display purposes)
                        if current_verse_text:
                            current_verse_text += " "
                        current_verse_text += arabic_word
            
            # If we reach a new verse section, save the previous one
            if line_index < len(lines) and re.match(r'^[A-Za-z0-9]{3}\.\d+\.\d+$', lines[line_index].strip()):
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
        
        logger.info(f"Parsed {len(bible_data['verses'])} verses and {len(bible_data['words'])} words from file")
        
    except Exception as e:
        logger.error(f"Error parsing Arabic Bible file: {e}")
        raise
    
    return bible_data

def load_arabic_bible_data(db_connection, bible_data):
    """
    Load the parsed Arabic Bible data into the database.
    """
    try:
        cur = db_connection.cursor()
        
        # Check if there are existing entries for this translation
        cur.execute("SELECT COUNT(*) FROM bible.arabic_verses WHERE translation_source = 'TTAraSVD'")
        count = cur.fetchone()[0]
        
        if count > 0:
            logger.info(f"Found {count} existing Arabic Bible verses. Truncating related tables to update with new data.")
            # Truncate related tables in the correct order
            cur.execute("TRUNCATE TABLE bible.arabic_words CASCADE")
            cur.execute("TRUNCATE TABLE bible.arabic_verses CASCADE")
            db_connection.commit()
        
        # Insert verses and get verse IDs
        verse_id_map = {}
        
        # Insert verses
        for i, verse in enumerate(bible_data['verses']):
            cur.execute("""
                INSERT INTO bible.arabic_verses
                (book_name, chapter_num, verse_num, verse_text, translation_source)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                verse['book_name'],
                verse['chapter_num'],
                verse['verse_num'],
                verse['verse_text'],
                verse['translation_source']
            ))
            verse_id = cur.fetchone()[0]
            verse_id_map[i + 1] = verse_id
            
            # Commit every 500 verses
            if (i + 1) % 500 == 0:
                db_connection.commit()
                logger.info(f"Inserted {i + 1} verses so far")
        
        # Commit remaining verses
        db_connection.commit()
        logger.info(f"Inserted {len(bible_data['verses'])} verses")
        
        # Insert words
        words_inserted = 0
        duplicates_skipped = 0
        
        for i, word in enumerate(bible_data['words']):
            # Map the original verse_id to the database verse_id
            db_verse_id = verse_id_map.get(word['verse_id'])
            if not db_verse_id:
                continue
            
            # Prepare optional fields
            columns = ["verse_id", "word_position", "arabic_word", "strongs_id"]
            values = [db_verse_id, word['word_position'], word['arabic_word'], word['strongs_id']]
            
            # Add optional fields if they exist
            optional_fields = [
                ('greek_word', 'greek_word'), 
                ('transliteration', 'transliteration'),
                ('gloss', 'gloss'), 
                ('morphology', 'morphology'),
                ('greek_word_position', 'greek_word_position'),
                ('lexicon', 'latin_word')  # Map lexicon to latin_word for compatibility
            ]
            
            for word_key, db_column in optional_fields:
                if word_key in word and word[word_key]:
                    columns.append(db_column)
                    values.append(word[word_key])
            
            # Dynamically build the SQL query with ON CONFLICT DO NOTHING
            placeholders = ", ".join(["%s"] * len(values))
            column_names = ", ".join(columns)
            
            sql_query = f"""
                INSERT INTO bible.arabic_words
                ({column_names})
                VALUES ({placeholders})
                ON CONFLICT (verse_id, word_position) DO NOTHING
            """
            
            try:
                cur.execute(sql_query, values)
                if cur.rowcount > 0:
                    words_inserted += 1
                else:
                    duplicates_skipped += 1
            except Exception as e:
                logger.warning(f"Error inserting word at position {word['word_position']} for verse id {db_verse_id}: {e}")
                # Continue processing other words
                continue
            
            # Commit every 1000 words
            if (i + 1) % 1000 == 0:
                db_connection.commit()
                logger.info(f"Processed {i + 1} words (inserted: {words_inserted}, skipped: {duplicates_skipped})")
        
        # Commit remaining words
        db_connection.commit()
        logger.info(f"Inserted {words_inserted} words (skipped {duplicates_skipped} duplicates)")
        
    except Exception as e:
        db_connection.rollback()
        logger.error(f"Error loading Arabic Bible data: {e}")
        raise e

def main(files=None):
    """Main ETL process for Arabic Bible data."""
    logger.info(f"Starting Arabic Bible ETL process")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Get database connection
        db_connection = get_db_connection()
        
        # Create the tables if they don't exist
        create_tables(db_connection)
        
        # If no files are specified, process all book files from the individual books directory
        if not files:
            base_dir = "data/Tagged-Bibles/Arabic Bibles/Translation Tags Individual Books"
            files = []
            
            # Get all individual book files (both NT and OT)
            for pattern in ["NT_*_TTAraSVD*.txt", "OT_*_TTAraSVD*.txt"]:
                book_files = glob.glob(os.path.join(base_dir, pattern))
                files.extend(book_files)
            
            logger.info(f"Found {len(files)} individual book files to process")
        
        # Process each file
        all_bible_data = {
            'verses': [],
            'words': []
        }
        
        for file_path in files:
            logger.info(f"Processing file: {file_path}")
            is_old_testament = 'OT_' in os.path.basename(file_path)
            bible_data = parse_arabic_bible_file(file_path, is_old_testament)
            
            all_bible_data['verses'].extend(bible_data['verses'])
            all_bible_data['words'].extend(bible_data['words'])
            
            # Log progress
            logger.info(f"Total verses so far: {len(all_bible_data['verses'])}, words: {len(all_bible_data['words'])}")
        
        # Load the data into the database
        load_arabic_bible_data(db_connection, all_bible_data)
        
        logger.info("Arabic Bible ETL process completed successfully")
        
    except Exception as e:
        logger.error(f"Error in Arabic Bible ETL process: {e}")
        sys.exit(1)
    finally:
        if 'db_connection' in locals() and db_connection is not None:
            db_connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process TTAraSVD (Translation Tags for Arabic SVD) Bible data')
    parser.add_argument('--files', type=str, nargs='*', 
                        help='Optional: Paths to the TTAraSVD files (if not specified, processes all individual book files)')
    args = parser.parse_args()
    
    main(args.files) 