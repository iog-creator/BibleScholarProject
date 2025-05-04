#!/usr/bin/env python3
"""
ETL script for loading tagged Bible texts.
This script parses the TAGNT (Greek NT) and TAHOT (Hebrew OT) files from STEPBible
and loads them into the corresponding database tables.
"""

import os
import re
import logging
import argparse
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_tagged_texts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('etl_tagged_texts')

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

def parse_greek_nt_file(file_path):
    """
    Parse a TAGNT file and extract the structured data.
    
    Args:
        file_path: Path to the TAGNT file
        
    Returns:
        List of dictionaries containing the structured data for each word
    """
    logger.info(f"Parsing Greek NT file: {file_path}")
    words = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # Skip header lines
            lines_to_skip = 200  # Skip header information
            for _ in range(lines_to_skip):
                next(file, None)
            
            current_ref = None
            
            for line in file:
                line = line.strip()
                
                # Skip empty lines and comment lines
                if not line or line.startswith('#_'):
                    continue
                
                # Check if the line contains a word entry
                if re.match(r'^[A-Za-z]+\.\d+\.\d+#\d+=', line):
                    # Parse the word entry
                    parts = line.split('\t')
                    if len(parts) < 4:
                        continue
                    
                    # Extract reference and word info
                    ref_part = parts[0]
                    greek_part = parts[1] if len(parts) > 1 else ""
                    english_part = parts[2] if len(parts) > 2 else ""
                    strongs_part = parts[3] if len(parts) > 3 else ""
                    
                    # Extract book, chapter, verse, word number
                    ref_match = re.match(r'([A-Za-z]+)\.(\d+)\.(\d+)#(\d+)=([A-Za-z]+)', ref_part)
                    if ref_match:
                        book, chapter, verse, word_num, manuscript_type = ref_match.groups()
                        
                        # Extract Greek word and remove parentheses if present
                        greek_word = re.search(r'([^\(]+)(?:\s*\([^)]+\))?', greek_part)
                        greek_word = greek_word.group(1).strip() if greek_word else ""
                        
                        # Extract English translation (remove angle brackets)
                        english_trans = re.sub(r'<[^>]+>', '', english_part).strip()
                        
                        # Extract Strong's number and grammar code
                        strongs_match = re.search(r'G(\d+[A-Za-z]?)=([A-Z0-9\-]+)', strongs_part)
                        if strongs_match:
                            strongs_num, grammar_code = strongs_match.groups()
                            strongs_id = f"G{strongs_num}"
                        else:
                            strongs_id = ""
                            grammar_code = ""
                        
                        # Create word entry
                        word = {
                            'book_name': book,
                            'chapter_num': int(chapter),
                            'verse_num': int(verse),
                            'word_num': int(word_num),
                            'word_text': greek_word,
                            'translation': english_trans,
                            'strongs_id': strongs_id,
                            'grammar_code': grammar_code,
                            'manuscript_type': manuscript_type
                        }
                        words.append(word)
                        
                        if len(words) % 1000 == 0:
                            logger.info(f"Parsed {len(words)} Greek words")
    
    except Exception as e:
        logger.error(f"Error parsing Greek NT file {file_path}: {e}")
        raise
    
    logger.info(f"Completed parsing Greek NT file. Total words: {len(words)}")
    return words

def get_valid_strongs_ids(conn, strongs_ids):
    """
    Get the list of Strong's IDs that exist in the greek_entries table.
    
    Args:
        conn: Database connection
        strongs_ids: List of Strong's IDs to check
        
    Returns:
        Set of valid Strong's IDs
    """
    valid_ids = set()
    
    if not strongs_ids:
        return valid_ids
    
    try:
        with conn.cursor() as cur:
            # Use UNNEST to efficiently check multiple IDs
            cur.execute("""
                SELECT strongs_id 
                FROM bible.greek_entries 
                WHERE strongs_id IN %s
            """, (tuple(strongs_ids),))
            
            for row in cur.fetchall():
                valid_ids.add(row[0])
    
    except Exception as e:
        logger.error(f"Error checking valid Strong's IDs: {e}")
        
    return valid_ids

