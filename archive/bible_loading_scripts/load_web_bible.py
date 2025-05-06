#!/usr/bin/env python
"""
Script to download and import the World English Bible (WEB) into the database.
The WEB is a modern public domain Bible translation.
"""

import os
import sys
import json
import logging
import requests
import psycopg2
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('web_bible_loading.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# WEB Bible API URL - using a different source
WEB_API_URL = "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_web.json"

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

def download_web_bible():
    """
    Download WEB Bible data from GitHub.
    
    Returns:
        The downloaded Bible data as a Python list of books
    """
    try:
        logger.info(f"Downloading WEB Bible from {WEB_API_URL}")
        response = requests.get(WEB_API_URL)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse JSON response - handle UTF-8 BOM
        content = response.content.decode('utf-8-sig')
        bible_data = json.loads(content)
        logger.info(f"Successfully downloaded WEB Bible: {len(bible_data)} books")
        return bible_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading WEB Bible: {e}")
        return None
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing WEB Bible JSON: {e}")
        return None

def process_web_bible(bible_data):
    """
    Process WEB Bible data into a format suitable for database import.
    
    Args:
        bible_data: The Bible data as a list of books
        
    Returns:
        A dictionary with verses ready for database import
    """
    verses = []
    
    try:
        for book in bible_data:
            book_name = book.get('name', '')
            book_abbr = book.get('abbrev', '')
            chapters = book.get('chapters', [])
            
            for chapter_idx, chapter in enumerate(chapters, 1):
                for verse_idx, verse_text in enumerate(chapter, 1):
                    verses.append({
                        'book_name': book_name,
                        'chapter_num': chapter_idx,
                        'verse_num': verse_idx,
                        'verse_text': verse_text,
                        'translation_source': 'WEB'
                    })
        
        logger.info(f"Processed {len(verses)} verses from WEB Bible")
        
    except Exception as e:
        logger.error(f"Error processing WEB Bible data: {e}")
    
    return {'verses': verses}

def load_bible_data(conn, bible_data):
    """
    Load Bible data into the database.
    
    Args:
        conn: Database connection
        bible_data: Dictionary with verse data
    """
    try:
        cursor = conn.cursor()
        
        # Insert verses
        inserted_count = 0
        updated_count = 0
        
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
            
            # Commit every 1000 verses to avoid memory issues
            if (inserted_count + updated_count) % 1000 == 0:
                conn.commit()
                logger.info(f"Processed {inserted_count + updated_count} verses...")
        
        # Final commit
        conn.commit()
        
        logger.info(f"WEB Bible data loading summary:")
        logger.info(f"  - Inserted: {inserted_count}")
        logger.info(f"  - Updated: {updated_count}")
        logger.info(f"  - Total processed: {len(bible_data['verses'])}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading WEB Bible data: {e}")
        raise

def main():
    """Main function to load WEB Bible."""
    start_time = datetime.now()
    logger.info("Starting WEB Bible data loading process")
    
    try:
        # Download Bible data
        bible_data = download_web_bible()
        if not bible_data:
            logger.error("Failed to download WEB Bible data")
            return 1
        
        # Process Bible data
        processed_data = process_web_bible(bible_data)
        
        # Connect to database
        logger.info("Connecting to database")
        conn = get_db_connection()
        
        # Load data into database
        logger.info("Loading WEB Bible data into database")
        load_bible_data(conn, processed_data)
        
        # Close connection
        conn.close()
        
        end_time = datetime.now()
        elapsed_time = end_time - start_time
        logger.info(f"WEB Bible data loading completed in {elapsed_time}")
        logger.info(f"Loaded {len(processed_data['verses'])} WEB verses into the database")
        
        print("\nWorld English Bible (WEB) successfully loaded into the database!")
        print(f"Total verses: {len(processed_data['verses'])}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error during WEB Bible data loading: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 