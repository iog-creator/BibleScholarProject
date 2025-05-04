"""
Unit tests for model validation.
"""

import pytest
from tvtms.models import Mapping, Rule, Documentation

def test_mapping_validation():
    """Test validation of mapping objects."""
    # Valid mapping
    valid_mapping = Mapping(
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
        target_range_note=None
    )
    assert valid_mapping.is_valid()

    # Invalid category
    invalid_mapping = Mapping(
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
        category="Invalid",  # Invalid category
        notes="Test note",
        source_range_note=None,
        target_range_note=None
    )
    with pytest.raises(ValueError, match="Invalid category"):
        invalid_mapping.is_valid()

    # Missing required field
    invalid_mapping = Mapping(
        source_tradition="",  # Empty required field
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
        target_range_note=None
    )
    with pytest.raises(ValueError, match="Required field"):
        invalid_mapping.is_valid()

    # Invalid numeric value
    invalid_mapping = Mapping(
        source_tradition="Latin",
        target_tradition="standard",
        source_book="Psa",
        source_chapter=0,  # Invalid chapter number
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
        target_range_note=None
    )
    with pytest.raises(ValueError, match="Invalid source_chapter"):
        invalid_mapping.is_valid()

def test_rule_validation():
    """Test validation of rule objects."""
    # Valid rule
    valid_rule = Rule(
        rule_type="conditional",
        content="Test condition",
        section_title=None,
        applies_to=["Latin", "Greek"],
        notes=""
    )
    assert valid_rule.is_valid()

    # Empty applies_to list
    invalid_rule = Rule(
        rule_type="conditional",
        content="Test condition",
        section_title=None,
        applies_to=[],  # Empty list
        notes=""
    )
    with pytest.raises(ValueError, match="applies_to list cannot be empty"):
        invalid_rule.is_valid()

    # Invalid rule type
    invalid_rule = Rule(
        rule_type="invalid",  # Invalid rule type
        content="Test condition",
        section_title=None,
        applies_to=["Latin"],
        notes=""
    )
    with pytest.raises(ValueError, match="Invalid rule type"):
        invalid_rule.is_valid()

    # Missing content
    invalid_rule = Rule(
        rule_type="conditional",
        content="",  # Empty content
        section_title=None,
        applies_to=["Latin"],
        notes=""
    )
    with pytest.raises(ValueError, match="Rule content is required"):
        invalid_rule.is_valid()

def test_documentation_validation():
    """Test validation of documentation objects."""
    # Valid documentation
    valid_doc = Documentation(
        section_title=None,
        content="Test note",
        category="notes",
        applies_to=["Latin"],
        meta_data={"key": "value"}
    )
    assert valid_doc.is_valid()

    # Empty content
    invalid_doc = Documentation(
        section_title=None,
        content="",  # Empty content
        category="notes",
        applies_to=["Latin"],
        meta_data={"key": "value"}
    )
    with pytest.raises(ValueError, match="Documentation content is required"):
        invalid_doc.is_valid()

    # Invalid category
    invalid_doc = Documentation(
        section_title=None,
        content="Test note",
        category="invalid",  # Invalid category
        applies_to=["Latin"],
        meta_data={"key": "value"}
    )
    with pytest.raises(ValueError, match="Invalid category"):
        invalid_doc.is_valid()

    # Empty applies_to list
    invalid_doc = Documentation(
        section_title=None,
        content="Test note",
        category="notes",
        applies_to=[],  # Empty list
        meta_data={"key": "value"}
    )
    with pytest.raises(ValueError, match="applies_to list cannot be empty"):
        invalid_doc.is_valid()

    # Invalid meta_data type
    invalid_doc = Documentation(
        section_title=None,
        content="Test note",
        category="notes",
        applies_to=["Latin"],
        meta_data=[]  # Wrong type
    )
    with pytest.raises(ValueError, match="meta_data must be a dictionary"):
        invalid_doc.is_valid()

def test_range_note_validation():
    """Test validation of range notes."""
    # Valid range notes
    valid_mapping = Mapping(
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
        target_range_note="Part of range Psa.119:175-120:2"
    )
    assert valid_mapping.is_valid()

    # Mismatched range notes
    invalid_mapping = Mapping(
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
        target_range_note=None  # Mismatched range notes
    )
    with pytest.raises(ValueError, match="Source and target range notes must both be present or both be absent"):
        invalid_mapping.is_valid()

def test_cross_reference_validation():
    """Test validation of cross-references between objects."""
    # Create related objects
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
        target_range_note=None
    )

    rule = Rule(
        rule_type="conditional",
        content="Test condition",
        section_title=None,
        applies_to=["Latin"],  # Matches mapping's source_tradition
        notes=""
    )

    doc = Documentation(
        section_title=None,
        content="Test note",
        category="notes",
        applies_to=["Latin"],  # Matches mapping's source_tradition
        meta_data={}
    )

    # Verify cross-references
    assert mapping.source_tradition in rule.applies_to
    assert mapping.source_tradition in doc.applies_to 