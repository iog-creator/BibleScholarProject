"""
Unit tests for database operations.
"""

import pytest
import json
from sqlalchemy import text
from tvtms.models import Mapping, Rule, Documentation
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch

# --- SQLAlchemy-compatible test store functions ---
def _store_mappings(engine, mappings):
    if not mappings:
        return
    data_to_insert = [
        (
            m.source_tradition,
            m.target_tradition,
            m.source_book,
            m.source_chapter,
            m.source_verse,
            m.source_subverse,
            m.manuscript_marker,
            m.target_book,
            m.target_chapter,
            m.target_verse,
            m.target_subverse,
            m.mapping_type,
            m.category,
            m.notes,
            m.source_range_note,
            m.target_range_note,
            m.note_marker,
            m.ancient_versions
        )
        for m in mappings
    ]
    columns = (
        "source_tradition", "target_tradition", "source_book", "source_chapter",
        "source_verse", "source_subverse", "manuscript_marker", "target_book",
        "target_chapter", "target_verse", "target_subverse", "mapping_type",
        "category", "notes", "source_range_note", "target_range_note",
        "note_marker", "ancient_versions"
    )
    placeholders = ", ".join([":{}".format(col) for col in columns])
    sql = f"""
        INSERT INTO versification_mappings ({', '.join(columns)})
        VALUES ({placeholders})
    """
    with engine.begin() as conn:
        for row in data_to_insert:
            conn.execute(
                text(sql),
                dict(zip(columns, row))
            )

def _store_rules(engine, rules):
    if not rules:
        return
    data_to_insert = [
        (
            r.rule_type,
            r.source_tradition,
            r.target_tradition,
            r.pattern,
            r.description
        ) for r in rules
    ]
    columns = ("rule_type", "source_tradition", "target_tradition", "pattern", "description")
    placeholders = ", ".join([":{}".format(col) for col in columns])
    sql = f"""
        INSERT INTO versification_rules ({', '.join(columns)})
        VALUES ({placeholders})
    """
    with engine.begin() as conn:
        for row in data_to_insert:
            conn.execute(
                text(sql),
                dict(zip(columns, row))
            )

def _store_documentation(engine, docs):
    if not docs:
        return
    data_to_insert = [
        (
            d.section_title,
            d.content,
            d.category,
            d.related_sections,
            d.notes
        ) for d in docs
    ]
    columns = ("section_title", "content", "category", "related_sections", "notes")
    placeholders = ", ".join([":{}".format(col) for col in columns])
    sql = f"""
        INSERT INTO versification_documentation ({', '.join(columns)})
        VALUES ({placeholders})
    """
    with engine.begin() as conn:
        for row in data_to_insert:
            conn.execute(
                text(sql),
                dict(zip(columns, row))
            )
# --- End test store functions ---

def test_store_mappings(test_db_engine):
    """Test storing mappings in the database."""
    # Clear existing data
    with test_db_engine.begin() as conn:
        conn.execute(text("DELETE FROM versification_mappings"))

    mapping = Mapping(
        source_tradition="Latin",
        target_tradition="standard",
        source_book="Psa",
        source_chapter=142,
        source_verse=12,
        source_subverse=None,
        manuscript_marker=None,
        target_book="Psa",
        target_chapter=143,
        target_verse=12,
        target_subverse=None,
        mapping_type="renumbering",
        category="Opt",
        notes="Test note",
        source_range_note=None,
        target_range_note=None,
        note_marker=None,
        ancient_versions=None
    )
    
    _store_mappings(test_db_engine, [mapping])
    
    # Verify storage
    with test_db_engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM versification_mappings")).fetchone()
        assert result is not None
        assert result.source_tradition == "Latin"
        assert result.target_tradition == "standard"
        assert result.source_book == "Psa"
        assert result.source_chapter == 142
        assert result.source_verse == 12
        assert result.target_book == "Psa"
        assert result.target_chapter == 143
        assert result.target_verse == 12
        assert result.mapping_type == "renumbering"
        assert result.category == "Opt"
        assert result.notes == "Test note"

def test_store_rules(test_db_engine):
    """Test storing rules in the database."""
    # Clear existing data
    with test_db_engine.begin() as conn:
        conn.execute(text("DELETE FROM versification_rules"))

    rule = Rule(
        rule_id=None,
        rule_type="conditional",
        source_tradition="Latin",
        target_tradition="Greek",
        pattern="Test condition",
        description=None
    )
    
    _store_rules(test_db_engine, [rule])
    
    # Verify storage
    with test_db_engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM versification_rules")).fetchone()
        assert result is not None
        assert result.rule_type == "conditional"
        assert result.source_tradition == "Latin"
        assert result.target_tradition == "Greek"
        assert result.pattern == "Test condition"
        assert result.description is None

