"""
Integration tests for lexicon data extraction and loading.

These tests verify that the Hebrew and Greek lexicon data (TBESH, TBESG, TFLSJ)
and word relationships have been correctly extracted and loaded into the database.
"""

import pytest
import logging
import re
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database connection
from src.database.connection import get_connection_string

@pytest.fixture(scope="module")
def db_engine():
    """Create a database engine for testing."""
    connection_string = get_connection_string()
    engine = create_engine(connection_string)
    return engine

def test_hebrew_lexicon_count(db_engine):
    """Test that the expected number of Hebrew lexicon entries are loaded."""
    expected_count = 9345  # As documented in COMPLETED_WORK.md
    
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.hebrew_entries
        """))
        actual_count = result.scalar()
        
    logger.info(f"Found {actual_count} Hebrew lexicon entries")
    assert actual_count == expected_count, f"Expected {expected_count} Hebrew lexicon entries, found {actual_count}"

def test_greek_lexicon_count(db_engine):
    """Test that the expected number of Greek lexicon entries are loaded."""
    expected_count = 10847  # As documented in COMPLETED_WORK.md
    
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.greek_entries
        """))
        actual_count = result.scalar()
        
    logger.info(f"Found {actual_count} Greek lexicon entries")
    assert actual_count == expected_count, f"Expected {expected_count} Greek lexicon entries, found {actual_count}"

def test_lsj_lexicon_count(db_engine):
    """Test that the expected number of LSJ lexicon entries are loaded."""
    expected_count = 10846  # As documented in COMPLETED_WORK.md
    
    with db_engine.connect() as conn:
        # Check if the table exists first
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'bible' 
                AND table_name = 'lsj_entries'
            )
        """))
        table_exists = result.scalar()
        
        if table_exists:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM bible.lsj_entries
            """))
            actual_count = result.scalar()
            
            logger.info(f"Found {actual_count} LSJ lexicon entries")
            assert actual_count == expected_count, f"Expected {expected_count} LSJ lexicon entries, found {actual_count}"
        else:
            logger.warning("LSJ lexicon table does not exist, skipping count check")
            pytest.skip("LSJ lexicon table does not exist")

