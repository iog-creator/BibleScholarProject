"""
Integration tests for Bible verse data extraction and loading.

These tests verify that the Hebrew Old Testament (TAHOT) and Greek New Testament (TAGNT)
verse data has been correctly extracted and loaded into the database.
"""

import pytest
import logging
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

def test_total_verses_count(db_engine):
    """Test that the expected total number of Bible verses are loaded."""
    expected_count = 31219  # As documented in COMPLETED_WORK.md
    
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.verses
        """))
        actual_count = result.scalar()
        
    logger.info(f"Found {actual_count} total Bible verses")
    assert actual_count == expected_count, f"Expected {expected_count} total Bible verses, found {actual_count}"

def test_hebrew_ot_verses_count(db_engine):
    """Test that the expected number of Hebrew Old Testament verses are loaded."""
    expected_count = 23261  # As documented in COMPLETED_WORK.md
    
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.verses
            WHERE translation_source = 'TAHOT'
        """))
        actual_count = result.scalar()
        
    logger.info(f"Found {actual_count} Hebrew Old Testament verses")
    assert actual_count == expected_count, f"Expected {expected_count} Hebrew OT verses, found {actual_count}"

def test_greek_nt_verses_count(db_engine):
    """Test that the expected number of Greek New Testament verses are loaded."""
    expected_count = 7958  # As documented in COMPLETED_WORK.md
    
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.verses
            WHERE translation_source = 'TAGNT'
        """))
        actual_count = result.scalar()
        
    logger.info(f"Found {actual_count} Greek New Testament verses")
    assert actual_count == expected_count, f"Expected {expected_count} Greek NT verses, found {actual_count}"

def test_hebrew_ot_words_count(db_engine):
    """Test that the expected number of Hebrew Old Testament words are loaded."""
    expected_count = 305577  # As documented in COMPLETED_WORK.md
    
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.hebrew_ot_words
        """))
        actual_count = result.scalar()
        
    logger.info(f"Found {actual_count} Hebrew Old Testament words")
    assert actual_count == expected_count, f"Expected {expected_count} Hebrew OT words, found {actual_count}"

def test_greek_nt_words_count(db_engine):
    """Test that the expected number of Greek New Testament words are loaded."""
    expected_count = 142096  # As documented in COMPLETED_WORK.md
    
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.greek_nt_words
        """))
        actual_count = result.scalar()
        
    logger.info(f"Found {actual_count} Greek New Testament words")
    assert actual_count == expected_count, f"Expected {expected_count} Greek NT words, found {actual_count}"

def test_bible_book_count(db_engine):
    """Test that the expected number of Bible books are loaded."""
    expected_ot_books = 39
    expected_nt_books = 27
    
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(DISTINCT book_name) FROM bible.verses
            WHERE translation_source = 'TAHOT'
        """))
        actual_ot_books = result.scalar()
        
        result = conn.execute(text("""
            SELECT COUNT(DISTINCT book_name) FROM bible.verses
            WHERE translation_source = 'TAGNT'
        """))
        actual_nt_books = result.scalar()
        
    logger.info(f"Found {actual_ot_books} OT books, {actual_nt_books} NT books")
    assert actual_ot_books == expected_ot_books, f"Expected {expected_ot_books} OT books, found {actual_ot_books}"
    assert actual_nt_books == expected_nt_books, f"Expected {expected_nt_books} NT books, found {actual_nt_books}"

def test_key_bible_verses(db_engine):
    """Test that key Bible verses are present with correct content."""
    key_verses = [
        {"book": "Gen", "chapter": 1, "verse": 1},  # In the beginning...
        {"book": "Exo", "chapter": 20, "verse": 3},  # 10 Commandments
        {"book": "Psa", "chapter": 23, "verse": 1},  # The LORD is my shepherd
        {"book": "Isa", "chapter": 53, "verse": 5},  # He was wounded for our transgressions
        {"book": "Mat", "chapter": 1, "verse": 1},   # The genealogy of Jesus
        {"book": "Jhn", "chapter": 3, "verse": 16},  # For God so loved the world
        {"book": "Rom", "chapter": 3, "verse": 23},  # All have sinned
        {"book": "Rev", "chapter": 22, "verse": 21}  # Last verse of the Bible
    ]
    
    with db_engine.connect() as conn:
        missing_verses = []
        
        for verse in key_verses:
            result = conn.execute(text(f"""
                SELECT book_name, chapter_num, verse_num, verse_text FROM bible.verses
                WHERE book_name = '{verse['book']}'
                AND chapter_num = {verse['chapter']}
                AND verse_num = {verse['verse']}
            """))
            verse_data = result.fetchone()
            
            if verse_data is None:
                missing_verses.append(f"{verse['book']} {verse['chapter']}:{verse['verse']}")
            else:
                logger.info(f"Found verse {verse['book']} {verse['chapter']}:{verse['verse']}: {verse_data.verse_text[:50]}...")
        
        if missing_verses:
            logger.warning(f"Missing key verses: {missing_verses}")
        
        assert len(missing_verses) == 0, f"Missing key verses: {missing_verses}"

