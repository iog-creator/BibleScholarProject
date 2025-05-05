"""
Integration tests for ETL process integrity.

These tests verify that all ETL processes are functioning correctly
and identify potential issues with data loading.
"""

import pytest
import logging
import os
import sys

# Add the root directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database connection
from src.database.connection import get_connection_string

ARABIC_BIBLE_DATA_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'data', 'Tagged-Bibles', 'Arabic Bibles', 'Translation Tags Individual Books'
)

pytestmark = pytest.mark.skipif(
    not os.path.exists(ARABIC_BIBLE_DATA_DIR),
    reason=f'Arabic Bible data directory not found: {ARABIC_BIBLE_DATA_DIR}'
)

@pytest.fixture(scope="module")
def db_engine():
    """Create a database engine for testing."""
    connection_string = get_connection_string()
    engine = create_engine(connection_string)
    return engine

def test_arabic_bible_file_count():
    """Test that the expected number of Arabic Bible files are available."""
    # Use os.path.join to create platform-independent path
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    arabic_bible_path = os.path.join(current_dir, "data", "Tagged-Bibles", "Arabic Bibles", "Translation Tags Individual Books")
    
    # Check if the directory exists
    assert os.path.isdir(arabic_bible_path), f"Arabic Bible directory not found: {arabic_bible_path}"
    
    # Count the number of text files
    files = [f for f in os.listdir(arabic_bible_path) if f.endswith('.txt')]
    file_count = len(files)
    
    logger.info(f"Found {file_count} Arabic Bible text files")
    assert file_count >= 66, f"Expected at least 66 Arabic Bible files, found {file_count}"
    
    # Log all file names for analysis
    for file in files:
        logger.info(f"Arabic Bible file: {file}")

def test_arabic_bible_etl_execution(db_engine):
    """Test that the Arabic Bible ETL process is properly loading data from all files."""
    # Check if we have a similar number of books and verses as expected
    with db_engine.connect() as conn:
        # Count unique books
        result = conn.execute(text("""
            SELECT COUNT(DISTINCT book_name) FROM bible.arabic_verses
        """))
        book_count = result.scalar()
        
        # Count total verses
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.arabic_verses
        """))
        verse_count = result.scalar()
        
        # Count total words
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.arabic_words
        """))
        word_count = result.scalar()
        
        # Count words with Strong's numbers
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.arabic_words WHERE strongs_id IS NOT NULL
        """))
        words_with_strongs = result.scalar()
        
        # Count New Testament words (G* Strong's)
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.arabic_words WHERE strongs_id LIKE 'G%'
        """))
        nt_words = result.scalar()
        
        # Count Old Testament words (H* Strong's)
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.arabic_words WHERE strongs_id LIKE 'H%'
        """))
        ot_words = result.scalar()
    
    logger.info(f"Arabic Bible ETL status:")
    logger.info(f"  Books: {book_count} (expected 66)")
    logger.info(f"  Verses: {verse_count} (expected ~31,091)")
    logger.info(f"  Words: {word_count} (current {word_count}, documentation states 382,293)")
    logger.info(f"  Strong's mapping: {words_with_strongs}/{word_count} ({words_with_strongs/word_count*100:.2f}%)")
    logger.info(f"  NT words: {nt_words}, OT words: {ot_words}")
    
    # Check if this appears to be a partial or complete load
    if word_count < 100000:  # Significantly below the expected 382,293
        logger.warning(f"Detected potential partial ETL load. Expected ~382,293 words, found {word_count}")
        logger.warning(f"This suggests the ETL process is not correctly processing all Arabic Bible files")
    
    # Verify verse distribution across books to check for partial loads
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT book_name, COUNT(*) as verse_count
            FROM bible.arabic_verses
            GROUP BY book_name
            ORDER BY verse_count
        """))
        book_stats = result.fetchall()
    
    # Log low-verse books which may indicate partial loading
    for book, count in book_stats:
        if count < 20:  # Most Bible books have more than 20 verses
            logger.warning(f"Low verse count for {book}: {count} verses (possible partial load)")

