"""
Integration tests for ETL pipeline.
"""

import os
import pytest
from sqlalchemy import text
from tvtms.parser import TVTMSParser
from tvtms.database import store_mappings, store_rules, store_documentation

pytestmark = pytest.mark.skipif(
    not os.getenv('DATABASE_URL'),
    reason='DATABASE_URL not set; skipping DB-dependent integration tests (see Cursor rule db_test_skip.mdc)'
)

def test_full_etl_pipeline(test_db_engine, temp_dir, parser):
    """Test full ETL pipeline."""
    content = """2) EXPANDED VERSION
    Latin\tPsa.142:12\tPsa.143:12\tRenumber verse\tOpt.\tNote1\tNote2\tNote3\tTestCondition"""

    file_path = os.path.join(temp_dir, 'test_tvtms.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Parse and store
    mappings, rules, docs = parser.parse_file(file_path)
    store_mappings(mappings, test_db_engine)
    store_rules(rules, test_db_engine)
    store_documentation(docs, test_db_engine)

    # Verify database state
    with test_db_engine.connect() as conn:
        # Check mappings
        result = conn.execute(text("""
            SELECT * FROM versification_mappings
            WHERE source_tradition = 'Latin'
            AND source_book = 'Psa'
            AND source_chapter = 142
            AND source_verse = 12
        """)).fetchone()
        assert result is not None
        assert result.target_book == "Psa"
        assert result.target_chapter == 143
        assert result.target_verse == 12
        assert result.mapping_type == "renumbering"
        assert result.category == "Opt"

        # Check rules
        result = conn.execute(text("SELECT * FROM versification_rules")).fetchone()
        assert result is not None
        assert result.rule_type == "conditional"
        assert result.content == "TestCondition"

        # Check documentation
        result = conn.execute(text("SELECT * FROM versification_documentation")).fetchone()
        assert result is not None
        assert result.content == "Note1"

def test_etl_with_range_references(test_db_engine, temp_dir, parser):
    """Test ETL pipeline with range references."""
    content = """2) EXPANDED VERSION
    Latin\tPsa.119:175-120:2\tPsa.120:1-2\tRenumber verse\tOpt.\tNote1\tNote2\tNote3\tTestCondition"""

    file_path = os.path.join(temp_dir, 'test_tvtms.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Parse and store
    mappings, rules, docs = parser.parse_file(file_path)
    store_mappings(mappings, test_db_engine)

    # Verify range handling
    with test_db_engine.connect() as conn:
        results = conn.execute(text("""
            SELECT source_chapter, source_verse, target_chapter, target_verse,
                   source_range_note, target_range_note
            FROM versification_mappings
            ORDER BY source_chapter, source_verse
        """)).fetchall()
        assert len(results) == 2
        assert results[0].source_chapter == 119
        assert results[0].source_verse == 175
        assert results[0].target_chapter == 120
        assert results[0].target_verse == 1
        assert results[0].source_range_note == "Part of range Psa.119:175-120:2"
        assert results[0].target_range_note == "Part of range Psa.120:1-2"

def test_etl_with_invalid_data(test_db_engine, temp_dir, parser):
    """Test ETL pipeline with invalid data handling."""
    content = """2) EXPANDED VERSION
    Latin\tInvalid.ref\tPsa.143:12\tRenumber verse\tOpt.\tNote1\tNote2\tNote3\tTestCondition
    Greek\tGen.1:1\tInvalid.ref\tKeep verse\tNec.\tNote4\tNote5\tNote6\tTestCondition2
    Hebrew\tRev.13:18\tRev.13:17\tInvalidType\tInvalidCategory\tNote7\tNote8\tNote9\tTestCondition3"""

    file_path = os.path.join(temp_dir, 'test_tvtms.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Parse and store
    mappings, rules, docs = parser.parse_file(file_path)

    # Only valid mappings should be present
    assert len(mappings) == 1  # Only the Rev.13:18->Rev.13:17 mapping should be valid

    store_mappings(mappings, test_db_engine)
    store_rules(rules, test_db_engine)
    store_documentation(docs, test_db_engine)

    # Verify database state
    with test_db_engine.connect() as conn:
        mapping_count = conn.execute(text("""
            SELECT COUNT(*) as count FROM versification_mappings
        """)).scalar()
        assert mapping_count == 1

        rule_count = conn.execute(text("""
            SELECT COUNT(*) as count FROM versification_rules
        """)).scalar()
        assert rule_count == 3  # All rules should be stored

        doc_count = conn.execute(text("""
            SELECT COUNT(*) as count FROM versification_documentation
        """)).scalar()
        assert doc_count == 9  # All documentation entries should be stored

def test_etl_with_empty_file(test_db_engine, temp_dir, parser):
    """Test ETL pipeline with empty file."""
    content = """2) EXPANDED VERSION
    # Just comments and empty lines

    """
    file_path = os.path.join(temp_dir, 'test_tvtms.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Parse and store
    mappings, rules, docs = parser.parse_file(file_path)

    # Should have no data
    assert len(mappings) == 0
    assert len(rules) == 0
    assert len(docs) == 0

    # Should not raise exceptions
    store_mappings(mappings, test_db_engine)
    store_rules(rules, test_db_engine)
    store_documentation(docs, test_db_engine)

    # Verify database state
    with test_db_engine.connect() as conn:
        mapping_count = conn.execute(text("""
            SELECT COUNT(*) as count FROM versification_mappings
        """)).scalar()
        assert mapping_count == 0

        rule_count = conn.execute(text("""
            SELECT COUNT(*) as count FROM versification_rules
        """)).scalar()
        assert rule_count == 0

        doc_count = conn.execute(text("""
            SELECT COUNT(*) as count FROM versification_documentation
        """)).scalar()
        assert doc_count == 0 