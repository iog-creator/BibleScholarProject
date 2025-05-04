#!/usr/bin/env python3
"""
Script to update critical theological terms directly in the database.

This script updates existing Hebrew words to ensure they have the correct Strong's ID
mappings for important theological terms.
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
logger = logging.getLogger('update_critical_terms')

def update_critical_theological_terms(conn):
    """Update existing critical theological terms in the hebrew_ot_words table."""
    
    # Critical terms with their Strong's IDs and expected Hebrew text
    critical_terms = [
        {
            "strongs_id": "H430", 
            "name": "Elohim", 
            "hebrew": "אלהים",
            "expected_min": 2600
        },
        {
            "strongs_id": "H113", 
            "name": "Adon", 
            "hebrew": "אדון",
            "expected_min": 335
        },
        {
            "strongs_id": "H2617", 
            "name": "Chesed", 
            "hebrew": "חסד",
            "expected_min": 248
        },
        {
            "strongs_id": "H3068", 
            "name": "YHWH", 
            "hebrew": "יהוה",
            "expected_min": 6000
        },
        {
            "strongs_id": "H539", 
            "name": "Aman", 
            "hebrew": "אמן",
            "expected_min": 100
        }
    ]
    
    try:
        with conn.cursor() as cursor:
            # Check initial term counts
            logger.info("Checking initial theological term counts:")
            initial_counts = {}
            for term in critical_terms:
                cursor.execute("""
                    SELECT COUNT(*) FROM bible.hebrew_ot_words
                    WHERE strongs_id = %s
                """, (term["strongs_id"],))
                count = cursor.fetchone()[0]
                initial_counts[term["strongs_id"]] = count
                status = "OK" if count >= term["expected_min"] else "LOW"
                logger.info(f"  {term['name']} ({term['strongs_id']}): {count}/{term['expected_min']} - {status}")

                # Also check words matching the Hebrew text
                cursor.execute("""
                    SELECT COUNT(*) FROM bible.hebrew_ot_words
                    WHERE word_text = %s
                """, (term["hebrew"],))
                word_text_count = cursor.fetchone()[0]
                logger.info(f"  Words with text '{term['hebrew']}': {word_text_count}")

            # Process each term
            updates = {}
            for term in critical_terms:
                # Check if we need to update this term
                if initial_counts[term["strongs_id"]] >= term["expected_min"]:
                    logger.info(f"No need to update {term['name']} ({term['strongs_id']}), already have sufficient count")
                    updates[term["strongs_id"]] = {"updated": 0, "matched": initial_counts[term["strongs_id"]]}
                    continue

                # First update any words with matching Hebrew text but wrong or missing Strong's ID
                cursor.execute("""
                    UPDATE bible.hebrew_ot_words
                    SET strongs_id = %s
                    WHERE word_text = %s AND (strongs_id IS NULL OR strongs_id != %s)
                """, (term["strongs_id"], term["hebrew"], term["strongs_id"]))
                text_updated = cursor.rowcount
                
                # Now check if we have cases where the Strong's ID is in the grammar_code but not set in strongs_id
                cursor.execute("""
                    UPDATE bible.hebrew_ot_words
                    SET strongs_id = %s
                    WHERE grammar_code LIKE %s AND (strongs_id IS NULL OR strongs_id != %s)
                """, (term["strongs_id"], f"%{{{term['strongs_id']}}}%", term["strongs_id"]))
                grammar_updated = cursor.rowcount
                
                # Now fix any cases where the word has the correct Strong's ID but wrong text
                cursor.execute("""
                    UPDATE bible.hebrew_ot_words
                    SET word_text = %s
                    WHERE strongs_id = %s AND word_text != %s
                    LIMIT 100  -- Limit updates to prevent over-correction
                """, (term["hebrew"], term["strongs_id"], term["hebrew"]))
                word_fixed = cursor.rowcount
                
                total_updated = text_updated + grammar_updated + word_fixed
                updates[term["strongs_id"]] = {
                    "updated_by_text": text_updated,
                    "updated_by_grammar": grammar_updated,
                    "word_text_fixed": word_fixed,
                    "total_updated": total_updated
                }
                
                logger.info(f"Updated {term['name']} ({term['strongs_id']}):")
                logger.info(f"  - Words updated by text match: {text_updated}")
                logger.info(f"  - Words updated by grammar code: {grammar_updated}")
                logger.info(f"  - Words with text fixed: {word_fixed}")
                logger.info(f"  - Total updates: {total_updated}")
            
            # Commit changes
            conn.commit()
            
            # Check final counts
            logger.info("Final theological term counts after updates:")
            for term in critical_terms:
                cursor.execute("""
                    SELECT COUNT(*) FROM bible.hebrew_ot_words
                    WHERE strongs_id = %s
                """, (term["strongs_id"],))
                final_count = cursor.fetchone()[0]
                updates[term["strongs_id"]]["final_count"] = final_count
                
                status = "OK" if final_count >= term["expected_min"] else "LOW"
                logger.info(f"  {term['name']} ({term['strongs_id']}): {final_count}/{term['expected_min']} - {status}")
            
            return {
                "initial_counts": initial_counts,
                "updates": updates
            }
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating critical theological terms: {e}")
        return {"error": str(e)}

def main():
    """Main function to update critical theological terms."""
    logger.info("Starting critical theological terms update process")
    
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return 1
        
        try:
            # Update critical terms
            results = update_critical_theological_terms(conn)
            if "error" in results:
                logger.error(f"Failed to update critical terms: {results['error']}")
                return 1
                
            logger.info("Critical theological terms update completed successfully")
            
            # Summary
            logger.info("Summary of updates:")
            for sid, data in results["updates"].items():
                initial = results["initial_counts"][sid]
                final = data.get("final_count", initial)
                updated = data.get("total_updated", 0)
                logger.info(f"  {sid}: {initial} → {final} (+{updated})")
            
            return 0
        
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"Error during critical terms update: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 