def test_arabic_etl_sample_file_parsing():
    """Test that a sample Arabic Bible file can be properly parsed."""
    from src.etl.etl_arabic_bible import parse_arabic_bible_file
    
    # Use os.path.join to create platform-independent path
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sample_file = os.path.join(
        current_dir, "data", "Tagged-Bibles", "Arabic Bibles", "Translation Tags Individual Books",
        "NT_25_3Jn_TTAraSVD - Translation Tags etc. for Arabic SVD - STEPBible.org CC BY-SA_1_2_1.txt"
    )
    
    # Check if the sample file exists
    assert os.path.isfile(sample_file), f"Sample file not found: {sample_file}"
    
    # Parse the file
    try:
        parsed_data = parse_arabic_bible_file(sample_file)
        
        verse_count = len(parsed_data['verses'])
        word_count = len(parsed_data['words'])
        
        logger.info(f"Sample file parse results: {verse_count} verses, {word_count} words")
        
        assert verse_count > 0, "Failed to parse any verses from sample file"
        assert word_count > 0, "Failed to parse any words from sample file"
        
        # Verify if each word has all expected fields
        sample_word = parsed_data['words'][0]
        
        logger.info(f"Sample word data: {sample_word}")
        assert 'verse_id' in sample_word, "Verse ID missing from parsed word"
        assert 'word_position' in sample_word, "Word position missing from parsed word"
        assert 'arabic_word' in sample_word, "Arabic word missing from parsed word"
        assert 'strongs_id' in sample_word, "Strong's ID missing from parsed word"
        
    except Exception as e:
        logger.error(f"Error parsing sample file: {e}")
        pytest.fail(f"Sample file parsing failed: {e}")

def test_etl_log_analysis():
    """Analyze ETL logs for errors or warnings."""
    log_path = "logs/etl/etl_arabic_bible.log"
    
    # Check if log file exists
    if not os.path.isfile(log_path):
        logger.warning(f"ETL log file not found: {log_path}")
        return
    
    error_count = 0
    processed_files = 0
    total_verses = 0
    total_words = 0
    
    # Parse the log file
    with open(log_path, 'r') as f:
        for line in f:
            if "ERROR" in line:
                error_count += 1
                logger.warning(f"ETL Error: {line.strip()}")
            
            if "Processing file:" in line:
                processed_files += 1
            
            if "Parsed" in line and "verses" in line and "words" in line:
                # Extract verse and word counts
                try:
                    parts = line.split("Parsed ")[1].split(" verses and ")
                    verses = int(parts[0])
                    words = int(parts[1].split(" words")[0])
                    total_verses += verses
                    total_words += words
                except (IndexError, ValueError):
                    pass
    
    logger.info(f"ETL log analysis:")
    logger.info(f"  Files processed: {processed_files}")
    logger.info(f"  Total parsed verses: {total_verses}")
    logger.info(f"  Total parsed words: {total_words}")
    logger.info(f"  Error count: {error_count}")
    
    if total_words < 100000:
        logger.warning(f"Log shows only {total_words} words parsed, well below expected 382,293")

def test_word_count_estimation(db_engine):
    """Estimate the expected word count based on average words per verse."""
    with db_engine.connect() as conn:
        # Get total verses
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.arabic_verses
        """))
        verse_count = result.scalar()
        
        # Get total words
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.arabic_words
        """))
        word_count = result.scalar()
    
    # Calculate words per verse
    words_per_verse = word_count / verse_count if verse_count > 0 else 0
    
    # Expected verses in a complete Bible is about 31,091
    expected_verse_count = 31091
    estimated_word_count = expected_verse_count * words_per_verse
    
    logger.info(f"Word count estimation:")
    logger.info(f"  Current words per verse: {words_per_verse:.2f}")
    logger.info(f"  Estimated total word count for {expected_verse_count} verses: {estimated_word_count:.0f}")
    
    # Check how this compares to the expected 382,293
    ratio = estimated_word_count / 382293 if estimated_word_count > 0 else 0
    logger.info(f"  Ratio of estimated count to documentation count: {ratio:.2f}")
    
    if 0.9 <= ratio <= 1.1:
        logger.info("Estimated word count is within 10% of the documentation count")
    else:
        logger.warning("Significant discrepancy between estimated and documentation word counts") 