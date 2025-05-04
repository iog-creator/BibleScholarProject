"""
Script to verify and lock loaded Bible data.

This script:
1. Verifies all required tables exist
2. Checks data has been loaded correctly
3. Adds constraints to lock the data
4. Generates a verification report
"""

import logging
from sqlalchemy import text, create_engine
from db_config import get_db_params
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_table_exists(conn, schema, table):
    """Verify if a table exists in the database."""
    exists = conn.execute(text(f"""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = '{schema}'
            AND table_name = '{table}'
        );
    """)).scalar()
    return exists

def count_rows(conn, schema, table):
    """Count rows in a table."""
    count = conn.execute(text(f"""
        SELECT COUNT(*) FROM {schema}.{table};
    """)).scalar()
    return count

def verify_books_data(conn):
    """Verify books data is loaded correctly."""
    if not verify_table_exists(conn, 'bible', 'books'):
        logger.error("Books table does not exist")
        return False
        
    row_count = count_rows(conn, 'bible', 'books')
    if row_count != 66:  # Expected number of Bible books
        logger.error(f"Unexpected number of books: {row_count} (expected 66)")
        return False
        
    # Verify required columns have data
    null_check = conn.execute(text("""
        SELECT COUNT(*) FROM bible.books 
        WHERE book_name IS NULL 
        OR testament IS NULL 
        OR book_number IS NULL 
        OR chapters IS NULL;
    """)).scalar()
    
    if null_check > 0:
        logger.error(f"Found {null_check} books with NULL values in required fields")
        return False
        
    logger.info("Books data verification passed")
    return True

def display_problematic_verses(conn):
    """Display verses with invalid chapter or verse numbers."""
    invalid_verses = conn.execute(text("""
        SELECT book_name, chapter, verse 
        FROM bible.verses 
        WHERE verse <= 0 OR chapter <= 0
        ORDER BY book_name, chapter, verse
        LIMIT 10
    """)).fetchall()
    
    if invalid_verses:
        logger.error("Sample of verses with invalid numbers:")
        for verse in invalid_verses:
            logger.error(f"  {verse.book_name} {verse.chapter}:{verse.verse}")
    
    return invalid_verses

def verify_verses_data(conn):
    """Verify verses data is loaded correctly."""
    if not verify_table_exists(conn, 'bible', 'verses'):
        logger.error("Verses table does not exist")
        return False
        
    row_count = count_rows(conn, 'bible', 'verses')
    if row_count == 0:
        logger.error("No verses found in the database")
        return False
        
    # Check for required fields
    null_check = conn.execute(text("""
        SELECT COUNT(*) FROM bible.verses 
        WHERE book_name IS NULL 
        OR chapter IS NULL 
        OR verse IS NULL;
    """)).scalar()
    
    if null_check > 0:
        logger.error(f"Found {null_check} verses with NULL values in required fields")
        return False
        
    # Check for invalid verse numbers - allowing verse 0 for Psalms (superscriptions)
    invalid_verses = conn.execute(text("""
        SELECT book_name, chapter, verse FROM bible.verses 
        WHERE (verse < 0) 
        OR (verse = 0 AND book_name != 'Psa')
        OR chapter <= 0
        ORDER BY book_name, chapter, verse
    """)).fetchall()
    
    if invalid_verses:
        logger.error(f"Found {len(invalid_verses)} verses with invalid chapter/verse numbers")
        return False
        
    # Count Psalm superscriptions for logging
    psalm_titles = conn.execute(text("""
        SELECT COUNT(*) FROM bible.verses 
        WHERE book_name = 'Psa' AND verse = 0
    """)).scalar()
    
    logger.info(f"Verses data verification passed ({row_count} verses, including {psalm_titles} Psalm superscriptions)")
    return True

