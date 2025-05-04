"""
Shared test fixtures and configuration for STEPBible-Datav2 tests.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
import tempfile
from sqlalchemy import create_engine, text
from tvtms.parser import TVTMSParser

@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine using SQLite."""
    engine = create_engine('sqlite:///:memory:')
    
    # Create tables
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS versification_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_tradition TEXT NOT NULL,
                target_tradition TEXT NOT NULL,
                source_book TEXT NOT NULL,
                source_chapter INTEGER NOT NULL,
                source_verse INTEGER NOT NULL,
                source_subverse TEXT,
                manuscript_marker TEXT,
                target_book TEXT NOT NULL,
                target_chapter INTEGER NOT NULL,
                target_verse INTEGER NOT NULL,
                target_subverse TEXT,
                mapping_type TEXT NOT NULL,
                category TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                source_range_note TEXT,
                target_range_note TEXT
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS versification_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_type TEXT NOT NULL,
                content TEXT NOT NULL,
                section_title TEXT,
                applies_to TEXT,  -- JSON array as text
                notes TEXT NOT NULL DEFAULT ''
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS versification_documentation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_title TEXT,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                applies_to TEXT,  -- JSON array as text
                meta_data TEXT    -- JSON object as text
            )
        """))

    return engine

@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture(scope="session")
def parser():
    """Create a TVTMSParser instance."""
    return TVTMSParser()

@pytest.fixture(scope="function")
def sample_tvtms_file(temp_dir):
    """Create a sample TVTMS file for testing."""
    content = """2) EXPANDED VERSION
Latin\tPsa.142:12\tPsa.143:12\tRenumber verse\tOpt.\tNote1\tNote2\tNote3\tTestCondition
Greek\tGen.1:1-3\tGen.1:1-3\tKeep verse\tNec.\tNote4\tNote5\tNote6\tTestCondition2"""
    
    file_path = os.path.join(temp_dir, 'test_tvtms.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path 