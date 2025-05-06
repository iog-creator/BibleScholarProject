#!/usr/bin/env python
"""
Script to directly download the ASV Bible from GitHub and import it into the database.
This uses the bibleapi/bibleapi-bibles-json repository which has the full ASV Bible in JSON format.
"""

import os
import sys
import json
import logging
import requests
import psycopg2
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('direct_asv_download.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# ASV Bible source URL - direct from GitHub repository
ASV_JSON_URL = "https://raw.githubusercontent.com/bibleapi/bibleapi-bibles-json/master/asv.json"

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

def download_asv_bible():
    """
    Download ASV Bible data from GitHub repository.
    
    Returns:
        The ASV Bible data as a Python list of dictionaries
    """
    try:
        logger.info(f"Downloading ASV Bible from {ASV_JSON_URL}")
        response = requests.get(ASV_JSON_URL)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse JSON response
        bible_data = response.json()
        logger.info(f"Successfully downloaded ASV Bible")
        return bible_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading ASV Bible: {e}")
        return None
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing ASV Bible JSON: {e}")
        return None

def process_bible_data(bible_data):
    """
    Process the raw Bible data into a format suitable for database import.
    
    Args:
        bible_data: The Bible data from the GitHub repository
        
    Returns:
        List of verse dictionaries ready for database import
    """
    if not bible_data or not isinstance(bible_data, dict) or 'resultset' not in bible_data:
        logger.error("Invalid bible data format")
        return []
    
    verses = []
    
    try:
        # The data structure is: bible_data -> resultset -> row -> [verses]
        if 'resultset' in bible_data and 'row' in bible_data['resultset']:
            row_data = bible_data['resultset']['row']
            
            if isinstance(row_data, list):
                for verse_data in row_data:
                    # Each verse has a 'field' array with 5 elements:
                    # [reference_id, book_num, testament_num, verse_num, verse_text]
                    if 'field' in verse_data and isinstance(verse_data['field'], list) and len(verse_data['field']) >= 5:
                        field = verse_data['field']
                        
                        # Parse the reference ID to get book, chapter, verse
                        reference_id = str(field[0])
                        book_num = int(field[1])
                        testament_num = int(field[2])
                        verse_num = int(field[3])
                        verse_text = field[4]
                        
                        # Parse chapter number from reference ID
                        # Reference ID format: BBCCCVVV (book, chapter, verse)
                        # The first 1-2 digits are the book number
                        # The middle 3 digits are the chapter number
                        # The last 3 digits are the verse number
                        if len(reference_id) >= 7:
                            try:
                                # Extract chapter from reference_id - drop book number and verse number
                                # We're only interested in the chapter part (ccc)
                                # If book number is 1-9, we have 1cccvvv
                                # If book number is 10-66, we have 2cccvvv
                                
                                # For single-digit book numbers (e.g., Genesis = 1)
                                if book_num < 10:
                                    # Skip the first digit (book number) and take the next 3 digits
                                    chapter_str = reference_id[1:4]
                                else:
                                    # Skip the first two digits (book number) and take the next 3 digits
                                    chapter_str = reference_id[2:5]
                                
                                chapter_num = int(chapter_str)
                            except ValueError:
                                # If parsing fails, use verse number as fallback
                                chapter_num = verse_num
                        else:
                            # Short reference ID, use verse number as chapter
                            chapter_num = verse_num
                        
                        book_name = get_book_name(book_num)
                        
                        verses.append({
                            'book_name': book_name,
                            'chapter_num': chapter_num,
                            'verse_num': verse_num,
                            'verse_text': verse_text,
                            'translation_source': 'ASV'
                        })
            
            logger.info(f"Processed {len(verses)} verses from ASV Bible")
            
            # Debug: Print first few verses to check format
            logger.info("Sample verses:")
            for i in range(min(5, len(verses))):
                v = verses[i]
                logger.info(f"Verse {i+1}: {v['book_name']} {v['chapter_num']}:{v['verse_num']} - {v['verse_text'][:30]}...")
                
            # Look for problematic verses
            problem_verses = []
            for v in verses:
                if v['chapter_num'] > 150:  # No book has more than 150 chapters
                    problem_verses.append(v)
            
            if problem_verses:
                logger.warning(f"Found {len(problem_verses)} problematic verses with unusual chapter numbers:")
                for i in range(min(5, len(problem_verses))):
                    v = problem_verses[i]
                    logger.warning(f"Problem verse: {v['book_name']} {v['chapter_num']}:{v['verse_num']} - {v['verse_text'][:30]}...")
        else:
            logger.error("Expected 'row' not found in Bible data")
        
        return verses
    
    except Exception as e:
        logger.error(f"Error processing ASV Bible data: {e}")
        return []

def get_book_name(book_number):
    """
    Map book number to full book name.
    
    Args:
        book_number: The numeric book reference (1-66)
        
    Returns:
        Full book name
    """
    books = [
        # Old Testament
        'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
        'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
        '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
        'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms',
        'Proverbs', 'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah',
        'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel',
        'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum',
        'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
        # New Testament
        'Matthew', 'Mark', 'Luke', 'John', 'Acts',
        'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
        'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
        '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
        'James', '1 Peter', '2 Peter', '1 John', '2 John',
        '3 John', 'Jude', 'Revelation'
    ]
    
    if 1 <= book_number <= len(books):
        return books[book_number - 1]
    return f"Book {book_number}"  # Fallback for unknown book numbers

def get_existing_verses(conn, translation='ASV'):
    """
    Get existing verses to avoid duplicates
    
    Args:
        conn: Database connection
        translation: Translation code
        
    Returns:
        Set of (book_name, chapter_num, verse_num) tuples
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT book_name, chapter_num, verse_num 
            FROM bible.verses 
            WHERE translation_source = %s
            """,
            (translation,)
        )
        
        existing = set()
        for book_name, chapter_num, verse_num in cursor.fetchall():
            existing.add((book_name, chapter_num, verse_num))
        
        logger.info(f"Found {len(existing)} existing {translation} verses in database")
        return existing
    
    except Exception as e:
        logger.error(f"Error getting existing verses: {e}")
        return set()