def verify_lexicon_data(conn):
    """Verify lexicon data is loaded correctly."""
    tables = ['greek_entries', 'hebrew_entries', 'word_relationships']
    
    for table in tables:
        if not verify_table_exists(conn, 'bible', table):
            logger.error(f"Table {table} does not exist")
            return False
            
    greek_count = count_rows(conn, 'bible', 'greek_entries')
    hebrew_count = count_rows(conn, 'bible', 'hebrew_entries')
    rel_count = count_rows(conn, 'bible', 'word_relationships')
    
    logger.info(f"Found {greek_count} Greek entries, {hebrew_count} Hebrew entries, {rel_count} relationships")
    
    if greek_count == 0 or hebrew_count == 0:
        logger.error("Missing lexicon entries")
        return False
        
    return True

def verify_morphology_data(conn):
    """Verify morphology documentation is loaded correctly."""
    tables = ['morphology_documentation_greek', 'morphology_documentation_hebrew']
    
    for table in tables:
        if not verify_table_exists(conn, 'bible', table):
            logger.error(f"Table {table} does not exist")
            return False
            
    greek_count = count_rows(conn, 'bible', 'morphology_documentation_greek')
    hebrew_count = count_rows(conn, 'bible', 'morphology_documentation_hebrew')
    
    logger.info(f"Found {greek_count} Greek morphology codes, {hebrew_count} Hebrew morphology codes")
    
    if greek_count == 0 or hebrew_count == 0:
        logger.error("Missing morphology documentation")
        return False
        
    return True

def verify_proper_names(conn):
    """Verify proper names data is loaded correctly."""
    if not verify_table_exists(conn, 'bible', 'proper_names'):
        logger.error("Proper names table does not exist")
        return False
        
    count = count_rows(conn, 'bible', 'proper_names')
    logger.info(f"Found {count} proper names")
    
    if count == 0:
        logger.error("No proper names found")
        return False
        
    return True

def verify_versification(conn):
    """Verify versification data is loaded correctly."""
    tables = ['versification_mappings', 'versification_rules']
    
    for table in tables:
        if not verify_table_exists(conn, 'bible', table):
            logger.error(f"Table {table} does not exist")
            return False
            
    mappings_count = count_rows(conn, 'bible', 'versification_mappings')
    rules_count = count_rows(conn, 'bible', 'versification_rules')
    
    logger.info(f"Found {mappings_count} versification mappings, {rules_count} rules")
    
    if mappings_count == 0:
        logger.error("No versification mappings found")
        return False
        
    return True

