#!/usr/bin/env python
"""
Script to download and import public domain Bible translations into the database.
This script handles KJV and ASV Bible texts from public repositories.
"""

import os
import sys
import json
import logging
import requests
import psycopg2
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('public_domain_bibles.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Bible sources (GitHub repositories with JSON Bible data)
BIBLE_SOURCES = {
    'KJV': {
        'url': 'https://raw.githubusercontent.com/scrollmapper/bible_databases/master/json/t_kjv.json',
        'name': 'King James Version'
    },
    'ASV': {
        'url': 'https://raw.githubusercontent.com/scrollmapper/bible_databases/master/json/t_asv.json',
        'name': 'American Standard Version'
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

def download_bible_json(translation_code):
    """
    Download Bible JSON data from GitHub repository.
    
    Args:
        translation_code: The translation code (KJV, ASV)
        
    Returns:
        The downloaded Bible data as a Python dictionary
    """
    if translation_code not in BIBLE_SOURCES:
        logger.error(f"Unknown translation code: {translation_code}")
        return None
    
    source = BIBLE_SOURCES[translation_code]
    url = source['url']
    
    try:
        logger.info(f"Downloading {source['name']} from {url}")
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse JSON response
        bible_data = response.json()
        logger.info(f"Successfully downloaded {source['name']}")
        return bible_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading {source['name']}: {e}")
        return None
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON for {source['name']}: {e}")
        return None

def download_and_save_bible(translation_code, output_dir='data/raw'):
    """
    Download Bible data and save to file.
    
    Args:
        translation_code: The translation code (KJV, ASV)
        output_dir: Directory to save the file
        
    Returns:
        Path to the saved file or None if download failed
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Download Bible data
    bible_data = download_bible_json(translation_code)
    if not bible_data:
        return None
    
    # Save to file
    output_file = os.path.join(output_dir, f"{translation_code.lower()}_bible.json")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(bible_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {translation_code} Bible data to {output_file}")
        return output_file
    
    except Exception as e:
        logger.error(f"Error saving {translation_code} Bible data: {e}")
        return None

def process_github_json_bible(json_data, translation_code):
    """
    Process GitHub JSON Bible data into a format suitable for database import.
    
    This function handles the format from scrollmapper repository.
    
    Args:
        json_data: The JSON Bible data
        translation_code: The translation code (KJV, ASV)
        
    Returns:
        A dictionary with verses ready for database import
    """
    verses = []
    
    try:
        # Process each verse
        for verse in json_data:
            book_num = int(verse.get('b', 0))
            chapter_num = int(verse.get('c', 0))
            verse_num = int(verse.get('v', 0))
            text = verse.get('t', '')
            
            # Get book name - the JSON format uses numbers, we need to map them
            book_name = get_book_name_from_number(book_num)
            
            # Add to verses list
            verses.append({
                'book_name': book_name,
                'chapter_num': chapter_num,
                'verse_num': verse_num,
                'verse_text': text,
                'translation_source': translation_code
            })
        
        logger.info(f"Processed {len(verses)} verses from {translation_code}")
        
    except Exception as e:
        logger.error(f"Error processing {translation_code} Bible data: {e}")
    
    return {'verses': verses}

def get_book_name_from_number(book_num):
    """Map book number to full book name."""
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
    
    if 1 <= book_num <= len(books):
        return books[book_num - 1]
    return f"Book {book_num}"  # Fallback for unknown book numbers

def load_bible_data(conn, bible_data, translation_code):
    """
    Load Bible data into the database.
    
    Args:
        conn: Database connection
        bible_data: Dictionary with verse data
        translation_code: The translation code (KJV, ASV)
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
        
        logger.info(f"{translation_code} Bible data loading summary:")
        logger.info(f"  - Inserted: {inserted_count}")
        logger.info(f"  - Updated: {updated_count}")
        logger.info(f"  - Total processed: {len(bible_data['verses'])}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading {translation_code} Bible data: {e}")
        raise

def load_translation(translation_code):
    """
    Download and load a Bible translation into the database.
    
    Args:
        translation_code: The translation code (KJV, ASV)
        
    Returns:
        True if successful, False otherwise
    """
    start_time = datetime.now()
    logger.info(f"Starting {translation_code} Bible data loading process")
    
    try:
        # Download Bible data
        bible_json = download_bible_json(translation_code)
        if not bible_json:
            return False
        
        # Process Bible data
        bible_data = process_github_json_bible(bible_json, translation_code)
        
        # Connect to database
        logger.info("Connecting to database")
        conn = get_db_connection()
        
        # Load data into database
        logger.info(f"Loading {translation_code} Bible data into database")
        load_bible_data(conn, bible_data, translation_code)
        
        # Close connection
        conn.close()
        
        end_time = datetime.now()
        elapsed_time = end_time - start_time
        logger.info(f"{translation_code} Bible data loading completed in {elapsed_time}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error during {translation_code} Bible data loading: {e}")
        return False

def main():
    """Main function to load public domain Bible translations."""
    overall_start_time = datetime.now()
    logger.info("Starting public domain Bible data loading process")
    
    # Define translations to load
    translations = ['KJV', 'ASV']
    
    # Load each translation
    results = {}
    for translation in translations:
        success = load_translation(translation)
        results[translation] = 'Success' if success else 'Failed'
    
    # Print summary
    overall_end_time = datetime.now()
    overall_elapsed_time = overall_end_time - overall_start_time
    logger.info(f"All Bible data loading completed in {overall_elapsed_time}")
    
    print("\nBible Loading Summary:")
    for translation, result in results.items():
        print(f"  - {BIBLE_SOURCES[translation]['name']} ({translation}): {result}")
    
    # Check results
    if all(result == 'Success' for result in results.values()):
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main()) 