def test_word_relationships_count(db_engine):
    """Test that word relationships are loaded."""
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.word_relationships
        """))
        actual_count = result.scalar()
        
    logger.info(f"Found {actual_count} word relationships")
    assert actual_count > 0, f"Expected word relationships to be loaded, found {actual_count}"

def test_hebrew_strongs_id_format(db_engine):
    """Test that Hebrew Strong's IDs follow the expected format."""
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT strongs_id FROM bible.hebrew_entries
            LIMIT 1000
        """))
        strongs_ids = [row[0] for row in result.fetchall()]
        
    # Hebrew Strong's IDs should match pattern H\d{4,5}[A-Za-z]?
    hebrew_pattern = re.compile(r'^H\d{4,5}[A-Za-z]?$')
    invalid_ids = [id for id in strongs_ids if not hebrew_pattern.match(id)]
    
    logger.info(f"Checked {len(strongs_ids)} Hebrew Strong's IDs")
    if invalid_ids:
        logger.warning(f"Found {len(invalid_ids)} invalid Hebrew Strong's IDs: {invalid_ids[:5]}...")
    
    assert len(invalid_ids) == 0, f"Found {len(invalid_ids)} invalid Hebrew Strong's IDs"

def test_greek_strongs_id_format(db_engine):
    """Test that Greek Strong's IDs follow the expected format."""
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT strongs_id FROM bible.greek_entries
            LIMIT 1000
        """))
        strongs_ids = [row[0] for row in result.fetchall()]
        
    # Greek Strong's IDs should match pattern G\d{4,5}[A-Za-z]?
    greek_pattern = re.compile(r'^G\d{4,5}[A-Za-z]?$')
    invalid_ids = [id for id in strongs_ids if not greek_pattern.match(id)]
    
    logger.info(f"Checked {len(strongs_ids)} Greek Strong's IDs")
    if invalid_ids:
        logger.warning(f"Found {len(invalid_ids)} invalid Greek Strong's IDs: {invalid_ids[:5]}...")
    
    assert len(invalid_ids) == 0, f"Found {len(invalid_ids)} invalid Greek Strong's IDs"

def test_lexicon_entries_completeness(db_engine):
    """Test that lexicon entries have required fields populated."""
    with db_engine.connect() as conn:
        # Check Hebrew entries
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.hebrew_entries
            WHERE hebrew_word IS NULL OR definition IS NULL
        """))
        incomplete_hebrew = result.scalar()
        
        # Check Greek entries
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.greek_entries
            WHERE greek_word IS NULL OR definition IS NULL
        """))
        incomplete_greek = result.scalar()
        
    logger.info(f"Found {incomplete_hebrew} incomplete Hebrew entries, {incomplete_greek} incomplete Greek entries")
    assert incomplete_hebrew == 0, f"Found {incomplete_hebrew} Hebrew entries missing required fields"
    assert incomplete_greek == 0, f"Found {incomplete_greek} Greek entries missing required fields"

def test_word_relationships_integrity(db_engine):
    """Test that word relationships have valid references to lexicon entries."""
    with db_engine.connect() as conn:
        # Check for word relationships with invalid source_id referencing Hebrew entries
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.word_relationships wr
            LEFT JOIN bible.hebrew_entries he ON wr.source_id = he.strongs_id
            WHERE wr.source_id LIKE 'H%' AND he.strongs_id IS NULL
        """))
        invalid_hebrew_sources = result.scalar()
        
        # Check for word relationships with invalid source_id referencing Greek entries
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.word_relationships wr
            LEFT JOIN bible.greek_entries ge ON wr.source_id = ge.strongs_id
            WHERE wr.source_id LIKE 'G%' AND ge.strongs_id IS NULL
        """))
        invalid_greek_sources = result.scalar()
        
        # Check for word relationships with invalid target_id referencing Hebrew entries
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.word_relationships wr
            LEFT JOIN bible.hebrew_entries he ON wr.target_id = he.strongs_id
            WHERE wr.target_id LIKE 'H%' AND he.strongs_id IS NULL
        """))
        invalid_hebrew_targets = result.scalar()
        
        # Check for word relationships with invalid target_id referencing Greek entries
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.word_relationships wr
            LEFT JOIN bible.greek_entries ge ON wr.target_id = ge.strongs_id
            WHERE wr.target_id LIKE 'G%' AND ge.strongs_id IS NULL
        """))
        invalid_greek_targets = result.scalar()
        
    logger.info(f"Invalid relationship sources: {invalid_hebrew_sources} Hebrew, {invalid_greek_sources} Greek")
    logger.info(f"Invalid relationship targets: {invalid_hebrew_targets} Hebrew, {invalid_greek_targets} Greek")
    
    total_invalid = invalid_hebrew_sources + invalid_greek_sources + invalid_hebrew_targets + invalid_greek_targets
    assert total_invalid == 0, f"Found {total_invalid} word relationships with invalid references"

def test_sample_important_lexicon_entries(db_engine):
    """Test that important lexicon entries are present."""
    key_hebrew_entries = [
        "H0430",  # Elohim (God)
        "H3068",  # YHWH (LORD)
        "H0001",  # First Hebrew entry
        "H8674"   # One of the last Hebrew entries
    ]
    
    key_greek_entries = [
        "G2316",  # Theos (God)
        "G2424",  # Iesous (Jesus)
        "G0001",  # First Greek entry
        "G5624"   # One of the last Greek entries
    ]
    
    with db_engine.connect() as conn:
        # Check Hebrew entries
        for strongs_id in key_hebrew_entries:
            result = conn.execute(text(f"""
                SELECT strongs_id, hebrew_word FROM bible.hebrew_entries
                WHERE strongs_id = '{strongs_id}'
            """))
            entry = result.fetchone()
            assert entry is not None, f"Key Hebrew entry {strongs_id} not found"
            if entry:
                logger.info(f"Found Hebrew entry {strongs_id}: {entry.hebrew_word}")
                
        # Check Greek entries
        for strongs_id in key_greek_entries:
            result = conn.execute(text(f"""
                SELECT strongs_id, greek_word FROM bible.greek_entries
                WHERE strongs_id = '{strongs_id}'
            """))
            entry = result.fetchone()
            assert entry is not None, f"Key Greek entry {strongs_id} not found"
            if entry:
                logger.info(f"Found Greek entry {strongs_id}: {entry.greek_word}") 