def lock_verified_data(conn):
    """Lock tables that have been verified by adding constraints and revoking permissions."""
    try:
        logger.info("Locking verified tables...")
        
        # Verify data before adding constraints
        logger.info("Verifying data before adding constraints...")
        
        # Check books data
        invalid_testament = conn.execute(text("""
            SELECT book_name, testament FROM bible.books 
            WHERE testament NOT IN ('OT', 'NT')
        """)).fetchall()
        
        if invalid_testament:
            logger.error(f"Found {len(invalid_testament)} books with invalid testament values")
            return False
            
        # Check verses data - allowing verse 0 for Psalms (superscriptions)
        invalid_verses = conn.execute(text("""
            SELECT book_name, chapter, verse FROM bible.verses 
            WHERE (verse < 0) 
            OR (verse = 0 AND book_name != 'Psa')
            OR chapter <= 0
        """)).fetchall()
        
        if invalid_verses:
            logger.error(f"Found {len(invalid_verses)} verses with invalid chapter/verse numbers")
            for v in invalid_verses[:5]:  # Show first 5 invalid verses
                logger.error(f"  Invalid verse: {v.book_name} {v.chapter}:{v.verse}")
            return False
            
        # Check lexicon data
        invalid_greek = conn.execute(text("""
            SELECT strongs_ref FROM bible.greek_entries 
            WHERE strongs_ref NOT LIKE 'G%'
        """)).fetchall()
        
        if invalid_greek:
            logger.error(f"Found {len(invalid_greek)} Greek entries with invalid Strong's references")
            return False
            
        invalid_hebrew = conn.execute(text("""
            SELECT strongs_ref FROM bible.hebrew_entries 
            WHERE strongs_ref NOT LIKE 'H%'
        """)).fetchall()
        
        if invalid_hebrew:
            logger.error(f"Found {len(invalid_hebrew)} Hebrew entries with invalid Strong's references")
            return False
        
        logger.info("All data validated, adding constraints...")
        
        # Add foreign key constraints
        logger.info("Adding foreign key constraints...")
        conn.execute(text("""
            ALTER TABLE bible.verses 
            ADD CONSTRAINT fk_verses_book_name 
            FOREIGN KEY (book_name) REFERENCES bible.books(book_name);
        """))
        
        # Add check constraints one by one
        logger.info("Adding check constraints...")
        
        # Books constraints
        conn.execute(text("""
            ALTER TABLE bible.books 
            ADD CONSTRAINT check_testament 
            CHECK (testament IN ('OT', 'NT'));
        """))
        
        # Verses constraints - allowing verse 0 for Psalms
        conn.execute(text("""
            ALTER TABLE bible.verses 
            ADD CONSTRAINT check_chapter_positive 
            CHECK (chapter > 0);
        """))
        
        conn.execute(text("""
            ALTER TABLE bible.verses 
            ADD CONSTRAINT check_verse_valid 
            CHECK (
                (verse > 0) OR 
                (verse = 0 AND book_name = 'Psa')
            );
        """))
        
        # Lexicon constraints
        conn.execute(text("""
            ALTER TABLE bible.greek_entries
            ADD CONSTRAINT check_greek_strongs
            CHECK (strongs_ref LIKE 'G%');
        """))
        
        conn.execute(text("""
            ALTER TABLE bible.hebrew_entries
            ADD CONSTRAINT check_hebrew_strongs
            CHECK (strongs_ref LIKE 'H%');
        """))
        
        # Revoke modification permissions
        logger.info("Revoking modification permissions...")
        tables = [
            'books', 'verses', 'greek_entries', 'hebrew_entries',
            'morphology_documentation_greek', 'morphology_documentation_hebrew'
        ]
        
        for table in tables:
            conn.execute(text(f"""
                REVOKE INSERT, UPDATE, DELETE ON bible.{table} FROM PUBLIC;
            """))
        
        logger.info("Successfully locked verified tables")
        return True
        
    except Exception as e:
        logger.error(f"Error locking tables: {str(e)}")
        return False

def generate_report(conn):
    """Generate a verification report."""
    report = []
    
    # Get table counts
    tables = {
        'books': 'bible.books',
        'verses': 'bible.verses',
        'greek_entries': 'bible.greek_entries',
        'hebrew_entries': 'bible.hebrew_entries',
        'greek_morphology': 'bible.morphology_documentation_greek',
        'hebrew_morphology': 'bible.morphology_documentation_hebrew',
        'proper_names': 'bible.proper_names',
        'versification_mappings': 'bible.versification_mappings',
        'versification_rules': 'bible.versification_rules'
    }
    
    for name, table in tables.items():
        count = count_rows(conn, *table.split('.'))
        report.append(f"{name}: {count} records")
    
    # Save report
    with open('data_verification_report.txt', 'w') as f:
        f.write("Bible Data Verification Report\n")
        f.write("============================\n\n")
        f.write("\n".join(report))
    
    logger.info("Verification report generated")

def main():
    """Main verification function."""
    try:
        db_params = get_db_params()
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}')
        
        with engine.begin() as conn:
            verifications = [
                ('Books', verify_books_data(conn)),
                ('Verses', verify_verses_data(conn)),
                ('Lexicon', verify_lexicon_data(conn)),
                ('Morphology', verify_morphology_data(conn)),
                ('Proper Names', verify_proper_names(conn)),
                ('Versification', verify_versification(conn))
            ]
            
            all_core_passed = all(v[1] for v in verifications[:4])  # Check only books, verses, lexicon, and morphology
            
            if all_core_passed:
                logger.info("Core data verification passed")
                if lock_verified_data(conn):
                    generate_report(conn)
                    logger.info("Core data verified and locked successfully")
                else:
                    logger.error("Failed to lock core data")
            else:
                failed = [v[0] for v in verifications[:4] if not v[1]]
                logger.error(f"Core verification failed for: {', '.join(failed)}")
                
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        raise

if __name__ == '__main__':
    main() 