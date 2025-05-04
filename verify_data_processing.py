<<<<<<< HEAD
#!/usr/bin/env python3
"""
Script to verify data processing steps and check data integrity.
"""

import os
import sys
import logging
import traceback
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data_verification.log')
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Create and return a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'bible_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def check_data_counts():
    """
    Check counts of records in key tables to verify data integrity.
    """
    conn = None
    try:
        logger.info("Connecting to database...")
        conn = get_db_connection()
        
        if conn is None:
            logger.error("Failed to connect to database")
            return False
            
        logger.info("Checking data counts...")
        tables = [
            ('hebrew_entries', 'Hebrew lexicon entries'),
            ('greek_entries', 'Greek lexicon entries'),
            ('hebrew_ot_words', 'Hebrew OT tagged words'),
            ('greek_nt_words', 'Greek NT tagged words'),
            ('verses', 'Bible verses'),
            ('hebrew_morphology_codes', 'Hebrew morphology codes'),
            ('greek_morphology_codes', 'Greek morphology codes'),
            ('proper_names', 'Proper names'),
            ('word_relationships', 'Word relationships')
        ]
        
        with conn.cursor() as cur:
            for table, description in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM bible.{table}")
                    count = cur.fetchone()[0]
                    if count > 0:
                        logger.info(f"[OK] {description}: {count:,} records")
                    else:
                        logger.warning(f"✗ {description}: No records found")
                except Exception as e:
                    logger.error(f"Error checking {description}: {e}")
                    
        # Check for specific expected counts
        expected_counts = [
            ('hebrew_entries', 8000, 'Hebrew lexicon entries'),
            ('greek_entries', 5000, 'Greek lexicon entries'),
            ('verses', 31000, 'Bible verses'),
        ]
        
        with conn.cursor() as cur:
            for table, min_expected, description in expected_counts:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM bible.{table}")
                    count = cur.fetchone()[0]
                    if count >= min_expected:
                        logger.info(f"[OK] {description} count meets minimum expectation: {count:,} ≥ {min_expected:,}")
                    else:
                        logger.warning(f"✗ {description} count below minimum expectation: {count:,} < {min_expected:,}")
                except Exception as e:
                    logger.error(f"Error checking expected count for {description}: {e}")
        
        # Check for integrity between related tables
        integrity_checks = [
            ('hebrew_ot_words', 'strongs_id', 'hebrew_entries', 'strongs_id', 'Hebrew words reference valid lexicon entries'),
            ('greek_nt_words', 'strongs_id', 'greek_entries', 'strongs_id', 'Greek words reference valid lexicon entries'),
        ]
        
        with conn.cursor() as cur:
            for source_table, source_column, target_table, target_column, description in integrity_checks:
                try:
                    # Count records in source table with foreign keys that don't exist in target table
                    # Exclude NULL values in source column
                    cur.execute(f"""
                        SELECT COUNT(*) FROM bible.{source_table} src
                        WHERE src.{source_column} IS NOT NULL 
                        AND NOT EXISTS (
                            SELECT 1 FROM bible.{target_table} tgt
                            WHERE tgt.{target_column} = src.{source_column}
                        )
                    """)
                    invalid_count = cur.fetchone()[0]
                    if invalid_count == 0:
                        logger.info(f"[OK] {description}")
                    else:
                        logger.warning(f"✗ {description}: {invalid_count:,} invalid references")
                        
                        # Sample some invalid references
                        cur.execute(f"""
                            SELECT src.{source_column} FROM bible.{source_table} src
                            WHERE src.{source_column} IS NOT NULL 
                            AND NOT EXISTS (
                                SELECT 1 FROM bible.{target_table} tgt
                                WHERE tgt.{target_column} = src.{source_column}
                            )
                            LIMIT 5
                        """)
                        invalid_samples = [row[0] for row in cur.fetchall()]
                        logger.warning(f"  Sample invalid references: {', '.join(invalid_samples)}")
                except Exception as e:
                    logger.error(f"Error checking {description}: {e}")
                    
        return True
    except Exception as e:
        logger.error(f"Error checking data counts: {e}")
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

