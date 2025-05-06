#!/usr/bin/env python
"""
Script to download and import the American Standard Version (ASV) Bible into the database.
This script uses the Bible API from wldeh/bible-api as the source.
"""

import os
import sys
import json
import logging
import requests
import psycopg2
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('asv_bible_loading.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Bible API base URL for ASV
API_BASE_URL = "https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/en-asv/books"

# Define Bible books to process
BIBLE_BOOKS = [
    "genesis", "exodus", "leviticus", "numbers", "deuteronomy",
    "joshua", "judges", "ruth", "1-samuel", "2-samuel",
    "1-kings", "2-kings", "1-chronicles", "2-chronicles",
    "ezra", "nehemiah", "esther", "job", "psalms",
    "proverbs", "ecclesiastes", "song-of-solomon", "isaiah", "jeremiah",
    "lamentations", "ezekiel", "daniel", "hosea", "joel",
    "amos", "obadiah", "jonah", "micah", "nahum",
    "habakkuk", "zephaniah", "haggai", "zechariah", "malachi",
    "matthew", "mark", "luke", "john", "acts",
    "romans", "1-corinthians", "2-corinthians", "galatians", "ephesians",
    "philippians", "colossians", "1-thessalonians", "2-thessalonians",
    "1-timothy", "2-timothy", "titus", "philemon", "hebrews",
    "james", "1-peter", "2-peter", "1-john", "2-john",
    "3-john", "jude", "revelation"
]

# Mapping for database book names (without hyphens, matching what's already in the database)
BOOK_NAME_MAPPING = {
    "genesis": "Genesis",
    "exodus": "Exodus",
    "leviticus": "Leviticus",
    "numbers": "Numbers",
    "deuteronomy": "Deuteronomy",
    "joshua": "Joshua",
    "judges": "Judges",
    "ruth": "Ruth",
    "1-samuel": "1 Samuel",
    "2-samuel": "2 Samuel",
    "1-kings": "1 Kings",
    "2-kings": "2 Kings",
    "1-chronicles": "1 Chronicles",
    "2-chronicles": "2 Chronicles",
    "ezra": "Ezra",
    "nehemiah": "Nehemiah",
    "esther": "Esther",
    "job": "Job",
    "psalms": "Psalms",
    "proverbs": "Proverbs",
    "ecclesiastes": "Ecclesiastes",
    "song-of-solomon": "Song of Solomon",
    "isaiah": "Isaiah",
    "jeremiah": "Jeremiah",
    "lamentations": "Lamentations",
    "ezekiel": "Ezekiel",
    "daniel": "Daniel",
    "hosea": "Hosea",
    "joel": "Joel",
    "amos": "Amos",
    "obadiah": "Obadiah",
    "jonah": "Jonah",
    "micah": "Micah",
    "nahum": "Nahum",
    "habakkuk": "Habakkuk",
    "zephaniah": "Zephaniah",
    "haggai": "Haggai",
    "zechariah": "Zechariah",
    "malachi": "Malachi",
    "matthew": "Matthew",
    "mark": "Mark",
    "luke": "Luke",
    "john": "John",
    "acts": "Acts",
    "romans": "Romans",
    "1-corinthians": "1 Corinthians",
    "2-corinthians": "2 Corinthians",
    "galatians": "Galatians",
    "ephesians": "Ephesians",
    "philippians": "Philippians",
    "colossians": "Colossians",
    "1-thessalonians": "1 Thessalonians",
    "2-thessalonians": "2 Thessalonians",
    "1-timothy": "1 Timothy",
    "2-timothy": "2 Timothy",
    "titus": "Titus",
    "philemon": "Philemon",
    "hebrews": "Hebrews",
    "james": "James",
    "1-peter": "1 Peter",
    "2-peter": "2 Peter",
    "1-john": "1 John",
    "2-john": "2 John",
    "3-john": "3 John",
    "jude": "Jude",
    "revelation": "Revelation"
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

def fetch_chapter_data(book, chapter):
    """
    Fetch chapter data from the API
    
    Args:
        book: Book name (as in API URL)
        chapter: Chapter number
        
    Returns:
        Dictionary with chapter data or None if error
    """
    url = f"{API_BASE_URL}/{book}/chapters/{chapter}.json"
    
    try:
        # Add a small delay to avoid rate limiting
        time.sleep(0.1)
        
        logger.debug(f"Fetching {book} chapter {chapter} from {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        # Convert response to JSON
        data = response.json()
        return data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {book} chapter {chapter}: {e}")
        return None
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON for {book} chapter {chapter}: {e}")
        return None

def get_chapter_count(book):
    """
    Determine how many chapters a book has by trying to fetch chapters
    until we get a 404 error
    
    Args:
        book: Book name
        
    Returns:
        Number of chapters
    """
    chapter = 1
    while True:
        url = f"{API_BASE_URL}/{book}/chapters/{chapter}.json"
        response = requests.get(url)
        
        if response.status_code == 404:
            # Previous chapter was the last one
            return chapter - 1
        
        chapter += 1
        
        # Safety check - no book has more than 150 chapters
        if chapter > 150:
            logger.warning(f"Safety limit reached for {book} chapter count")
            return chapter - 1

def process_book(book, existing_verses):
    """
    Process a single book: get chapter count, fetch all chapters, extract verses
    
    Args:
        book: Book name (as in API URL)
        existing_verses: Set of (book_name, chapter_num, verse_num) tuples that
                         already exist in the database
        
    Returns:
        List of verse dictionaries
    """
    logger.info(f"Processing {book}...")
    book_verses = []
    
    try:
        # Get chapter count
        chapter_count = get_chapter_count(book)
        logger.info(f"{book} has {chapter_count} chapters")
        
        # Process each chapter
        for chapter_num in range(1, chapter_count + 1):
            chapter_data = fetch_chapter_data(book, chapter_num)
            
            if not chapter_data:
                logger.warning(f"Skipping {book} chapter {chapter_num} due to fetch error")
                continue
            
            # Process each verse in the chapter
            for verse_num, verse_text in chapter_data.items():
                if not verse_num.isdigit():
                    # Skip non-numeric keys (metadata etc.)
                    continue
                
                verse_num = int(verse_num)
                book_name = BOOK_NAME_MAPPING.get(book)
                
                # Skip if verse already exists
                if (book_name, chapter_num, verse_num) in existing_verses:
                    logger.debug(f"Skipping existing verse: {book_name} {chapter_num}:{verse_num}")
                    continue
                
                book_verses.append({
                    'book_name': book_name,
                    'chapter_num': chapter_num,
                    'verse_num': verse_num,
                    'verse_text': verse_text,
                    'translation_source': 'ASV'
                })
        
        logger.info(f"Processed {len(book_verses)} verses from {book}")
        
    except Exception as e:
        logger.error(f"Error processing {book}: {e}")
    
    return book_verses

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

def load_verses(conn, verses):
    """
    Load verses into the database
    
    Args:
        conn: Database connection
        verses: List of verse dictionaries
        
    Returns:
        Number of verses inserted
    """
    if not verses:
        logger.info("No verses to load")
        return 0
    
    inserted_count = 0
    updated_count = 0
    
    try:
        cursor = conn.cursor()
        
        for verse in verses:
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
            
            # Commit every 100 verses
            if inserted_count % 100 == 0:
                conn.commit()
                logger.info(f"Inserted {inserted_count} verses so far...")
        
        # Final commit
        conn.commit()
        
        logger.info(f"ASV Bible loading summary:")
        logger.info(f"  - Inserted: {inserted_count}")
        logger.info(f"  - Total: {inserted_count}")
        
        return inserted_count
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading verses: {e}")
        raise

def main():
    """Main function to load ASV Bible data."""
    start_time = datetime.now()
    logger.info("Starting ASV Bible data loading process")
    
    try:
        # Connect to database
        conn = get_db_connection()
        
        # Get existing verses to avoid duplicates
        existing_verses = get_existing_verses(conn)
        
        all_verses = []
        
        # Process books using ThreadPoolExecutor for parallelism
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_book = {executor.submit(process_book, book, existing_verses): book for book in BIBLE_BOOKS}
            
            for future in as_completed(future_to_book):
                book = future_to_book[future]
                try:
                    verses = future.result()
                    all_verses.extend(verses)
                    logger.info(f"Completed processing {book}, got {len(verses)} verses")
                except Exception as e:
                    logger.error(f"Error processing {book}: {e}")
        
        # Load all verses into database
        logger.info(f"Loading {len(all_verses)} ASV verses into database")
        inserted_count = load_verses(conn, all_verses)
        
        # Close connection
        conn.close()
        
        end_time = datetime.now()
        elapsed_time = end_time - start_time
        logger.info(f"ASV Bible data loading completed in {elapsed_time}")
        
        print(f"\nASV Bible successfully loaded into database!")
        print(f"Total verses: {inserted_count}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error during ASV Bible data loading: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 