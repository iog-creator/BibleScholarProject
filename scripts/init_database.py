#!/usr/bin/env python3
"""
Database initialization script for the BibleScholarProject.

This script:
1. Creates the bible schema if it doesn't exist
2. Creates all required tables
3. Sets up initial constraints and indexes
4. Seeds the database with necessary lookup data
"""

import os
import sys
import logging
import argparse
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
        logging.FileHandler('init_database.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('init_database')

def create_schema(conn):
    """Create the bible schema if it doesn't exist."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS bible;")
            conn.commit()
        logger.info("Ensured bible schema exists")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating schema: {e}")
        return False

def create_tables(conn):
    """Create all required tables if they don't exist."""
    try:
        with conn.cursor() as cursor:
            # Create verses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bible.verses (
                    id SERIAL PRIMARY KEY,
                    book_name TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    verse_num INTEGER NOT NULL,
                    verse_text TEXT NOT NULL,
                    translation_source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (book_name, chapter_num, verse_num, translation_source)
                )
            """)
            
            # Create Hebrew entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bible.hebrew_entries (
                    id SERIAL,
                    strongs_id TEXT UNIQUE NOT NULL,
                    extended_strongs TEXT,
                    hebrew_word TEXT,
                    transliteration TEXT,
                    pos TEXT,
                    gloss TEXT,
                    definition TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create Hebrew OT words table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bible.hebrew_ot_words (
                    id SERIAL PRIMARY KEY,
                    book_name TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    verse_num INTEGER NOT NULL,
                    word_num INTEGER NOT NULL,
                    word_text TEXT NOT NULL,
                    strongs_id TEXT,
                    grammar_code TEXT,
                    word_transliteration TEXT,
                    translation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (book_name, chapter_num, verse_num, word_num)
                )
            """)
            
            # Create Greek entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bible.greek_entries (
                    id SERIAL PRIMARY KEY,
                    strongs_id TEXT UNIQUE NOT NULL,
                    word_text TEXT,
                    transliteration TEXT,
                    definition TEXT,
                    part_of_speech TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create Greek NT words table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bible.greek_nt_words (
                    id SERIAL PRIMARY KEY,
                    book_name TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    verse_num INTEGER NOT NULL,
                    word_num INTEGER NOT NULL,
                    word_text TEXT NOT NULL,
                    strongs_id TEXT,
                    grammar_code TEXT,
                    word_transliteration TEXT,
                    translation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (book_name, chapter_num, verse_num, word_num)
                )
            """)
            
            # Create verse/word linking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bible.verse_word_links (
                    id SERIAL PRIMARY KEY,
                    verse_id INTEGER NOT NULL REFERENCES bible.verses(id),
                    word_id INTEGER NOT NULL,
                    word_type TEXT NOT NULL, -- 'hebrew' or 'greek'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (verse_id, word_id, word_type)
                )
            """)
            
            # Create cross-language terms mapping table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bible.cross_language_terms (
                    id SERIAL PRIMARY KEY,
                    term_key TEXT UNIQUE NOT NULL,
                    hebrew_strongs_id TEXT,
                    greek_strongs_id TEXT,
                    arabic_term TEXT,
                    theological_category TEXT,
                    equivalent_type TEXT, -- 'exact', 'partial', 'contextual'
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for efficient queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_verses_reference 
                ON bible.verses (book_name, chapter_num, verse_num)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_hebrew_ot_words_reference 
                ON bible.hebrew_ot_words (book_name, chapter_num, verse_num)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_hebrew_ot_words_strongs 
                ON bible.hebrew_ot_words (strongs_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_greek_nt_words_reference 
                ON bible.greek_nt_words (book_name, chapter_num, verse_num)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_greek_nt_words_strongs 
                ON bible.greek_nt_words (strongs_id)
            """)
            
            conn.commit()
            logger.info("Created all required tables")
            return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating tables: {e}")
        return False

def seed_critical_terms(conn):
    """Seed the critical theological terms in the database."""
    try:
        with conn.cursor() as cursor:
            # First check if we already have sufficient critical terms
            cursor.execute("SELECT COUNT(*) FROM bible.hebrew_entries WHERE strongs_id IN ('H430', 'H3068', 'H113', 'H2617', 'H539')")
            count = cursor.fetchone()[0]
            
            if count >= 5:
                logger.info(f"Critical terms already present in hebrew_entries ({count}/5)")
                return True
            
            # Seed the critical Hebrew terms
            critical_terms = [
                ('H430', 'H430', 'אלהים', 'elohim', 'N:N-M-P', 'God', 'God, gods, judges, angels'),
                ('H3068', 'H3068', 'יהוה', 'YHWH', 'N:NPR-M', 'LORD', 'the proper name of the God of Israel'),
                ('H113', 'H113', 'אדון', 'adon', 'N:N-M', 'lord', 'lord, master, owner'),
                ('H2617', 'H2617', 'חסד', 'chesed', 'N:N-F', 'lovingkindness', 'goodness, kindness, faithfulness'),
                ('H539', 'H539', 'אמן', 'aman', 'V:QAL', 'believe', 'to confirm, support, believe, be faithful')
            ]
            
            for term in critical_terms:
                cursor.execute("""
                    INSERT INTO bible.hebrew_entries 
                    (strongs_id, extended_strongs, hebrew_word, transliteration, pos, gloss, definition)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (strongs_id) DO NOTHING
                """, term)
            
            # Seed cross-language mappings
            cross_language_terms = [
                ('god', 'H430', 'G2316', 'الله', 'deity', 'partial', 'Elohim-Theos-Allah mapping'),
                ('lord', 'H3068', 'G2962', 'الرب', 'deity', 'contextual', 'YHWH-Kyrios-Rabb mapping'),
                ('faith', 'H539', 'G4102', 'إيمان', 'belief', 'exact', 'Aman-Pistis-Iman mapping')
            ]
            
            for term in cross_language_terms:
                cursor.execute("""
                    INSERT INTO bible.cross_language_terms
                    (term_key, hebrew_strongs_id, greek_strongs_id, arabic_term, theological_category, equivalent_type, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (term_key) DO NOTHING
                """, term)
            
            conn.commit()
            logger.info("Seeded critical theological terms")
            return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error seeding critical terms: {e}")
        return False

def validate_database(conn):
    """Validate that the database has been properly initialized."""
    try:
        with conn.cursor() as cursor:
            # Check that all required tables exist
            required_tables = [
                'verses', 'hebrew_entries', 'hebrew_ot_words', 
                'greek_entries', 'greek_nt_words', 'verse_word_links',
                'cross_language_terms'
            ]
            
            # Build a query to count all tables at once
            table_checks = []
            for table in required_tables:
                table_checks.append(f"""
                    (SELECT EXISTS(
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'bible' AND table_name = '{table}'
                    ) AS {table}_exists)
                """)
            
            query = " CROSS JOIN ".join(table_checks)
            cursor.execute(f"SELECT * FROM {query}")
            result = cursor.fetchone()
            
            # Count how many tables exist
            tables_found = sum(1 for exists in result if exists)
            
            if tables_found == len(required_tables):
                logger.info(f"All {len(required_tables)} required tables exist")
            else:
                missing_tables = [table for i, table in enumerate(required_tables) if not result[i]]
                logger.warning(f"Missing tables: {', '.join(missing_tables)}")
            
            # Check critical terms
            cursor.execute("SELECT COUNT(*) FROM bible.hebrew_entries WHERE strongs_id IN ('H430', 'H3068', 'H113', 'H2617', 'H539')")
            critical_terms_count = cursor.fetchone()[0]
            logger.info(f"Found {critical_terms_count}/5 critical Hebrew terms")
            
            # Check cross-language mappings
            cursor.execute("SELECT COUNT(*) FROM bible.cross_language_terms")
            mappings_count = cursor.fetchone()[0]
            logger.info(f"Found {mappings_count} cross-language term mappings")
            
            return tables_found == len(required_tables) and critical_terms_count == 5
    except Exception as e:
        logger.error(f"Error validating database: {e}")
        return False

def main():
    """Main function to initialize the database."""
    parser = argparse.ArgumentParser(description='Initialize the BibleScholarProject database')
    parser.add_argument('--force', action='store_true', help='Force recreation of tables (WARNING: will delete existing data)')
    args = parser.parse_args()
    
    logger.info("Starting database initialization")
    
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False
        
        try:
            # Create schema
            if not create_schema(conn):
                return False
            
            # Handle force recreation of tables
            if args.force:
                logger.warning("Force flag is set - dropping existing tables")
                with conn.cursor() as cursor:
                    cursor.execute("""
                        DROP TABLE IF EXISTS 
                            bible.verse_word_links,
                            bible.hebrew_ot_words,
                            bible.greek_nt_words,
                            bible.cross_language_terms,
                            bible.verses,
                            bible.hebrew_entries,
                            bible.greek_entries
                        CASCADE
                    """)
                    conn.commit()
                logger.info("Dropped existing tables")
            
            # Create tables
            if not create_tables(conn):
                return False
            
            # Seed critical terms
            if not seed_critical_terms(conn):
                return False
            
            # Validate the database
            if not validate_database(conn):
                logger.warning("Database validation found issues")
            
            logger.info("Database initialization completed successfully")
            return True
        
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 