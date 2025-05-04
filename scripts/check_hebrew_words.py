#!/usr/bin/env python3
"""
Script to check Hebrew words in the BibleScholarProject database.
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
logger = logging.getLogger('check_hebrew_words')

def check_critical_hebrew_words(conn):
    """Check for critical Hebrew theological terms in the database."""
    critical_terms = {
        "אלהים": {"strongs_id": "H430", "name": "Elohim", "expected_min": 2600},
        "יהוה": {"strongs_id": "H3068", "name": "YHWH", "expected_min": 6000},
        "אדון": {"strongs_id": "H113", "name": "Adon", "expected_min": 335},
        "חסד": {"strongs_id": "H2617", "name": "Chesed", "expected_min": 248},
        "אמן": {"strongs_id": "H539", "name": "Aman", "expected_min": 100}
    }
    
    try:
        with conn.cursor() as cursor:
            # Get counts for each Hebrew word
            placeholders = ", ".join(["%s" for _ in critical_terms])
            cursor.execute(f"""
                SELECT word_text, COUNT(*) as count
                FROM bible.hebrew_ot_words
                WHERE word_text IN ({placeholders})
                GROUP BY word_text
            """, list(critical_terms.keys()))
            
            # Store the results
            results = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Display results
            logger.info("Critical Hebrew theological terms in hebrew_ot_words:")
            for word, info in critical_terms.items():
                count = results.get(word, 0)
                status = "OK" if count >= info["expected_min"] else "LOW"
                logger.info(f"  {info['name']} ({word} / {info['strongs_id']}): {count} occurrences (expected {info['expected_min']}) - {status}")
            
            # Check strongs_id mappings
            logger.info("\nStrong's ID mappings:")
            for word, info in critical_terms.items():
                # Count words with this word_text but no strongs_id
                cursor.execute("""
                    SELECT COUNT(*) FROM bible.hebrew_ot_words
                    WHERE word_text = %s AND strongs_id IS NULL
                """, (word,))
                missing_strongs = cursor.fetchone()[0]
                
                # Count words with this word_text and matching strongs_id
                cursor.execute("""
                    SELECT COUNT(*) FROM bible.hebrew_ot_words
                    WHERE word_text = %s AND strongs_id = %s
                """, (word, info["strongs_id"]))
                correct_strongs = cursor.fetchone()[0]
                
                # Count words with this word_text but wrong strongs_id
                cursor.execute("""
                    SELECT COUNT(*) FROM bible.hebrew_ot_words
                    WHERE word_text = %s AND strongs_id IS NOT NULL AND strongs_id != %s
                """, (word, info["strongs_id"]))
                wrong_strongs = cursor.fetchone()[0]
                
                total = missing_strongs + correct_strongs + wrong_strongs
                logger.info(f"  {info['name']} ({word}):")
                logger.info(f"    - Total occurrences: {total}")
                logger.info(f"    - Mapped to {info['strongs_id']}: {correct_strongs}")
                logger.info(f"    - Missing strongs_id: {missing_strongs}")
                logger.info(f"    - Wrong strongs_id: {wrong_strongs}")
                
                if total > 0 and correct_strongs == 0:
                    logger.warning(f"  WARNING: {info['name']} is present but not correctly mapped to {info['strongs_id']}")
                elif total > 0 and correct_strongs < total:
                    logger.warning(f"  WARNING: {info['name']} is partially mapped to {info['strongs_id']} ({correct_strongs}/{total})")
    
    except Exception as e:
        logger.error(f"Error checking critical Hebrew words: {e}")

def main():
    """Main function to check Hebrew words."""
    logger.info("Starting Hebrew words check")
    
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return 1
        
        try:
            # Check critical Hebrew words
            check_critical_hebrew_words(conn)
            
            logger.info("Hebrew words check completed successfully")
            return 0
        
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"Error during Hebrew words check: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 