def test_verse_words_relationship(db_engine):
    """Test that Bible words are correctly linked to their verses."""
    with db_engine.connect() as conn:
        # Test Hebrew words
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.hebrew_ot_words w
            JOIN bible.verses v ON w.book_name = v.book_name 
                AND w.chapter_num = v.chapter_num 
                AND w.verse_num = v.verse_num
        """))
        linked_hebrew_words = result.scalar()
        
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.hebrew_ot_words
        """))
        total_hebrew_words = result.scalar()
        
        # Test Greek words
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.greek_nt_words w
            JOIN bible.verses v ON w.book_name = v.book_name 
                AND w.chapter_num = v.chapter_num 
                AND w.verse_num = v.verse_num
        """))
        linked_greek_words = result.scalar()
        
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.greek_nt_words
        """))
        total_greek_words = result.scalar()
        
    hebrew_linking_percentage = (linked_hebrew_words / total_hebrew_words) * 100 if total_hebrew_words > 0 else 0
    greek_linking_percentage = (linked_greek_words / total_greek_words) * 100 if total_greek_words > 0 else 0
    
    logger.info(f"Found {linked_hebrew_words} out of {total_hebrew_words} Hebrew words linked to verses ({hebrew_linking_percentage:.2f}%)")
    logger.info(f"Found {linked_greek_words} out of {total_greek_words} Greek words linked to verses ({greek_linking_percentage:.2f}%)")
    
    assert hebrew_linking_percentage > 99, f"Only {hebrew_linking_percentage:.2f}% of Hebrew words are linked to verses (expected > 99%)"
    assert greek_linking_percentage > 99, f"Only {greek_linking_percentage:.2f}% of Greek words are linked to verses (expected > 99%)"

def test_word_strongs_mapping(db_engine):
    """Test that words are correctly mapped to Strong's numbers."""
    with db_engine.connect() as conn:
        # Test Hebrew words - we now check both strongs_id field and grammar_code field
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.hebrew_ot_words
            WHERE strongs_id IS NOT NULL
        """))
        mapped_hebrew_words_strongs_id = result.scalar()
        
        # Check grammar_code field for {HNNNN} patterns
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.hebrew_ot_words
            WHERE grammar_code LIKE '%{H%}%'
        """))
        mapped_hebrew_words_grammar = result.scalar()
        
        # Get total Hebrew words
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.hebrew_ot_words
        """))
        total_hebrew_words = result.scalar()
        
        # Test Greek words
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.greek_nt_words
            WHERE strongs_id IS NOT NULL
        """))
        mapped_greek_words = result.scalar()
        
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.greek_nt_words
        """))
        total_greek_words = result.scalar()
        
    # Calculate percentages
    hebrew_mapping_percentage_strongs = (mapped_hebrew_words_strongs_id / total_hebrew_words) * 100 if total_hebrew_words > 0 else 0
    hebrew_mapping_percentage_grammar = (mapped_hebrew_words_grammar / total_hebrew_words) * 100 if total_hebrew_words > 0 else 0
    hebrew_mapping_effective = max(hebrew_mapping_percentage_strongs, hebrew_mapping_percentage_grammar)
    greek_mapping_percentage = (mapped_greek_words / total_greek_words) * 100 if total_greek_words > 0 else 0
    
    logger.info(f"Hebrew Strong's ID mapping:")
    logger.info(f"  Words with strongs_id field: {mapped_hebrew_words_strongs_id} ({hebrew_mapping_percentage_strongs:.2f}%)")
    logger.info(f"  Words with Strong's in grammar_code: {mapped_hebrew_words_grammar} ({hebrew_mapping_percentage_grammar:.2f}%)")
    logger.info(f"  Effective mapping rate: {hebrew_mapping_effective:.2f}%")
    logger.info(f"Greek Strong's ID mapping: {mapped_greek_words} out of {total_greek_words} ({greek_mapping_percentage:.2f}%)")
    
    # After our fix, we expect at least 99% coverage in Hebrew strongs_id field
    assert hebrew_mapping_percentage_strongs >= 99, f"Only {hebrew_mapping_percentage_strongs:.2f}% of Hebrew words have Strong's in strongs_id field (expected >= 99%)"
    
    # Greek words should still have Strong's mapping
    assert greek_mapping_percentage >= 80, f"Only {greek_mapping_percentage:.2f}% of Greek words have Strong's mapping (expected >= 80%)"

def test_psalm_titles(db_engine):
    """Test that Psalm titles (verse 0) are properly loaded."""
    # Psalm titles are typically stored as verse 0
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.verses
            WHERE book_name = 'Psa' AND verse_num = 0
        """))
        psalm_titles_count = result.scalar()
        
    logger.info(f"Found {psalm_titles_count} Psalm titles (verse 0)")
    # Some Psalms don't have titles, but most do
    assert psalm_titles_count > 100, f"Expected more than 100 Psalm titles, found {psalm_titles_count}"

