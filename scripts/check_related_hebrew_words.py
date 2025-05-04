#!/usr/bin/env python3
"""
Script to check for any Hebrew words in the database that might be related to the critical theological terms.
"""

import os
import sys
import re
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
logger = logging.getLogger('check_related_hebrew_words')

def search_for_related_words(conn, search_term, strongs_id=None):
    """Search for Hebrew words related to the given term."""
    try:
        with conn.cursor() as cursor:
            # Search for the exact Strong's ID
            if strongs_id:
                cursor.execute("""
                    SELECT word_text, strongs_id, COUNT(*) as count
                    FROM bible.hebrew_ot_words
                    WHERE strongs_id = %s
                    GROUP BY word_text, strongs_id
                    ORDER BY count DESC
                    LIMIT 10
                """, (strongs_id,))
                
                results = cursor.fetchall()
                logger.info(f"Words with Strong's ID {strongs_id}:")
                for word_text, sid, count in results:
                    logger.info(f"  {word_text}: {count} occurrences")
                
                # If no results, try a partial match
                if not results:
                    cursor.execute("""
                        SELECT word_text, strongs_id, COUNT(*) as count
                        FROM bible.hebrew_ot_words
                        WHERE strongs_id LIKE %s
                        GROUP BY word_text, strongs_id
                        ORDER BY count DESC
                        LIMIT 10
                    """, (f"{strongs_id}%",))
                    
                    results = cursor.fetchall()
                    logger.info(f"Words with Strong's ID starting with {strongs_id}:")
                    for word_text, sid, count in results:
                        logger.info(f"  {word_text} ({sid}): {count} occurrences")
            
            # Check if any word in the database contains the search term as a substring
            cursor.execute("""
                SELECT DISTINCT word_text, strongs_id, COUNT(*) as count
                FROM bible.hebrew_ot_words
                WHERE word_text LIKE %s
                GROUP BY word_text, strongs_id
                ORDER BY count DESC
                LIMIT 10
            """, (f"%{search_term}%",))
            
            results = cursor.fetchall()
            logger.info(f"Words containing '{search_term}':")
            for word_text, sid, count in results:
                logger.info(f"  {word_text} ({sid}): {count} occurrences")
            
            # Get most common Hebrew words
            cursor.execute("""
                SELECT word_text, strongs_id, COUNT(*) as count
                FROM bible.hebrew_ot_words
                GROUP BY word_text, strongs_id
                ORDER BY count DESC
                LIMIT 15
            """)
            
            results = cursor.fetchall()
            logger.info("Most common Hebrew words:")
            for word_text, sid, count in results:
                logger.info(f"  {word_text} ({sid}): {count} occurrences")
            
            return results
    except Exception as e:
        logger.error(f"Error searching for related words: {e}")
        return []

def search_alternative_spellings(conn):
    """Search for alternative spellings of critical theological terms."""
    # Critical terms with their Strong's IDs and expected Hebrew text
    critical_terms = {
        "H430": {"name": "Elohim", "hebrew": "אלהים"},
        "H113": {"name": "Adon", "hebrew": "אדון"},
        "H2617": {"name": "Chesed", "hebrew": "חסד"},
        "H3068": {"name": "YHWH", "hebrew": "יהוה"},
        "H539": {"name": "Aman", "hebrew": "אמן"}
    }
    
    try:
        with conn.cursor() as cursor:
            logger.info("=== Checking for alternative spellings of critical theological terms ===")
            
            # Query to find if any words are already mapped to these Strong's IDs
            for strongs_id, info in critical_terms.items():
                cursor.execute("""
                    SELECT word_text, COUNT(*) as count
                    FROM bible.hebrew_ot_words
                    WHERE strongs_id = %s
                    GROUP BY word_text
                    ORDER BY count DESC
                    LIMIT 5
                """, (strongs_id,))
                
                results = cursor.fetchall()
                logger.info(f"Words mapped to {info['name']} ({strongs_id}):")
                if results:
                    for word_text, count in results:
                        expected = "Expected" if word_text == info["hebrew"] else "Different"
                        logger.info(f"  {word_text}: {count} occurrences ({expected})")
                else:
                    logger.info(f"  No words found with Strong's ID {strongs_id}")
                
                # Check if the Hebrew word exists in the database with any Strong's ID
                cursor.execute("""
                    SELECT strongs_id, COUNT(*) as count
                    FROM bible.hebrew_ot_words
                    WHERE strongs_id IS NOT NULL
                    GROUP BY strongs_id
                    ORDER BY count DESC
                    LIMIT 20
                """)
                
                results = cursor.fetchall()
                logger.info("Most common Strong's IDs in the database:")
                for sid, count in results:
                    logger.info(f"  {sid}: {count} occurrences")
                
            # Get a sample of records to see how words are actually stored
            cursor.execute("""
                SELECT book_name, chapter_num, verse_num, word_num, word_text, strongs_id, grammar_code
                FROM bible.hebrew_ot_words
                ORDER BY RANDOM()
                LIMIT 10
            """)
            
            results = cursor.fetchall()
            logger.info("Random sample of Hebrew words in the database:")
            for book, chapter, verse, word_num, word_text, sid, grammar in results:
                logger.info(f"  {book} {chapter}:{verse} - Word #{word_num}: '{word_text}' ({sid}) - Grammar: {grammar}")
            
            # Check if there might be encoding issues by looking at the byte representation
            cursor.execute("""
                SELECT word_text, LENGTH(word_text) as char_length, 
                       OCTET_LENGTH(word_text) as byte_length,
                       strongs_id
                FROM bible.hebrew_ot_words
                WHERE strongs_id IN ('H0853', 'H3068', 'H5921a', 'H0413', 'H3605')
                LIMIT 10
            """)
            
            results = cursor.fetchall()
            logger.info("Checking for potential encoding issues:")
            for word_text, char_len, byte_len, sid in results:
                logger.info(f"  '{word_text}' ({sid}): {char_len} characters, {byte_len} bytes")
                
            # Check column types and encoding
            cursor.execute("""
                SELECT column_name, data_type, character_maximum_length, 
                       character_set_name, collation_name
                FROM information_schema.columns
                WHERE table_schema = 'bible' AND table_name = 'hebrew_ot_words'
                  AND column_name IN ('word_text', 'strongs_id', 'grammar_code')
            """)
            
            results = cursor.fetchall()
            logger.info("Column information for hebrew_ot_words:")
            for col, data_type, max_len, charset, collation in results:
                logger.info(f"  {col}: {data_type}({max_len}) - Charset: {charset}, Collation: {collation}")
                
    except Exception as e:
        logger.error(f"Error searching for alternative spellings: {e}")
        return None

def main():
    """Main function to check related Hebrew words."""
    logger.info("Starting check for related Hebrew words")
    
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return 1
        
        try:
            # Search for alternative spellings of critical terms
            search_alternative_spellings(conn)
            
            # Search for specific words
            search_for_related_words(conn, "אלה", "H430")  # Potential partial for אלהים (Elohim)
            search_for_related_words(conn, "יהו", "H3068")  # Potential partial for יהוה (YHWH)
            
            logger.info("Related Hebrew words check completed successfully")
            return 0
        
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"Error during related Hebrew words check: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 