def check_step_data_files():
    """
    Check if STEP Bible data files are present and accessible.
    """
    logger.info("Checking STEP Bible data files...")
    
    step_data_dir = "STEPBible-Data"
    if not os.path.exists(step_data_dir):
        logger.error(f"STEP Bible data directory not found: {step_data_dir}")
        return False
        
    # Check for key data files
    key_files = [
        ("Lexicons/TBESH - Translators Brief lexicon of Extended Strongs for Hebrew - STEPBible.org CC BY.txt", "Hebrew lexicon"),
        ("Lexicons/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt", "Greek lexicon"),
        ("TEHMC - Translators Expansion of Hebrew Morphology Codes - STEPBible.org CC BY.txt", "Hebrew morphology codes"),
        ("TEGMC - Translators Expansion of Greek Morphhology Codes - STEPBible.org CC BY.txt", "Greek morphology codes"),
        ("Translators Amalgamated OT+NT/TAGNT Mat-Jhn - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt", "Greek NT (Gospels)"),
        ("Translators Amalgamated OT+NT/TAGNT Act-Rev - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt", "Greek NT (Acts-Revelation)"),
        ("Translators Amalgamated OT+NT/TAHOT Gen-Deu - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt", "Hebrew OT (Torah)"),
        ("Translators Amalgamated OT+NT/TAHOT Jos-Est - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt", "Hebrew OT (Historical Books)"),
        ("Translators Amalgamated OT+NT/TAHOT Job-Sng - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt", "Hebrew OT (Wisdom Literature)"),
        ("Translators Amalgamated OT+NT/TAHOT Isa-Mal - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt", "Hebrew OT (Prophets)")
    ]
    
    missing_files = []
    for file_path, description in key_files:
        full_path = os.path.join(step_data_dir, file_path)
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path) / (1024 * 1024)  # Size in MB
            logger.info(f"[OK] Found {description}: {full_path} ({file_size:.2f} MB)")
        else:
            logger.warning(f"✗ Missing {description}: {full_path}")
            missing_files.append((file_path, description))
            
    if missing_files:
        logger.warning(f"Missing {len(missing_files)} key data files. Run the download script to obtain them.")
        return False
    else:
        logger.info("All key STEP Bible data files found")
        return True

def main():
    """
    Run all verification checks.
    """
    logger.info("Starting data verification...")
    
    # Check STEP Bible data files
    step_files_ok = check_step_data_files()
    
    # Check database data counts
    db_counts_ok = check_data_counts()
    
    # Summarize results
    logger.info("\n===== VERIFICATION SUMMARY =====")
    logger.info(f"STEP Bible data files: {'OK' if step_files_ok else 'ISSUES FOUND'}")
    logger.info(f"Database data counts: {'OK' if db_counts_ok else 'ISSUES FOUND'}")
    
    if step_files_ok and db_counts_ok:
        logger.info("All verification checks passed")
        return 0
    else:
        logger.warning("Some verification checks failed - see log for details")
        return 1

if __name__ == "__main__":
=======
#!/usr/bin/env python3
"""
Script to verify data processing steps and check data integrity.
"""

import os
import sys
import logging
import traceback
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data_verification.log')
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Create and return a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'bible_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def check_data_counts():
    """
    Check counts of records in key tables to verify data integrity.
    """
    conn = None
    try:
        logger.info("Connecting to database...")
        conn = get_db_connection()
        
        if conn is None:
            logger.error("Failed to connect to database")
            return False
            
        logger.info("Checking data counts...")
        tables = [
            ('hebrew_entries', 'Hebrew lexicon entries'),
            ('greek_entries', 'Greek lexicon entries'),
            ('hebrew_ot_words', 'Hebrew OT tagged words'),
            ('greek_nt_words', 'Greek NT tagged words'),
            ('verses', 'Bible verses'),
            ('hebrew_morphology_codes', 'Hebrew morphology codes'),
            ('greek_morphology_codes', 'Greek morphology codes'),
            ('proper_names', 'Proper names'),
            ('word_relationships', 'Word relationships')
        ]
        
        with conn.cursor() as cur:
            for table, description in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM bible.{table}")
                    count = cur.fetchone()[0]
                    if count > 0:
                        logger.info(f"[OK] {description}: {count:,} records")
                    else:
                        logger.warning(f"✗ {description}: No records found")
                except Exception as e:
                    logger.error(f"Error checking {description}: {e}")
                    
        # Check for specific expected counts
        expected_counts = [
            ('hebrew_entries', 8000, 'Hebrew lexicon entries'),
            ('greek_entries', 5000, 'Greek lexicon entries'),
            ('verses', 31000, 'Bible verses'),
        ]
        
        with conn.cursor() as cur:
            for table, min_expected, description in expected_counts:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM bible.{table}")
                    count = cur.fetchone()[0]
                    if count >= min_expected:
                        logger.info(f"[OK] {description} count meets minimum expectation: {count:,} ≥ {min_expected:,}")
                    else:
                        logger.warning(f"✗ {description} count below minimum expectation: {count:,} < {min_expected:,}")
                except Exception as e:
                    logger.error(f"Error checking expected count for {description}: {e}")
        
        # Check for integrity between related tables
        integrity_checks = [
            ('hebrew_ot_words', 'strongs_id', 'hebrew_entries', 'strongs_id', 'Hebrew words reference valid lexicon entries'),
            ('greek_nt_words', 'strongs_id', 'greek_entries', 'strongs_id', 'Greek words reference valid lexicon entries'),
        ]
        
        with conn.cursor() as cur:
            for source_table, source_column, target_table, target_column, description in integrity_checks:
                try:
                    # Count records in source table with foreign keys that don't exist in target table
                    # Exclude NULL values in source column
                    cur.execute(f"""
                        SELECT COUNT(*) FROM bible.{source_table} src
                        WHERE src.{source_column} IS NOT NULL 
                        AND NOT EXISTS (
                            SELECT 1 FROM bible.{target_table} tgt
                            WHERE tgt.{target_column} = src.{source_column}
                        )
                    """)
                    invalid_count = cur.fetchone()[0]
                    if invalid_count == 0:
                        logger.info(f"[OK] {description}")
                    else:
                        logger.warning(f"✗ {description}: {invalid_count:,} invalid references")
                        
                        # Sample some invalid references
                        cur.execute(f"""
                            SELECT src.{source_column} FROM bible.{source_table} src
                            WHERE src.{source_column} IS NOT NULL 
                            AND NOT EXISTS (
                                SELECT 1 FROM bible.{target_table} tgt
                                WHERE tgt.{target_column} = src.{source_column}
                            )
                            LIMIT 5
                        """)
                        invalid_samples = [row[0] for row in cur.fetchall()]
                        logger.warning(f"  Sample invalid references: {', '.join(invalid_samples)}")
                except Exception as e:
                    logger.error(f"Error checking {description}: {e}")
                    
        return True
    except Exception as e:
        logger.error(f"Error checking data counts: {e}")
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

