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

def clear_versification_tables_raw(conn):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE bible.versification_mappings RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE bible.versification_rules RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE bible.versification_documentation RESTART IDENTITY CASCADE;")
    conn.commit()

def test_full_etl_pipeline(test_db_engine, temp_dir, parser):
    """Test full ETL pipeline."""
    conn = test_db_engine.raw_connection()
    clear_versification_tables_raw(conn)
    content = """2) EXPANDED VERSION
#DataStart(Expanded)
SourceType\tSourceRef\tStandardRef\tAction\tNoteMarker\tNoteA\tNoteB\tAncient Versions\tTests
Latin\tPsa.1:1\tPsa.1:2\tRenumber verse\tOpt.\tNote1\tNote2\t\tTestCondition
#DataEnd(Expanded)"""
    file_path = os.path.join(temp_dir, 'test_tvtms.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    mappings, rules, docs = parser.parse_file(file_path)
    try:
        store_mappings(mappings, conn)
        store_rules(rules, conn)
        store_documentation(docs, conn)
        with test_db_engine.connect() as check_conn:
            result = check_conn.execute(text("""
                SELECT * FROM bible.versification_mappings
                WHERE source_tradition = 'latin'
                AND source_book = 'Psa'
                AND source_chapter::integer = 1
                AND source_verse::integer = 1
            """)).fetchone()
            assert result is not None
    finally:
        conn.rollback()

def test_etl_with_range_references(test_db_engine, temp_dir, parser):
    """Test ETL pipeline with range references."""
    conn = test_db_engine.raw_connection()
    clear_versification_tables_raw(conn)
    content = """2) EXPANDED VERSION
#DataStart(Expanded)
SourceType\tSourceRef\tStandardRef\tAction\tNoteMarker\tNoteA\tNoteB\tAncient Versions\tTests
Latin\tGen.1:1\tGen.1:2\tRenumber verse\tOpt.\tNote1\tNote2\t\tTestCondition
Latin\tGen.1:3\tGen.1:4\tRenumber verse\tOpt.\tNote1\tNote2\t\tTestCondition
#DataEnd(Expanded)"""
    file_path = os.path.join(temp_dir, 'test_tvtms.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    mappings, rules, docs = parser.parse_file(file_path)
    try:
        store_mappings(mappings, conn)
        with test_db_engine.connect() as check_conn:
            results = check_conn.execute(text("""
                SELECT source_chapter::integer, source_verse::integer, target_chapter::integer, target_verse::integer,
                       source_range_note, target_range_note
                FROM bible.versification_mappings
                WHERE source_book = 'Gen'
                ORDER BY source_chapter::integer, source_verse::integer
            """)).fetchall()
            assert len(results) == 2
    finally:
        conn.rollback()

def test_etl_with_invalid_data(test_db_engine, temp_dir, parser):
    """Test ETL pipeline with invalid data handling."""
    conn = test_db_engine.raw_connection()
    clear_versification_tables_raw(conn)
    content = """2) EXPANDED VERSION
#DataStart(Expanded)
SourceType\tSourceRef\tStandardRef\tAction\tNoteMarker\tNoteA\tNoteB\tAncient Versions\tTests
Latin\tInvalid.ref\tPsa.1:2\tRenumber verse\tOpt.\tNote1\tNote2\t\tTestCondition
Greek\tGen.1:1\tInvalid.ref\tKeep verse\tNec.\tNote4\tNote5\t\tTestCondition2
Hebrew\tRev.1:1\tRev.1:2\tRenumber verse\tOpt.\tNote7\tNote8\t\tTestCondition3
#DataEnd(Expanded)"""
    file_path = os.path.join(temp_dir, 'test_tvtms.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    mappings, rules, docs = parser.parse_file(file_path)
    try:
        store_mappings(mappings, conn)
        with test_db_engine.connect() as check_conn:
            mapping_count = check_conn.execute(text("""
                SELECT COUNT(*) as count FROM bible.versification_mappings
            """)).scalar()
            # Only valid mappings are stored; parser logs invalid refs for DSPy training
            assert mapping_count == 1
    finally:
        conn.rollback()

def test_etl_with_empty_file(test_db_engine, temp_dir, parser):
    """Test ETL pipeline with empty file."""
    conn = test_db_engine.raw_connection()
    clear_versification_tables_raw(conn)
    content = """2) EXPANDED VERSION
#DataStart(Expanded)
SourceType\tSourceRef\tStandardRef\tAction\tNoteMarker\tNoteA\tNoteB\tAncient Versions\tTests
#DataEnd(Expanded)
"""
    file_path = os.path.join(temp_dir, 'test_tvtms.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    mappings, rules, docs = parser.parse_file(file_path)
    try:
        store_mappings(mappings, conn)
        with test_db_engine.connect() as check_conn:
            mapping_count = check_conn.execute(text("""
                SELECT COUNT(*) as count FROM bible.versification_mappings
            """)).scalar()
            assert mapping_count == 0
    finally:
        conn.rollback() 