def save_greek_words_to_db(conn, words):
    """
    Save the parsed Greek NT words to the database.
    
    Args:
        conn: Database connection
        words: List of word dictionaries
    """
    logger.info(f"Saving {len(words)} Greek NT words to database")
    
    try:
        # First, get all unique Strong's IDs from the parsed words
        strongs_ids = set()
        for word in words:
            if word['strongs_id']:
                strongs_ids.add(word['strongs_id'])
        
        # Check which Strong's IDs exist in the lexicon
        valid_strongs_ids = get_valid_strongs_ids(conn, strongs_ids)
        logger.info(f"Found {len(valid_strongs_ids)} valid Strong's IDs out of {len(strongs_ids)} unique IDs")
        
        # Remove invalid Strong's IDs to avoid FK constraint violations
        for word in words:
            if word['strongs_id'] and word['strongs_id'] not in valid_strongs_ids:
                logger.warning(f"Removing invalid Strong's ID {word['strongs_id']} for word {word['word_text']} at {word['book_name']} {word['chapter_num']}:{word['verse_num']}")
                word['strongs_id'] = None
        
        with conn.cursor() as cur:
            # Insert verses first (unique book, chapter, verse combinations)
            verses = {}
            for word in words:
                key = (word['book_name'], word['chapter_num'], word['verse_num'])
                if key not in verses:
                    verses[key] = {
                        'book_name': word['book_name'],
                        'chapter_num': word['chapter_num'],
                        'verse_num': word['verse_num'],
                        'verse_text': '',  # Will be populated later
                        'translation_source': 'TAGNT'
                    }
            
            # Insert verses
            verse_data = list(verses.values())
            if verse_data:
                execute_batch(cur, """
                    INSERT INTO bible.verses 
                        (book_name, chapter_num, verse_num, verse_text, translation_source)
                    VALUES 
                        (%(book_name)s, %(chapter_num)s, %(verse_num)s, %(verse_text)s, %(translation_source)s)
                    ON CONFLICT (book_name, chapter_num, verse_num) DO UPDATE SET
                        translation_source = EXCLUDED.translation_source
                    RETURNING id, book_name, chapter_num, verse_num
                """, verse_data)
                
                # Get verse IDs
                verse_ids = {}
                cur.execute("""
                    SELECT id, book_name, chapter_num, verse_num 
                    FROM bible.verses 
                    WHERE (book_name, chapter_num, verse_num) IN %s
                """, (tuple((v['book_name'], v['chapter_num'], v['verse_num']) for v in verse_data),))
                
                for row in cur.fetchall():
                    verse_ids[(row[1], row[2], row[3])] = row[0]
            
            # Insert Greek words
            execute_batch(cur, """
                INSERT INTO bible.greek_nt_words 
                    (book_name, chapter_num, verse_num, word_num, word_text, translation, 
                     strongs_id, grammar_code, manuscript_type)
                VALUES 
                    (%(book_name)s, %(chapter_num)s, %(verse_num)s, %(word_num)s, %(word_text)s, 
                     %(translation)s, %(strongs_id)s, %(grammar_code)s, %(manuscript_type)s)
                ON CONFLICT (book_name, chapter_num, verse_num, word_num) DO UPDATE SET
                    word_text = EXCLUDED.word_text,
                    translation = EXCLUDED.translation,
                    strongs_id = EXCLUDED.strongs_id,
                    grammar_code = EXCLUDED.grammar_code,
                    manuscript_type = EXCLUDED.manuscript_type,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, book_name, chapter_num, verse_num, word_num
            """, words)
            
            # Get word IDs and link to verses
            cur.execute("""
                SELECT id, book_name, chapter_num, verse_num, word_num 
                FROM bible.greek_nt_words 
                WHERE (book_name, chapter_num, verse_num) IN %s
            """, (tuple((v['book_name'], v['chapter_num'], v['verse_num']) for v in verse_data),))
            
            word_links = []
            for row in cur.fetchall():
                word_id = row[0]
                book, chapter, verse, word_num = row[1], row[2], row[3], row[4]
                verse_id = verse_ids.get((book, chapter, verse))
                if verse_id:
                    word_links.append({
                        'verse_id': verse_id,
                        'greek_word_id': word_id,
                        'word_position': word_num
                    })
            
            # Insert word-verse links
            if word_links:
                execute_batch(cur, """
                    INSERT INTO bible.verse_word_links 
                        (verse_id, greek_word_id, word_position)
                    VALUES 
                        (%(verse_id)s, %(greek_word_id)s, %(word_position)s)
                    ON CONFLICT DO NOTHING
                """, word_links)
        
        conn.commit()
        logger.info(f"Successfully saved {len(words)} Greek NT words to database")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving Greek NT words to database: {e}")
        raise

def process_greek_nt_file(conn, file_path):
    """
    Process a TAGNT file and load it into the database.
    
    Args:
        conn: Database connection
        file_path: Path to the TAGNT file
    """
    logger.info(f"Processing Greek NT file: {file_path}")
    try:
        words = parse_greek_nt_file(file_path)
        save_greek_words_to_db(conn, words)
        logger.info(f"Successfully processed Greek NT file: {file_path}")
    except Exception as e:
        logger.error(f"Error processing Greek NT file {file_path}: {e}")
        raise

def main():
    """
    Main function.
    """
    parser = argparse.ArgumentParser(description='Load tagged Bible texts into the database')
    parser.add_argument('--greek', help='Path to the TAGNT Greek NT file')
    parser.add_argument('--hebrew', help='Path to the TAHOT Hebrew OT file')
    args = parser.parse_args()
    
    if not args.greek and not args.hebrew:
        logger.error("At least one of --greek or --hebrew must be specified")
        return 1
    
    try:
        logger.info("Starting ETL process for tagged Bible texts")
        
        # Connect to the database
        conn = get_db_connection()
        
        try:
            # Process Greek NT file if specified
            if args.greek:
                process_greek_nt_file(conn, args.greek)
            
            # Process Hebrew OT file if specified (to be implemented)
            if args.hebrew:
                logger.info(f"Hebrew OT processing not yet implemented for file: {args.hebrew}")
            
            logger.info("ETL process for tagged Bible texts completed successfully")
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in ETL process for tagged Bible texts: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main()) 