def check_step_data_files():
    """
    Check if STEP Bible data files are present and accessible.
    """
    logger.info("Checking STEP Bible data files...")
    
    step_data_dir = "STEPBible-Data"
    if not os.path.exists(step_data_dir):
        logger.error(f"STEP Bible data directory not found: {step_data_dir}")
        return False
        
    # Check for key data files
    key_files = [
        ("Lexicons/TBESH - Translators Brief lexicon of Extended Strongs for Hebrew - STEPBible.org CC BY.txt", "Hebrew lexicon"),
        ("Lexicons/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt", "Greek lexicon"),
        ("TEHMC - Translators Expansion of Hebrew Morphology Codes - STEPBible.org CC BY.txt", "Hebrew morphology codes"),
        ("TEGMC - Translators Expansion of Greek Morphhology Codes - STEPBible.org CC BY.txt", "Greek morphology codes"),
        ("Translators Amalgamated OT+NT/TAGNT Mat-Jhn - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt", "Greek NT (Gospels)"),
        ("Translators Amalgamated OT+NT/TAGNT Act-Rev - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt", "Greek NT (Acts-Revelation)"),
        ("Translators Amalgamated OT+NT/TAHOT Gen-Deu - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt", "Hebrew OT (Torah)"),
        ("Translators Amalgamated OT+NT/TAHOT Jos-Est - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt", "Hebrew OT (Historical Books)"),
        ("Translators Amalgamated OT+NT/TAHOT Job-Sng - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt", "Hebrew OT (Wisdom Literature)"),
        ("Translators Amalgamated OT+NT/TAHOT Isa-Mal - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt", "Hebrew OT (Prophets)")
    ]
    
    missing_files = []
    for file_path, description in key_files:
        full_path = os.path.join(step_data_dir, file_path)
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path) / (1024 * 1024)  # Size in MB
            logger.info(f"[OK] Found {description}: {full_path} ({file_size:.2f} MB)")
        else:
            logger.warning(f"✗ Missing {description}: {full_path}")
            missing_files.append((file_path, description))
            
    if missing_files:
        logger.warning(f"Missing {len(missing_files)} key data files. Run the download script to obtain them.")
        return False
    else:
        logger.info("All key STEP Bible data files found")
        return True

def main():
    """
    Run all verification checks.
    """
    logger.info("Starting data verification...")
    
    # Check STEP Bible data files
    step_files_ok = check_step_data_files()
    
    # Check database data counts
    db_counts_ok = check_data_counts()
    
    # Summarize results
    logger.info("\n===== VERIFICATION SUMMARY =====")
    logger.info(f"STEP Bible data files: {'OK' if step_files_ok else 'ISSUES FOUND'}")
    logger.info(f"Database data counts: {'OK' if db_counts_ok else 'ISSUES FOUND'}")
    
    if step_files_ok and db_counts_ok:
        logger.info("All verification checks passed")
        return 0
    else:
        logger.warning("Some verification checks failed - see log for details")
        return 1

if __name__ == "__main__":
>>>>>>> 7ce9bae97b2e6d0fe65169a363af093a8e5043a4
    sys.exit(main()) 