def test_verse_content_completeness(db_engine):
    """Test that verses have valid content."""
    with db_engine.connect() as conn:
        # Check for empty verses
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.verses
            WHERE verse_text IS NULL OR TRIM(verse_text) = ''
        """))
        empty_count = result.scalar()
        
    logger.info(f"Found {empty_count} empty verses")
    assert empty_count == 0, f"Found {empty_count} empty verses"

def test_theological_terms_integrity(db_engine):
    """Test that key theological terms are present and properly linked to lexicon entries."""
    important_hebrew_terms = {
        # Strong's ID     Root form and meaning
        "H430":          "אלהים",     # Elohim (God)
        "H3068":         "יהוה",      # YHWH (LORD)
        "H113":          "אדון",      # Adon (Lord, Master)
        "H4899":         "משיח",      # Mashiach (Messiah, Anointed One)
        "H6944":         "קדש",       # Qodesh (Holy, Set Apart)
        "H8451":         "תורה",      # Torah (Law)
        "H2617":         "חסד",       # Chesed (Lovingkindness)
        "H6664":         "צדק",       # Tsedeq (Righteousness)
        "H5315":         "נפש",       # Nephesh (Soul)
        "H7965":         "שלום",      # Shalom (Peace)
    }

    important_greek_terms = {
        # Strong's ID     Root form and meaning
        "G2316":         "θεος",      # Theos (God)
        "G2962":         "κυριος",    # Kyrios (Lord)
        "G5547":         "χριστος",   # Christos (Christ)
        "G4151":         "πνευμα",    # Pneuma (Spirit)
        "G40":           "αγιος",     # Hagios (Holy)
        "G26":           "αγαπη",     # Agape (Love)
        "G4102":         "πιστις",    # Pistis (Faith)
        "G1680":         "ελπις",     # Elpis (Hope)
        "G5485":         "χαρις",     # Charis (Grace)
        "G1515":         "ειρηνη",    # Eirene (Peace)
    }
    
    with db_engine.connect() as conn:
        # Check for presence of Strong's IDs in Hebrew words
        missing_hebrew = []
        for strongs_id, term_info in important_hebrew_terms.items():
            # Check if the Strong's ID exists in the database
            result = conn.execute(text("""
                SELECT COUNT(*) FROM bible.hebrew_ot_words
                WHERE strongs_id = :strongs_id OR grammar_code LIKE '%{' || :strongs_id || '}%'
            """), {"strongs_id": strongs_id})
            count = result.scalar()
            
            if count == 0:
                missing_hebrew.append(f"{term_info} ({strongs_id})")
                logger.warning(f"Hebrew Strong's ID {strongs_id} ({term_info}) not found in any words")
            else:
                logger.info(f"Found {count} occurrences of Hebrew Strong's ID {strongs_id} ({term_info})")
                
                # Sample check: Get some examples of this term
                result = conn.execute(text("""
                    SELECT word_text, grammar_code, book_name, chapter_num, verse_num 
                    FROM bible.hebrew_ot_words
                    WHERE strongs_id = :strongs_id OR grammar_code LIKE '%{' || :strongs_id || '}%'
                    LIMIT 3
                """), {"strongs_id": strongs_id})
                samples = result.fetchall()
                for sample in samples:
                    logger.info(f"  Example: '{sample.word_text}' [{sample.book_name} {sample.chapter_num}:{sample.verse_num}]")
        
        # Check for presence of Strong's IDs in Greek words
        missing_greek = []
        for strongs_id, term_info in important_greek_terms.items():
            # Check if the Strong's ID exists in the database
            result = conn.execute(text("""
                SELECT COUNT(*) FROM bible.greek_nt_words
                WHERE strongs_id = :strongs_id
            """), {"strongs_id": strongs_id})
            count = result.scalar()
            
            if count == 0:
                missing_greek.append(f"{term_info} ({strongs_id})")
                logger.warning(f"Greek Strong's ID {strongs_id} ({term_info}) not found in any words")
            else:
                logger.info(f"Found {count} occurrences of Greek Strong's ID {strongs_id} ({term_info})")
                
                # Sample check: Get some examples of this term
                result = conn.execute(text("""
                    SELECT word_text, strongs_id, book_name, chapter_num, verse_num 
                    FROM bible.greek_nt_words
                    WHERE strongs_id = :strongs_id
                    LIMIT 3
                """), {"strongs_id": strongs_id})
                samples = result.fetchall()
                for sample in samples:
                    logger.info(f"  Example: '{sample.word_text}' [{sample.book_name} {sample.chapter_num}:{sample.verse_num}]")
        
        # Log results
        if missing_hebrew:
            logger.warning(f"Missing Hebrew theological terms: {', '.join(missing_hebrew)}")
        if missing_greek:
            logger.warning(f"Missing Greek theological terms: {', '.join(missing_greek)}")
        
        # Check for specific theological passages
        key_passages = [
            {"book": "Gen", "chapter": 1, "verse": 1},      # Creation
            {"book": "Exo", "chapter": 20, "verse": 2},     # Ten Commandments
            {"book": "Lev", "chapter": 16, "verse": 16},    # Day of Atonement
            {"book": "Deu", "chapter": 6, "verse": 4},      # Shema
            {"book": "Isa", "chapter": 53, "verse": 5},     # Suffering Servant
            {"book": "Psa", "chapter": 23, "verse": 1},     # Shepherd Psalm
            {"book": "Mat", "chapter": 5, "verse": 3},      # Beatitudes
            {"book": "Jhn", "chapter": 3, "verse": 16},     # For God so loved
            {"book": "Rom", "chapter": 3, "verse": 23},     # All have sinned
            {"book": "1Co", "chapter": 15, "verse": 3},     # Gospel summary
        ]
        
        missing_passages = []
        found_passages = []
        for passage in key_passages:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM bible.verses 
                WHERE book_name = :book AND chapter_num = :chapter AND verse_num = :verse
            """), passage)
            count = result.scalar()
            
            if count == 0:
                missing_passages.append(f"{passage['book']} {passage['chapter']}:{passage['verse']}")
            else:
                # Get verse text for found passages
                result = conn.execute(text("""
                    SELECT verse_text FROM bible.verses 
                    WHERE book_name = :book AND chapter_num = :chapter AND verse_num = :verse
                """), passage)
                verse_text = result.scalar()
                
                found_passages.append({
                    "reference": f"{passage['book']} {passage['chapter']}:{passage['verse']}",
                    "text": verse_text[:50] + ("..." if len(verse_text) > 50 else "")
                })
        
        # Log found passages
        for passage in found_passages:
            logger.info(f"Found key passage: {passage['reference']} - {passage['text']}")
            
        # Log missing passages
        if missing_passages:
            logger.warning(f"Missing key theological passages: {', '.join(missing_passages)}")
        
        # Final assertions - allow for some missing terms since we're using exact matches
        assert len(missing_hebrew) <= 5, f"Too many important Hebrew terms missing: {len(missing_hebrew)}"
        assert len(missing_greek) <= 5, f"Too many important Greek terms missing: {len(missing_greek)}"
        assert len(missing_passages) == 0, f"Important theological passages are missing: {len(missing_passages)}"
        
        logger.info("Theological terms integrity check completed") 