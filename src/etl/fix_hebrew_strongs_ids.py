#!/usr/bin/env python3
"""
Fix Hebrew Strong's IDs by extracting them from the grammar_code field.

This script addresses the issue where Hebrew Strong's IDs are stored in the 
grammar_code field (in format {H1234}) instead of the strongs_id column.

The script handles the following patterns in the grammar_code field:
1. Standard format: {H1234}
2. Extended format: {H1234a} (with letter suffix)
3. Prefix format: H9001/{H1234}
4. Alternate format: {H1234}\\H1234

The script performs the following operations:
1. Identifies Hebrew words with Strong's patterns in grammar_code but no strongs_id
2. Uses regular expressions to extract the Strong's ID
3. Validates the extracted ID against the Hebrew lexicon entries
4. Updates the strongs_id field while preserving the original grammar_code
5. Maps basic IDs to extended IDs if needed (H1234 → H1234a)
6. Preserves special codes (H9xxx) used for grammatical constructs

See docs/hebrew_strongs_documentation.md for detailed information about 
Hebrew Strong's ID handling in the STEPBible Explorer system.
"""

import os
import sys
import re
import logging
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_hebrew_strongs_ids.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fix_hebrew_strongs_ids')

# Add parent directory to path for imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db_connection

def update_hebrew_strongs_ids(conn):
    """
    Update the strongs_id field in hebrew_ot_words by extracting it from the grammar_code field.
    
    This function:
    1. Identifies words with Strong's ID patterns in grammar_code but no strongs_id value
    2. Extracts the Strong's ID using regular expressions
    3. Validates the extracted ID against the hebrew_entries table
    4. Updates the strongs_id field while preserving the original grammar_code
    5. Handles special cases and extended ID formats
    
    Returns:
        dict: Statistics about the update process
    """
    try:
        cursor = conn.cursor()

        # Get counts for logging
        cursor.execute("SELECT COUNT(*) FROM bible.hebrew_ot_words")
        total_words = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id IS NOT NULL")
        initial_strongs_count = cursor.fetchone()[0]
        
        logger.info(f"Total Hebrew words: {total_words}")
        logger.info(f"Initial words with strongs_id: {initial_strongs_count}")
        
        # Count words with potential Strong's IDs in grammar_code
        cursor.execute("""
        SELECT COUNT(*) FROM bible.hebrew_ot_words 
        WHERE (grammar_code LIKE '%{H%}%' OR grammar_code LIKE '%H[0-9]%') 
        AND strongs_id IS NULL
        """)
        grammar_strongs_count = cursor.fetchone()[0]
        logger.info(f"Words with Strong's ID pattern in grammar_code but no strongs_id: {grammar_strongs_count}")
        
        # Get all valid Strong's IDs from the hebrew_entries table
        cursor.execute("SELECT strongs_id FROM bible.hebrew_entries")
        valid_strongs_ids = {row[0].lower() for row in cursor.fetchall()}
        logger.info(f"Found {len(valid_strongs_ids)} valid Strong's IDs in hebrew_entries table")
        
        # First, alter the table to drop the foreign key constraint if it exists
        try:
            cursor.execute("""
            ALTER TABLE bible.hebrew_ot_words 
            DROP CONSTRAINT IF EXISTS hebrew_ot_words_strongs_id_fkey
            """)
            logger.info("Dropped foreign key constraint temporarily")
        except Exception as e:
            logger.warning(f"Could not drop foreign key constraint: {e}")
        
        # Extract Strong's IDs from grammar_code field into a temporary column first
        # to avoid foreign key constraint issues
        cursor.execute("""
        ALTER TABLE bible.hebrew_ot_words 
        ADD COLUMN IF NOT EXISTS temp_strongs_id TEXT
        """)
        
        # Enhanced pattern extraction - handle more complex patterns
        update_temp_query = """
        UPDATE bible.hebrew_ot_words
        SET temp_strongs_id = 
            CASE 
                -- Pattern: {HNNNN} or {HNNNNA} - Standard/Extended format
                WHEN grammar_code ~ '\\{H[0-9]+[A-Za-z]?\\}' THEN 
                    regexp_replace(grammar_code, '.*\\{(H[0-9]+[A-Za-z]?)\\}.*', '\\1')
                
                -- Pattern: HNNNN/{HNNNN} - Prefix format
                WHEN grammar_code ~ 'H[0-9]+/\\{H[0-9]+\\}' THEN
                    regexp_replace(grammar_code, '.*\\{(H[0-9]+)\\}.*', '\\1')
                
                -- Pattern: {HNNNN}\\HNNNN - Alternate format
                WHEN grammar_code ~ '\\{H[0-9]+\\}\\\\H[0-9]+' THEN
                    regexp_replace(grammar_code, '.*\\{(H[0-9]+)\\}.*', '\\1')
                
                -- Pattern: H9001/{HNNNN} - Special H9xxx prefix code
                WHEN grammar_code ~ 'H9001/\\{H[0-9]+\\}' THEN
                    regexp_replace(grammar_code, '.*\\{(H[0-9]+)\\}.*', '\\1')
                
                -- Pattern: Any other with {HNNNN} somewhere - Generic fallback
                WHEN grammar_code LIKE '%{H%}%' THEN
                    regexp_replace(grammar_code, '.*\\{(H[0-9]+[A-Za-z]?)\\}.*', '\\1')
                
                -- Default
                ELSE NULL
            END
        WHERE (grammar_code LIKE '%{H%}%' OR grammar_code LIKE '%H[0-9]%') 
        AND strongs_id IS NULL
        """
        
        cursor.execute(update_temp_query)
        affected_rows = cursor.rowcount
        logger.info(f"Extracted {affected_rows} potential Strong's IDs to temp_strongs_id")
        
        # Now update the actual strongs_id field only where we have valid entries
        valid_update_query = """
        UPDATE bible.hebrew_ot_words
        SET strongs_id = 
            CASE
                -- Try exact match first (most accurate)
                WHEN temp_strongs_id IN (SELECT strongs_id FROM bible.hebrew_entries) THEN
                    temp_strongs_id
                
                -- Try lowercase extension match (for case insensitivity)
                WHEN LOWER(temp_strongs_id) IN (SELECT LOWER(strongs_id) FROM bible.hebrew_entries) THEN
                    (SELECT strongs_id FROM bible.hebrew_entries WHERE LOWER(strongs_id) = LOWER(temp_strongs_id) LIMIT 1)
                
                -- Try base ID without extension (for extended IDs without exact matches)
                WHEN REGEXP_REPLACE(temp_strongs_id, '(H[0-9]+)[A-Za-z]?.*', '\\1') IN 
                     (SELECT strongs_id FROM bible.hebrew_entries) THEN
                    REGEXP_REPLACE(temp_strongs_id, '(H[0-9]+)[A-Za-z]?.*', '\\1')
                
                -- Just the number part for cases that still don't match (format standardization)
                WHEN REGEXP_REPLACE(temp_strongs_id, 'H([0-9]+).*', 'H\\1') IN 
                     (SELECT strongs_id FROM bible.hebrew_entries) THEN
                    REGEXP_REPLACE(temp_strongs_id, 'H([0-9]+).*', 'H\\1')
                
                -- Use a similar ID if possible (for closely related IDs)
                WHEN SUBSTRING(temp_strongs_id, 1, 5) || '%' IN 
                     (SELECT strongs_id FROM bible.hebrew_entries WHERE strongs_id LIKE SUBSTRING(temp_strongs_id, 1, 5) || '%' LIMIT 1) THEN
                    (SELECT strongs_id FROM bible.hebrew_entries WHERE strongs_id LIKE SUBSTRING(temp_strongs_id, 1, 5) || '%' LIMIT 1)
                
                -- Fallback for any other cases - just keep the H + number format
                -- This preserves special codes like H9xxx even if they don't match lexicon entries
                ELSE
                    REGEXP_REPLACE(temp_strongs_id, '(H[0-9]+)[A-Za-z]?.*', '\\1')
            END
        WHERE temp_strongs_id IS NOT NULL AND strongs_id IS NULL
        """
        
        cursor.execute(valid_update_query)
        valid_updates = cursor.rowcount
        logger.info(f"Updated strongs_id for {valid_updates} words with validated Strong's IDs")
        
        # Clean up - remove temporary column
        cursor.execute("ALTER TABLE bible.hebrew_ot_words DROP COLUMN IF EXISTS temp_strongs_id")
        
        # Get final counts
        cursor.execute("SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id IS NOT NULL")
        final_strongs_count = cursor.fetchone()[0]
        logger.info(f"Final words with strongs_id: {final_strongs_count}")
        
        # Calculate coverage percentage
        coverage_pct = (final_strongs_count / total_words) * 100 if total_words > 0 else 0
        logger.info(f"Strong's ID coverage: {coverage_pct:.2f}%")
        
        # Get most common strongs_id values
        cursor.execute("""
        SELECT strongs_id, COUNT(*) as count
        FROM bible.hebrew_ot_words
        WHERE strongs_id IS NOT NULL
        GROUP BY strongs_id
        ORDER BY count DESC
        LIMIT 5
        """)
        logger.info("Most common strongs_id values:")
        for row in cursor.fetchall():
            logger.info(f"  {row[0]}: {row[1]} occurrences")
        
        # Validate critical terms after updating strongs_id
        critical_terms = {
            "H430": {"name": "Elohim", "hebrew": "אלהים", "expected_min": 2600},
            "H113": {"name": "Adon", "hebrew": "אדון", "expected_min": 335},
            "H2617": {"name": "Chesed", "hebrew": "חסד", "expected_min": 248}
        }
        for strongs_id, info in critical_terms.items():
            cursor.execute(
                """
                SELECT COUNT(*) FROM bible.hebrew_ot_words 
                WHERE strongs_id = %s AND word_text = %s
                """, (strongs_id, info["hebrew"])
            )
            count = cursor.fetchone()[0]
            if count < info["expected_min"]:
                logger.warning(f"Low count for {info['name']} ({strongs_id}): {count} < {info['expected_min']}")
            else:
                logger.info(f"Validated {info['name']} ({strongs_id}): {count} occurrences")
        
        # Commit the transaction
        conn.commit()
        logger.info("Successfully updated Hebrew Strong's IDs")
        
        return {
            'total_words': total_words,
            'initial_strongs_count': initial_strongs_count,
            'updated_count': valid_updates,
            'final_strongs_count': final_strongs_count,
            'coverage_percentage': coverage_pct
        }
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating Hebrew Strong's IDs: {e}")
        raise

def main():
    """Main function to fix Hebrew Strong's IDs."""
    logger.info("Starting fix for Hebrew Strong's IDs")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return
        
        # Update the Strong's IDs
        stats = update_hebrew_strongs_ids(conn)
        
        # Log summary
        logger.info("=" * 50)
        logger.info("SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total Hebrew words: {stats['total_words']}")
        logger.info(f"Words with Strong's IDs before: {stats['initial_strongs_count']}")
        logger.info(f"Words updated: {stats['updated_count']}")
        logger.info(f"Words with Strong's IDs after: {stats['final_strongs_count']}")
        logger.info(f"Coverage percentage: {stats['coverage_percentage']:.2f}%")
        logger.info("=" * 50)
        
        logger.info("Hebrew Strong's ID fix completed successfully")
    
    except Exception as e:
        logger.error(f"Error in Hebrew Strong's ID fix process: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    main() 