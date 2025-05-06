#!/usr/bin/env python
"""
Script to download and import the American Standard Version (ASV) Bible into the database.
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
        logging.FileHandler('asv_bible_loading.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# ASV Bible API URL - using a different source
ASV_API_URL = "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_asv.json"

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
    Download ASV Bible data from GitHub.
    
    Returns:
        The downloaded Bible data as a Python list of books
    """
    try:
        logger.info(f"Downloading ASV Bible from {ASV_API_URL}")
        response = requests.get(ASV_API_URL)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse JSON response - handle UTF-8 BOM
        content = response.content.decode('utf-8-sig')
        bible_data = json.loads(content)
        logger.info(f"Successfully downloaded ASV Bible: {len(bible_data)} books")
        return bible_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading ASV Bible: {e}")
        return None
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing ASV Bible JSON: {e}")
        return None

def process_asv_bible(bible_data):
    """
    Process ASV Bible data into a format suitable for database import.
    
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
                        'translation_source': 'ASV'
                    })
        
        logger.info(f"Processed {len(verses)} verses from ASV Bible")
        
    except Exception as e:
        logger.error(f"Error processing ASV Bible data: {e}")
    
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
        
        logger.info(f"ASV Bible data loading summary:")
        logger.info(f"  - Inserted: {inserted_count}")
        logger.info(f"  - Updated: {updated_count}")
        logger.info(f"  - Total processed: {len(bible_data['verses'])}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading ASV Bible data: {e}")
        raise

def main():
    """Main function to load ASV Bible."""
    start_time = datetime.now()
    logger.info("Starting ASV Bible data loading process")
    
    try:
        # Download Bible data
        bible_data = download_asv_bible()
        if not bible_data:
            logger.error("Failed to download ASV Bible data")
            return 1
        
        # Process Bible data
        processed_data = process_asv_bible(bible_data)
        
        # Connect to database
        logger.info("Connecting to database")
        conn = get_db_connection()
        
        # Load data into database
        logger.info("Loading ASV Bible data into database")
        load_bible_data(conn, processed_data)
        
        # Close connection
        conn.close()
        
        end_time = datetime.now()
        elapsed_time = end_time - start_time
        logger.info(f"ASV Bible data loading completed in {elapsed_time}")
        logger.info(f"Loaded {len(processed_data['verses'])} ASV verses into the database")
        
        print("\nASV Bible successfully loaded into the database!")
        print(f"Total verses: {len(processed_data['verses'])}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error during ASV Bible data loading: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 