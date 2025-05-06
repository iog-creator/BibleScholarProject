"""
ETL script for loading English Bible text data into the database.
This script handles processing English Bible text files, specifically the ESV translation.

Input Files Used:
- TTESV file: TTESV - Tyndale Translation tags for ESV - TyndaleHouse.com STEPBible.org CC BY-NC.txt

Features:
- Processes English Bible verse data
- Handles Strong's numbers and morphology codes
- Creates structured data for database loading
- Implements error handling

Database Schema:
--------------
Core Tables:
- bible.verses: Core verse data

Usage:
    python etl_english_bible.py

Dependencies:
------------
Core:
- pandas
- psycopg2-binary
- sqlalchemy
- logging
- re

Note:
----
This script is part of the BibleScholar project.
All data is created by Tyndale House Cambridge and curated by STEPBible.org.
"""

import os
import re
import logging
import pandas as pd
import psycopg2
from typing import Dict, List, Any
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('etl_english_bible.log', mode='w')
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

def parse_esv_bible_file(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parse the TTESV file to extract English Bible text with Strong's numbers.
    
    Args:
        file_path: Path to the TTESV file
        
    Returns:
        A dictionary with verse data
    """
    bible_data = {
        'verses': []
    }
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into lines
        lines = content.split('\n')
        
        current_book = None
        current_chapter = None
        current_verse = None
        current_verse_text = ""
        verse_section_started = False
        
        line_index = 0
        while line_index < len(lines):
            line = lines[line_index].strip()
            line_index += 1
            
            # Skip empty lines and license/header information
            if not line or 'STEPBible.org' in line or 'CC BY' in line or line.startswith('='):
                continue
            
            # Check if this is a verse reference line (like "Mat.1.1")
            verse_ref_match = re.match(r'^([A-Za-z0-9]{3})\.(\d+)\.(\d+)(\s+|$)', line)
            if verse_ref_match:
                # If we were processing a previous verse, save it
                if current_book and current_chapter and current_verse and current_verse_text:
                    bible_data['verses'].append({
                        'book_name': current_book,
                        'chapter_num': current_chapter,
                        'verse_num': current_verse,
                        'verse_text': current_verse_text,
                        'translation_source': 'ESV'
                    })
                
                # Parse new verse reference
                book_abbr, chapter, verse = verse_ref_match.groups()[0:3]
                # Convert book abbreviation to full name
                current_book = BOOK_ABBR_MAP.get(book_abbr, book_abbr)
                current_chapter = int(chapter)
                current_verse = int(verse)
                current_verse_text = ""
                verse_section_started = True
                
                # The verse text might be on the same line after the reference
                rest_of_line = line[verse_ref_match.end():].strip()
                if rest_of_line:
                    current_verse_text = rest_of_line
            
            # If we're in a verse section and this is not a new verse reference,
            # then this line is part of the verse text
            elif verse_section_started and not re.match(r'^([A-Za-z0-9]{3})\.(\d+)\.(\d+)', line):
                # Skip lines with Strong's numbers or morphology codes
                if line.startswith('#') or re.match(r'^\d+\s+', line):
                    continue
                
                if current_verse_text:
                    current_verse_text += " " + line
                else:
                    current_verse_text = line
        
        # Don't forget to process the last verse
        if current_book and current_chapter and current_verse and current_verse_text:
            bible_data['verses'].append({
                'book_name': current_book,
                'chapter_num': current_chapter,
                'verse_num': current_verse,
                'verse_text': current_verse_text,
                'translation_source': 'ESV'
            })
        
        logger.info(f"Parsed {len(bible_data['verses'])} verses from file {file_path}")
        
    except Exception as e:
        logger.error(f"Error parsing English Bible file: {e}")
        raise
    
    return bible_data

def load_esv_bible_data(conn, bible_data: Dict[str, List[Dict[str, Any]]]):
    """
    Load ESV Bible data into the database.
    
    Args:
        conn: Database connection
        bible_data: Dictionary with verse data
    """
    try:
        cursor = conn.cursor()
        
        # Insert verses
        for verse in bible_data['verses']:
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
        
        conn.commit()
        logger.info(f"Successfully loaded {len(bible_data['verses'])} ESV verses into the database")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading ESV Bible data: {e}")
        raise

def process_esv_bible():
    """Process ESV Bible file and load into database."""
    try:
        # Get the path to the ESV Bible file
        file_path = "STEPBible-Data/Tagged-Bibles/TTESV - Tyndale Translation tags for ESV - TyndaleHouse.com STEPBible.org CC BY-NC.txt"
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"ESV Bible file not found: {file_path}")
            return
        
        # Parse the file
        bible_data = parse_esv_bible_file(file_path)
        
        # Connect to the database
        conn = get_db_connection()
        
        # Load the data
        load_esv_bible_data(conn, bible_data)
        
        # Close the connection
        conn.close()
        
        logger.info("ESV Bible processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing ESV Bible: {e}")

def main():
    """Main entry point for the script."""
    try:
        process_esv_bible()
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main() 