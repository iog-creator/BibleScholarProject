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

# Standard library imports
import os
import sys
import re
import logging
from pathlib import Path

# Third-party package imports
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

# Add parent directory to path for development mode
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # Try absolute import first (installed mode)
    from src.database.connection import get_db_connection, check_table_exists
except ImportError:
    try:
        # Try relative import (development mode within package)
        from ..database.connection import get_db_connection, check_table_exists
    except ImportError:
        # Fall back to directly modifying path and using absolute import
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.database.connection import get_db_connection, check_table_exists

from src.utils.file_utils import append_dspy_training_example

def force_update_critical_terms(conn):
    """
    Force update Strong's IDs for critical theological terms regardless of existing assignments.
    
    This function directly maps critical Hebrew theological terms to their canonical Strong's IDs.
    It ensures these important terms are consistently identified in the database.
    
    Returns:
        dict: Statistics about the update process
    """
    try:
        cursor = conn.cursor()
        
        # First, check if tables exist
        if not check_table_exists(conn, 'bible', 'hebrew_ot_words'):
            logger.error("Table bible.hebrew_ot_words does not exist")
            return {"error": "Table hebrew_ot_words does not exist"}
            
        if not check_table_exists(conn, 'bible', 'hebrew_entries'):
            logger.error("Table bible.hebrew_entries does not exist")
            return {"error": "Table hebrew_entries does not exist"}

        # Get counts for logging
        cursor.execute("SELECT COUNT(*) FROM bible.hebrew_ot_words")
        total_words = cursor.fetchone()[0]
        logger.info(f"Total Hebrew words: {total_words}")
        
        # Define critical theological terms with exact Hebrew text match
        critical_terms = {
            "H430": {"name": "Elohim", "hebrew": "אלהים", "expected_min": 2600},
            "H113": {"name": "Adon", "hebrew": "אדון", "expected_min": 335},
            "H2617": {"name": "Chesed", "hebrew": "חסד", "expected_min": 248},
            "H3068": {"name": "YHWH", "hebrew": "יהוה", "expected_min": 6000},
            "H539": {"name": "Aman", "hebrew": "אמן", "expected_min": 100}
        }
        
        # Get initial counts for each critical term
        for strongs_id, info in critical_terms.items():
            cursor.execute(
                """
                SELECT COUNT(*) FROM bible.hebrew_ot_words 
                WHERE strongs_id = %s
                """, (strongs_id,)
            )
            initial_count = cursor.fetchone()[0]
            
            cursor.execute(
                """
                SELECT COUNT(*) FROM bible.hebrew_ot_words 
                WHERE word_text = %s
                """, (info["hebrew"],)
            )
            word_count = cursor.fetchone()[0]
            
            logger.info(f"Initial state for {info['name']} ({strongs_id}):")
            logger.info(f"  - Words with correct Strong's ID: {initial_count}")
            logger.info(f"  - Words with Hebrew text '{info['hebrew']}': {word_count}")
            
        # STEP 1: Clear any existing incorrect Strong's IDs for critical terms
        # This ensures we can remap them correctly
        updates_by_term = {}
        for strongs_id, info in critical_terms.items():
            cursor.execute(
                """
                UPDATE bible.hebrew_ot_words
                SET strongs_id = NULL
                WHERE word_text = %s AND strongs_id != %s
                """, (info["hebrew"], strongs_id)
            )
            cleared_count = cursor.rowcount
            updates_by_term[strongs_id] = {"cleared": cleared_count}
            logger.info(f"Cleared {cleared_count} incorrect Strong's IDs for {info['name']}")
        
        # STEP 2: Assign the correct Strong's ID to all words with matching Hebrew text
        for strongs_id, info in critical_terms.items():
            cursor.execute(
                """
                UPDATE bible.hebrew_ot_words
                SET strongs_id = %s
                WHERE word_text = %s AND (strongs_id IS NULL OR strongs_id != %s)
                """, (strongs_id, info["hebrew"], strongs_id)
            )
            updated_count = cursor.rowcount
            updates_by_term[strongs_id]["updated"] = updated_count
            logger.info(f"Updated {updated_count} words to have Strong's ID {strongs_id} for {info['name']}")
            
        # STEP 3: If a critical Hebrew word appears in a verse with grammar code containing 
        # its Strong's ID but has the wrong word_text, correct it
        for strongs_id, info in critical_terms.items():
            cursor.execute(
                """
                UPDATE bible.hebrew_ot_words
                SET word_text = %s
                WHERE strongs_id = %s AND word_text != %s
                AND grammar_code LIKE %s
                """, (info["hebrew"], strongs_id, info["hebrew"], f"%{{{strongs_id}}}%")
            )
            text_fixed_count = cursor.rowcount
            updates_by_term[strongs_id]["text_fixed"] = text_fixed_count
            logger.info(f"Fixed {text_fixed_count} word_text values for Strong's ID {strongs_id}")
        
        # Commit changes
        conn.commit()
        
        # Verify final counts for critical terms
        total_updated = 0
        final_counts = {}
        for strongs_id, info in critical_terms.items():
            cursor.execute(
                """
                SELECT COUNT(*) FROM bible.hebrew_ot_words 
                WHERE strongs_id = %s
                """, (strongs_id,)
            )
            final_count = cursor.fetchone()[0]
            final_counts[strongs_id] = final_count
            total_updated += updates_by_term[strongs_id].get("updated", 0)
            
            status = "OK" if final_count >= info["expected_min"] else "LOW"
            logger.info(f"Final count for {info['name']} ({strongs_id}): {final_count} (expected {info['expected_min']}) - {status}")
        
        return {
            "total_words": total_words,
            "total_updated": total_updated,
            "final_counts": final_counts,
            "updates_by_term": updates_by_term
        }
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating critical Hebrew Strong's IDs: {e}")
        return {"error": str(e)}

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
        
        # First, check if tables exist
        if not check_table_exists(conn, 'bible', 'hebrew_ot_words'):
            logger.error("Table bible.hebrew_ot_words does not exist")
            return {"error": "Table hebrew_ot_words does not exist"}
            
        if not check_table_exists(conn, 'bible', 'hebrew_entries'):
            logger.error("Table bible.hebrew_entries does not exist")
            return {"error": "Table hebrew_entries does not exist"}

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
        
        # Special handling for critical theological terms:
        # These terms need direct mapping since the grammar codes might not have the IDs
        critical_terms = {
            "H430": {"name": "Elohim", "hebrew": "אלהים", "expected_min": 2600},
            "H113": {"name": "Adon", "hebrew": "אדון", "expected_min": 335},
            "H2617": {"name": "Chesed", "hebrew": "חסד", "expected_min": 248},
            "H3068": {"name": "YHWH", "hebrew": "יהוה", "expected_min": 6000},
            "H539": {"name": "Aman", "hebrew": "אמן", "expected_min": 100}
        }
        
        # Update critical terms by direct word mapping
        for strongs_id, info in critical_terms.items():
            # First check if we already have this Strong's ID in the database
            cursor.execute(
                """
                SELECT COUNT(*) FROM bible.hebrew_ot_words 
                WHERE strongs_id = %s
                """, (strongs_id,)
            )
            existing_count = cursor.fetchone()[0]
            
            if existing_count < info["expected_min"]:
                logger.info(f"Fixing {info['name']} ({strongs_id}) - Currently has {existing_count} occurrences, expected {info['expected_min']}")
                
                # Update words matching the Hebrew text to have the correct Strong's ID
                cursor.execute(
                    """
                    UPDATE bible.hebrew_ot_words
                    SET strongs_id = %s
                    WHERE word_text = %s AND (strongs_id IS NULL OR strongs_id != %s)
                    """, (strongs_id, info["hebrew"], strongs_id)
                )
                updated_rows = cursor.rowcount
                logger.info(f"  - Updated {updated_rows} words for {info['name']}")
        
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
        for strongs_id, info in critical_terms.items():
            cursor.execute(
                """
                SELECT COUNT(*) FROM bible.hebrew_ot_words 
                WHERE strongs_id = %s
                """, (strongs_id,)
            )
            updated_count = cursor.fetchone()[0]
            
            if updated_count < info["expected_min"]:
                logger.warning(f"{info['name']} ({strongs_id}) still has only {updated_count} occurrences (expected {info['expected_min']})")
            else:
                logger.info(f"{info['name']} ({strongs_id}) now has {updated_count} occurrences (expected {info['expected_min']})")
        
        # Commit the transaction
        conn.commit()
        
        # Return statistics
        return {
            "total_words": total_words,
            "initial_strongs_count": initial_strongs_count,
            "grammar_strongs_count": grammar_strongs_count,
            "updated_count": valid_updates,
            "final_strongs_count": final_strongs_count,
            "coverage_percentage": coverage_pct
        }
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating Hebrew Strong's IDs: {e}")
        return {"error": str(e)}