def test_store_documentation(test_db_engine):
    """Test storing documentation in the database."""
    # Clear existing data
    with test_db_engine.begin() as conn:
        conn.execute(text("DELETE FROM versification_documentation"))

    doc = Documentation(
        section_title=None,
        content="Test note",
        category="notes",
        related_sections=None,
        notes=None
    )
    
    _store_documentation(test_db_engine, [doc])
    
    # Verify storage
    with test_db_engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM versification_documentation")).fetchone()
        assert result is not None
        assert result.section_title is None
        assert result.content == "Test note"
        assert result.category == "notes"

def test_store_empty_lists(test_db_engine):
    """Test storing empty lists doesn't cause errors."""
    # These should not raise exceptions
    _store_mappings(test_db_engine, [])
    _store_rules(test_db_engine, [])
    _store_documentation(test_db_engine, [])

def test_store_multiple_mappings(test_db_engine):
    """Test storing multiple mappings in a single transaction."""
    # Clear existing data
    with test_db_engine.begin() as conn:
        conn.execute(text("DELETE FROM versification_mappings"))

    mappings = [
        Mapping(
            source_tradition="Latin",
            target_tradition="standard",
            source_book="Psa",
            source_chapter=142,
            source_verse=12,
            source_subverse=None,
            manuscript_marker=None,
            target_book="Psa",
            target_chapter=143,
            target_verse=12,
            target_subverse=None,
            mapping_type="renumbering",
            category="Opt",
            notes="Test note 1",
            source_range_note=None,
            target_range_note=None,
            note_marker=None,
            ancient_versions=None
        ),
        Mapping(
            source_tradition="Greek",
            target_tradition="standard",
            source_book="Gen",
            source_chapter=1,
            source_verse=1,
            source_subverse=None,
            manuscript_marker=None,
            target_book="Gen",
            target_chapter=1,
            target_verse=1,
            target_subverse=None,
            mapping_type="standard",
            category="Nec",
            notes="Test note 2",
            source_range_note=None,
            target_range_note=None,
            note_marker=None,
            ancient_versions=None
        )
    ]
    
    _store_mappings(test_db_engine, mappings)
    
    # Verify storage
    with test_db_engine.connect() as conn:
        results = conn.execute(text("SELECT * FROM versification_mappings ORDER BY source_tradition")).fetchall()
        assert len(results) == 2
        assert results[0].source_tradition == "Greek"
        assert results[0].notes == "Test note 2"
        assert results[1].source_tradition == "Latin"
        assert results[1].notes == "Test note 1"

def test_store_mapping_with_range_notes(test_db_engine):
    """Test storing mappings with range notes."""
    # Clear existing data
    with test_db_engine.begin() as conn:
        conn.execute(text("DELETE FROM versification_mappings"))

    mapping = Mapping(
        source_tradition="Latin",
        target_tradition="standard",
        source_book="Psa",
        source_chapter=119,
        source_verse=175,
        source_subverse=None,
        manuscript_marker=None,
        target_book="Psa",
        target_chapter=120,
        target_verse=2,
        target_subverse=None,
        mapping_type="renumbering",
        category="Opt",
        notes="Test note",
        source_range_note="Part of range Psa.119:175-120:2",
        target_range_note="Part of range Psa.119:175-120:2",
        note_marker=None,
        ancient_versions=None
    )
    
    _store_mappings(test_db_engine, [mapping])
    
    # Verify storage
    with test_db_engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM versification_mappings")).fetchone()
        assert result is not None
        assert result.source_range_note == "Part of range Psa.119:175-120:2"
        assert result.target_range_note == "Part of range Psa.119:175-120:2"

def test_database_connection_error(test_db_engine):
    """Test database connection error handling."""
    mapping = Mapping(
        source_tradition="Latin",
        target_tradition="standard",
        source_book="Psa",
        source_chapter=142,
        source_verse=12,
        source_subverse=None,
        manuscript_marker=None,
        target_book="Psa",
        target_chapter=143,
        target_verse=12,
        target_subverse=None,
        mapping_type="renumbering",
        category="Opt",
        notes="Test note",
        source_range_note=None,
        target_range_note=None,
        note_marker=None,
        ancient_versions=None
    )

    # Mock SQLAlchemy engine to raise error
    with patch.object(test_db_engine, 'begin') as mock_begin:
        mock_begin.side_effect = SQLAlchemyError("Test error")

        with pytest.raises(SQLAlchemyError):
            _store_mappings(test_db_engine, [mapping]) 