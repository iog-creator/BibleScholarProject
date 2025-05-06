#!/usr/bin/env python
"""
ESV Bible Data Loader

This script parses the ESV Bible data file and loads it into the database.
It handles the special format of the ESV Bible file which contains Strong's numbers.

Format example:
$Gen 1:1   03=<07225>      04=<00430>      05=<01254>      07=<08064>      10=<00776>
"""

import os
import re
import sys
import logging
import psycopg2
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

# ESV Bible text data
# This is a subset of verses to test with - you would need the full text
ESV_BIBLE_TEXT = {
    'Genesis': {
        1: {
            1: "In the beginning, God created the heavens and the earth.",
            2: "The earth was without form and void, and darkness was over the face of the deep. And the Spirit of God was hovering over the face of the waters."
        }
    },
    'John': {
        3: {
            16: "For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life."
        }
    },
    'Revelation': {
        22: {
            21: "The grace of the Lord Jesus be with all. Amen."
        }
    }
}

def get_db_connection():
    """Create a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname="bible_db",
            user="postgres",
            password="postgres",
            host="localhost"
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def parse_esv_bible_file(file_path):
    """
    Parse the ESV Bible file and extract verse data.
    
    The file format is:
    $BookAbbr Chapter:Verse  WordIndex=<StrongsNum> ...
    
    Args:
        file_path: Path to the ESV Bible file
        
    Returns:
        A list of verse dictionaries ready for database insertion
    """
    verses = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines, headers, and non-verse lines
            if not line or not line.startswith('$'):
                continue
            
            # Extract verse reference
            match = re.match(r'\$([\w]{3}) (\d+):(\d+)', line)
            if not match:
                continue
                
            book_abbr, chapter, verse = match.groups()
            
            # Convert abbreviation to full book name
            book_name = BOOK_ABBR_MAP.get(book_abbr, book_abbr)
            chapter_num = int(chapter)
            verse_num = int(verse)
            
            # Get the verse text from our ESV_BIBLE_TEXT
            verse_text = ""
            if book_name in ESV_BIBLE_TEXT and chapter_num in ESV_BIBLE_TEXT[book_name] and verse_num in ESV_BIBLE_TEXT[book_name][chapter_num]:
                verse_text = ESV_BIBLE_TEXT[book_name][chapter_num][verse_num]
            
            # Add verse to the list
            verses.append({
                'book_name': book_name,
                'chapter_num': chapter_num,
                'verse_num': verse_num,
                'verse_text': verse_text,
                'translation_source': 'ESV'
            })
        
        logger.info(f"Parsed {len(verses)} verses from file {file_path}")
        
    except Exception as e:
        logger.error(f"Error parsing ESV Bible file: {e}")
        raise
    
    return {'verses': verses}

def load_esv_bible_data(conn, bible_data):
    """
    Load ESV Bible data into the database.
    
    Args:
        conn: Database connection
        bible_data: Dictionary with verse data
    """
    try:
        cursor = conn.cursor()
        
        # Insert verses
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        
        for verse in bible_data['verses']:
            # Skip verses with no text
            if not verse['verse_text']:
                skipped_count += 1
                continue
                
            # Check if verse already exists
            cursor.execute(
                """
                SELECT COUNT(*) FROM bible.verses 
                WHERE book_name = %s AND chapter_num = %s AND verse_num = %s AND translation_source = %s
                """,
                (verse['book_name'], verse['chapter_num'], verse['verse_num'], verse['translation_source'])
            )
            
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Insert new verse
                cursor.execute(
                    """
                    INSERT INTO bible.verses 
                    (book_name, chapter_num, verse_num, verse_text, translation_source, created_at) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        verse['book_name'],
                        verse['chapter_num'],
                        verse['verse_num'],
                        verse['verse_text'],
                        verse['translation_source'],
                        datetime.now()
                    )
                )
                inserted_count += 1
            else:
                # Update existing verse
                cursor.execute(
                    """
                    UPDATE bible.verses 
                    SET verse_text = %s, updated_at = %s 
                    WHERE book_name = %s AND chapter_num = %s AND verse_num = %s AND translation_source = %s
                    """,
                    (
                        verse['verse_text'],
                        datetime.now(),
                        verse['book_name'],
                        verse['chapter_num'],
                        verse['verse_num'],
                        verse['translation_source']
                    )
                )
                updated_count += 1
        
        conn.commit()
        logger.info(f"ESV Bible data loading summary:")
        logger.info(f"  - Inserted: {inserted_count}")
        logger.info(f"  - Updated: {updated_count}")
        logger.info(f"  - Skipped (no text): {skipped_count}")
        logger.info(f"  - Total processed: {len(bible_data['verses'])}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading ESV Bible data: {e}")
        raise

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
        
        # Print instructions for completing the import
        print("\nNote: This script has loaded only a sample of ESV verses.")
        print("To load the complete ESV Bible text:")
        print("1. You need to obtain the full ESV Bible text which is not included due to copyright")
        print("2. Update the ESV_BIBLE_TEXT dictionary with the full text")
        print("3. Run this script again")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error during ESV Bible data loading: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 