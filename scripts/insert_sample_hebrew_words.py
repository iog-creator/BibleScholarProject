#!/usr/bin/env python3
"""
Script to insert sample Hebrew words data into the BibleScholarProject database.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import local modules
from src.database.connection import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('insert_sample_hebrew_words')

def insert_critical_hebrew_words(conn):
    """Insert sample data for critical Hebrew theological terms."""
    # Sample data structure for critical terms
    # Format: (book_name, chapter_num, verse_num, word_num, word_text, word_transliteration, translation)
    critical_samples = [
        # Elohim (H430) - אלהים
        ('Genesis', 1, 1, 1, 'אלהים', 'elohim', 'God'),
        ('Genesis', 1, 2, 5, 'אלהים', 'elohim', 'God'),
        ('Exodus', 3, 4, 8, 'אלהים', 'elohim', 'God'),
        ('Deuteronomy', 6, 4, 3, 'אלהים', 'elohim', 'God'),
        ('Psalms', 19, 1, 7, 'אלהים', 'elohim', 'God'),
        
        # YHWH (H3068) - יהוה
        ('Genesis', 2, 4, 4, 'יהוה', 'YHWH', 'LORD'),
        ('Exodus', 3, 2, 2, 'יהוה', 'YHWH', 'LORD'),
        ('Deuteronomy', 6, 4, 1, 'יהוה', 'YHWH', 'LORD'),
        ('Psalms', 23, 1, 2, 'יהוה', 'YHWH', 'LORD'),
        ('Isaiah', 6, 1, 6, 'יהוה', 'YHWH', 'LORD'),
        
        # Adon (H113) - אדון
        ('Genesis', 18, 12, 6, 'אדון', 'adon', 'lord'),
        ('Exodus', 4, 10, 3, 'אדון', 'adon', 'lord'),
        ('Joshua', 3, 11, 2, 'אדון', 'adon', 'Lord'),
        ('Psalms', 110, 1, 3, 'אדון', 'adon', 'lord'),
        
        # Chesed (H2617) - חסד
        ('Genesis', 24, 12, 8, 'חסד', 'chesed', 'lovingkindness'),
        ('Exodus', 15, 13, 4, 'חסד', 'chesed', 'lovingkindness'),
        ('Psalms', 136, 1, 6, 'חסד', 'chesed', 'lovingkindness'),
        ('Micah', 6, 8, 5, 'חסד', 'chesed', 'mercy'),
        
        # Aman (H539) - אמן
        ('Genesis', 15, 6, 3, 'אמן', 'aman', 'believed'),
        ('Exodus', 4, 31, 5, 'אמן', 'aman', 'believed'),
        ('Isaiah', 7, 9, 4, 'אמן', 'aman', 'believe'),
        ('Habakkuk', 2, 4, 3, 'אמן', 'aman', 'faith')
    ]
    
    # Map Hebrew words to their Strong's IDs
    strongs_mapping = {
        'אלהים': 'H430',  # Elohim
        'יהוה': 'H3068',  # YHWH
        'אדון': 'H113',   # Adon
        'חסד': 'H2617',   # Chesed
        'אמן': 'H539'     # Aman
    }
    
    try:
        with conn.cursor() as cursor:
            # First check if we already have data
            cursor.execute("SELECT COUNT(*) FROM bible.hebrew_ot_words")
            count = cursor.fetchone()[0]
            
            if count > 0:
                logger.warning(f"Database already contains {count} Hebrew words. Aborting insert to avoid duplicates.")
                return False
            
            # Insert the sample data
            for sample in critical_samples:
                book_name, chapter_num, verse_num, word_num, word_text, word_transliteration, translation = sample
                strongs_id = strongs_mapping.get(word_text)
                grammar_code = "{" + strongs_id + "}"
                
                cursor.execute("""
                    INSERT INTO bible.hebrew_ot_words
                    (book_name, chapter_num, verse_num, word_num, word_text, 
                     word_transliteration, translation, strongs_id, grammar_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    book_name, chapter_num, verse_num, word_num, word_text,
                    word_transliteration, translation, strongs_id, grammar_code
                ))
            
            # Commit the transaction
            conn.commit()
            
            # Verify the inserts
            cursor.execute("""
                SELECT word_text, COUNT(*) as count
                FROM bible.hebrew_ot_words
                GROUP BY word_text
                ORDER BY word_text
            """)
            
            results = cursor.fetchall()
            logger.info("Inserted word counts:")
            for word, count in results:
                logger.info(f"  {word}: {count} records")
                
            return True
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting sample Hebrew words: {e}")
        return False

def main():
    """Main function to insert sample data."""
    logger.info("Starting sample Hebrew words insertion")
    
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return 1
        
        try:
            # Insert sample data
            if insert_critical_hebrew_words(conn):
                logger.info("Sample Hebrew words inserted successfully")
            else:
                logger.warning("No data was inserted")
            
            return 0
        
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"Error during sample data insertion: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 