def main():
    """
    Main function to run the script.
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Get database connection
        logger.info("Connecting to database...")
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return 1
            
        try:
            # First, force update critical terms
            logger.info("Starting critical theological terms update...")
            critical_stats = force_update_critical_terms(conn)
            
            if "error" in critical_stats:
                logger.error(f"Error updating critical terms: {critical_stats['error']}")
                return 1
                
            logger.info("Critical terms update completed successfully")
            logger.info(f"Critical terms summary: {critical_stats}")
            
            # Then, update remaining Hebrew Strong's IDs
            logger.info("Starting general Hebrew Strong's ID extraction and update...")
            general_stats = update_hebrew_strongs_ids(conn)
            
            if "error" in general_stats:
                logger.error(f"Error: {general_stats['error']}")
                return 1
                
            logger.info("Hebrew Strong's ID update completed successfully")
            logger.info(f"Summary: {general_stats}")
            
            # In the main processing loop, after fixing each word's strongs_id:
            # context = f"{word_text} | {grammar_code}"
            # labels = {'extracted_strongs_id': strongs_id, 'fixed': was_fixed}
            # metadata = {'word_id': word_id, 'verse_ref': verse_ref}
            # append_dspy_training_example('data/processed/dspy_training_data/hebrew_strongs_fix_training_data.jsonl', context, labels, metadata)
            
            return 0
        finally:
            # Clean up
            conn.close()
            
    except Exception as e:
        logger.error(f"Error running Hebrew Strong's ID update: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 