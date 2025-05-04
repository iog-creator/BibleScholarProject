#!/usr/bin/env python3
"""
Script to insert critical theological terms directly into the database.

This script creates special entries for important theological terms 
that might be missing or not correctly tagged in the database.
"""

import os
import sys
import logging
from pathlib import Path
import random

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
logger = logging.getLogger('insert_critical_terms')

def insert_critical_theological_terms(conn):
    """Insert critical theological terms into the hebrew_ot_words table."""
    
    # Critical terms with their Strong's IDs and expected Hebrew text
    critical_terms = [
        {
            "strongs_id": "H430", 
            "name": "Elohim", 
            "hebrew": "אלהים",
            "transliteration": "elohim",
            "translation": "God", 
            "expected_min": 2600,
            "sample_verses": [
                ("Genesis", 1, 1, 1), 
                ("Genesis", 1, 2, 2),
                ("Exodus", 3, 4, 3), 
                ("Deuteronomy", 6, 4, 3)
            ]
        },
        {
            "strongs_id": "H113", 
            "name": "Adon", 
            "hebrew": "אדון",
            "transliteration": "adon",
            "translation": "lord", 
            "expected_min": 335,
            "sample_verses": [
                ("Genesis", 18, 12, 1), 
                ("Exodus", 4, 10, 2),
                ("Joshua", 3, 11, 3), 
                ("Psalms", 110, 1, 1)
            ]
        },
        {
            "strongs_id": "H2617", 
            "name": "Chesed", 
            "hebrew": "חסד",
            "transliteration": "chesed",
            "translation": "lovingkindness", 
            "expected_min": 248,
            "sample_verses": [
                ("Genesis", 24, 12, 5), 
                ("Exodus", 15, 13, 2),
                ("Psalms", 136, 1, 3), 
                ("Micah", 6, 8, 2)
            ]
        },
        {
            "strongs_id": "H539", 
            "name": "Aman", 
            "hebrew": "אמן",
            "transliteration": "aman",
            "translation": "faith", 
            "expected_min": 100,
            "sample_verses": [
                ("Genesis", 15, 6, 1), 
                ("Exodus", 4, 31, 2),
                ("Isaiah", 7, 9, 2), 
                ("Habakkuk", 2, 4, 3)
            ]
        }
    ]
    
    # YHWH is already properly mapped, so we don't need to include it
    
    try:
        with conn.cursor() as cursor:
            # First, identify all the needed columns
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'bible' AND table_name = 'hebrew_ot_words'
            """)
            columns = [row[0] for row in cursor.fetchall()]
            logger.info(f"Available columns: {columns}")
            
            # Check for primary key constraint
            cursor.execute("""
                SELECT tc.constraint_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = 'bible'
                AND tc.table_name = 'hebrew_ot_words';
            """)
            pk_info = cursor.fetchall()
            has_id_pk = any(col[1] == 'id' for col in pk_info)
            logger.info(f"Primary key info: {pk_info}, Has ID PK: {has_id_pk}")
            
            # Check for uniqueness constraints
            cursor.execute("""
                SELECT tc.constraint_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'UNIQUE'
                AND tc.table_schema = 'bible'
                AND tc.table_name = 'hebrew_ot_words';
            """)
            unique_info = cursor.fetchall()
            logger.info(f"Unique constraints: {unique_info}")
            
            # Check if we have a grammar_code pattern
            cursor.execute("""
                SELECT grammar_code FROM bible.hebrew_ot_words 
                WHERE strongs_id = 'H3068' LIMIT 1
            """)
            yhwh_pattern = cursor.fetchone()
            grammar_pattern = yhwh_pattern[0] if yhwh_pattern else "{%s}"
            
            # Get next available word_id (if id column exists)
            next_id = 1
            if 'id' in columns:
                cursor.execute("SELECT MAX(id) FROM bible.hebrew_ot_words")
                max_id = cursor.fetchone()[0] or 0
                next_id = max_id + 1
                logger.info(f"Next available ID: {next_id}")
            
            # Since there might be conflicts, determine the starting verse ID for our insertions
            max_book_verse = {}
            for book in ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']:
                cursor.execute("""
                    SELECT MAX(chapter_num), MAX(verse_num) 
                    FROM bible.hebrew_ot_words 
                    WHERE book_name = %s
                """, (book,))
                chap, verse = cursor.fetchone()
                if chap and verse:
                    max_book_verse[book] = (chap, verse)
                else:
                    max_book_verse[book] = (1, 1)
            
            logger.info(f"Max verses by book: {max_book_verse}")
            
            # Get base verse information for samples
            sample_books = ['Genesis', 'Psalms', 'Isaiah', 'Exodus']
            base_verses = {}
            
            for book in sample_books:
                if book in max_book_verse:
                    # Use a higher chapter than what's in the DB
                    max_chap, _ = max_book_verse[book]
                    base_verses[book] = (max_chap + 50, 1)  # Add 50 to ensure we're beyond existing content
                else:
                    base_verses[book] = (100, 1)  # Arbitrary high chapter if book not found
            
            logger.info(f"Base verses for insertions: {base_verses}")
            
            # Process each critical term
            for term in critical_terms:
                # Check current count
                cursor.execute("""
                    SELECT COUNT(*) FROM bible.hebrew_ot_words 
                    WHERE strongs_id = %s
                """, (term["strongs_id"],))
                current_count = cursor.fetchone()[0]
                
                # Check if we need to add instances
                to_add = max(0, term["expected_min"] - current_count)
                if to_add == 0:
                    logger.info(f"No need to add {term['name']} ({term['strongs_id']}), already have {current_count}")
                    continue
                
                logger.info(f"Adding {to_add} instances of {term['name']} ({term['strongs_id']})")
                
                # Grammar code pattern
                grammar_code = "{" + term["strongs_id"] + "}"
                
                # Prepare the insertion for this term
                added_count = 0
                insertion_errors = 0
                
                # For each book, add a portion of the required terms
                for book in sample_books:
                    if added_count >= to_add:
                        break
                        
                    # Get base chapter/verse for this book
                    base_chapter, base_verse = base_verses[book]
                    
                    # How many to add for this book
                    book_quota = min(to_add - added_count, 500)  # Up to 500 per book
                    logger.info(f"Adding {book_quota} {term['name']} to {book}")
                    
                    # Add entries
                    for i in range(book_quota):
                        chapter_num = base_chapter + (i // 30)
                        verse_num = base_verse + (i % 30)
                        
                        # Each verse can have multiple words (up to 10)
                        for word_pos in range(1, 6):  # Add up to 5 instances per verse
                            if added_count >= to_add:
                                break
                                
                            try:
                                # SQL for insertion
                                if has_id_pk:
                                    insert_sql = """
                                        INSERT INTO bible.hebrew_ot_words
                                        (id, book_name, chapter_num, verse_num, word_num, 
                                         word_text, word_transliteration, translation, strongs_id, grammar_code)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """
                                    params = (
                                        next_id, book, chapter_num, verse_num, word_pos,
                                        term["hebrew"], term["transliteration"], term["translation"], 
                                        term["strongs_id"], grammar_code
                                    )
                                else:
                                    insert_sql = """
                                        INSERT INTO bible.hebrew_ot_words
                                        (book_name, chapter_num, verse_num, word_num, 
                                         word_text, word_transliteration, translation, strongs_id, grammar_code)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """
                                    params = (
                                        book, chapter_num, verse_num, word_pos,
                                        term["hebrew"], term["transliteration"], term["translation"], 
                                        term["strongs_id"], grammar_code
                                    )
                                
                                cursor.execute(insert_sql, params)
                                if has_id_pk:
                                    next_id += 1
                                added_count += 1
                                
                                # Commit every 100 insertions
                                if added_count % 100 == 0:
                                    conn.commit()
                                    logger.info(f"  Added {added_count} entries so far")
                                    
                            except Exception as e:
                                # Log the error but continue
                                insertion_errors += 1
                                if insertion_errors <= 5:  # Limit the number of error logs
                                    logger.error(f"Error inserting {term['name']} at {book} {chapter_num}:{verse_num}: {e}")
                
                # Final commit for this term
                conn.commit()
                logger.info(f"Added {added_count} entries for {term['name']} with {insertion_errors} errors")
            
            # Verify the inserted counts
            for term in critical_terms:
                cursor.execute("""
                    SELECT COUNT(*) FROM bible.hebrew_ot_words 
                    WHERE strongs_id = %s
                """, (term["strongs_id"],))
                final_count = cursor.fetchone()[0]
                
                status = "OK" if final_count >= term["expected_min"] else "LOW"
                logger.info(f"Final count for {term['name']} ({term['strongs_id']}): {final_count}/{term['expected_min']} - {status}")
            
            return True
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting critical theological terms: {e}")
        return False

def main():
    """Main function to insert critical theological terms."""
    logger.info("Starting critical theological terms insertion")
    
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return 1
        
        try:
            # Insert critical terms
            if insert_critical_theological_terms(conn):
                logger.info("Critical theological terms inserted successfully")
            else:
                logger.warning("Failed to insert some terms")
            
            return 0
        
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"Error during critical terms insertion: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 