def load_verses(conn, verses, existing_verses):
    """
    Load verses into the database
    
    Args:
        conn: Database connection
        verses: List of verse dictionaries
        existing_verses: Set of existing verse tuples to skip
        
    Returns:
        Number of verses inserted
    """
    if not verses:
        logger.info("No verses to load")
        return 0
    
    inserted_count = 0
    skipped_count = 0
    
    try:
        cursor = conn.cursor()
        
        for verse in verses:
            # Skip if verse already exists
            if (verse['book_name'], verse['chapter_num'], verse['verse_num']) in existing_verses:
                skipped_count += 1
                continue
            
            # Insert verse
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
            
            # Commit every 1000 verses
            if inserted_count % 1000 == 0:
                conn.commit()
                logger.info(f"Inserted {inserted_count} verses so far...")
        
        # Final commit
        conn.commit()
        
        logger.info(f"ASV Bible loading summary:")
        logger.info(f"  - Inserted: {inserted_count}")
        logger.info(f"  - Skipped: {skipped_count}")
        logger.info(f"  - Total processed: {len(verses)}")
        
        return inserted_count
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading verses: {e}")
        raise

def main():
    """Main function to download and load ASV Bible data."""
    start_time = datetime.now()
    logger.info("Starting ASV Bible direct download and import process")
    
    try:
        # Download Bible data
        bible_data = download_asv_bible()
        if not bible_data:
            logger.error("Failed to download ASV Bible data")
            return 1
        
        # Process Bible data
        verses = process_bible_data(bible_data)
        if not verses:
            logger.error("Failed to process ASV Bible data")
            return 1
        
        # Connect to database
        logger.info("Connecting to database")
        conn = get_db_connection()
        
        # Get existing verses to avoid duplicates
        existing_verses = get_existing_verses(conn)
        
        # Load verses into database
        logger.info(f"Loading {len(verses)} ASV verses into database")
        inserted_count = load_verses(conn, verses, existing_verses)
        
        # Close connection
        conn.close()
        
        end_time = datetime.now()
        elapsed_time = end_time - start_time
        logger.info(f"ASV Bible data loading completed in {elapsed_time}")
        
        print("\nAmerican Standard Version (ASV) Bible successfully loaded into database!")
        print(f"Total verses inserted: {inserted_count}")
        
        # Trigger DSPy training data collection
        try:
            from src.utils import dspy_collector
            dspy_collector.trigger_after_verse_insertion(conn, 'ASV')
            logger.info("Triggered DSPy training data collection")
        except Exception as e:
            logger.warning(f"DSPy training data collection failed: {e}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error during ASV Bible data loading: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 