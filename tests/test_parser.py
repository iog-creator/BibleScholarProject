"""
Test the TVTMS parser.
"""

import os
import pytest
from tvtms.parser import TVTMSParser
from tvtms.models import Mapping, Rule, Documentation

pytestmark = pytest.mark.skipif(
    not os.getenv('DATABASE_URL'),
    reason='DATABASE_URL not set; skipping DB-dependent parser tests (see Cursor rule db_test_skip.mdc)'
)

def test_parse_file():
    """Test parsing the TVTMS file."""
    parser = TVTMSParser()
    file_path = 'data/raw/TVTMS_expanded.txt'  # Use authoritative TXT file
    
    # Ensure file exists
    assert os.path.exists(file_path), f"Test file not found: {file_path}"
    
    # Parse file
    result = parser.parse_file(file_path)
    # Support both (mappings, rules, documentation) and just mappings
    if isinstance(result, tuple) and len(result) == 3:
        mappings, rules, documentation = result
    else:
        mappings = result
        rules = []
        documentation = []
    
    # Verify we got some data
    assert len(mappings) > 0, "No mappings found"
    # Only check rules/documentation if present
    if rules is not None:
        assert isinstance(rules, list)
    if documentation is not None:
        assert isinstance(documentation, list)
    
    # Verify first mapping has required fields
    first_mapping = mappings[0]
    assert isinstance(first_mapping, Mapping)
    assert first_mapping.source_tradition
    assert first_mapping.target_tradition
    assert first_mapping.source_book
    assert first_mapping.target_book
    assert first_mapping.mapping_type in {'standard', 'renumbering', 'merge_prev', 'merge_next', 'omit', 'split', 'insert'}
    assert first_mapping.category in {'Opt', 'Nec', 'Acd', 'Inf', 'None'}
    
    # Verify first rule has required fields
    first_rule = rules[0]
    assert isinstance(first_rule, Rule)
    assert first_rule.rule_type
    assert first_rule.content
    assert isinstance(first_rule.applies_to, list)
    
    # Verify first documentation has required fields
    first_doc = documentation[0]
    assert isinstance(first_doc, Documentation)
    assert first_doc.content
    assert first_doc.category
    assert isinstance(first_doc.applies_to, list)
    assert isinstance(first_doc.meta_data, dict)

def test_parse_reference():
    """Test parsing book references."""
    parser = TVTMSParser()
    
    # Test basic reference
    refs = parser.parse_reference("Gen.1:1")
    assert len(refs) == 1
    assert refs[0]['book'] == 'Gen'
    assert refs[0]['chapter'] == 1
    assert refs[0]['verse'] == 1
    assert not refs[0].get('subverse')
    
    # Test reference with subverse
    refs = parser.parse_reference("Gen.1:1.1")
    assert len(refs) == 1
    assert refs[0]['book'] == 'Gen'
    assert refs[0]['chapter'] == 1
    assert refs[0]['verse'] == 1
    assert refs[0]['subverse'] == '1'
    
    # Test multiple references
    refs = parser.parse_reference("Gen.1:1 Gen.1:2")
    assert len(refs) == 2
    assert refs[0]['verse'] == 1
    assert refs[1]['verse'] == 2

def test_normalize_mapping_type():
    """Test mapping type normalization."""
    parser = TVTMSParser()
    
    # Test standard mappings
    assert parser.normalize_mapping_type("Keep verse") == "standard"
    assert parser.normalize_mapping_type("Standard") == "standard"
    assert parser.normalize_mapping_type("identical") == "standard"
    
    # Test merge mappings
    assert parser.normalize_mapping_type("MergedPrev verse") == "merge_prev"
    assert parser.normalize_mapping_type("MergedNext verse") == "merge_next"
    assert parser.normalize_mapping_type("merge prev") == "merge_prev"
    
    # Test special cases
    assert parser.normalize_mapping_type("IfEmpty verse") == "omit"
    assert parser.normalize_mapping_type("SubdividedVerse") == "split"
    assert parser.normalize_mapping_type("LongVerse") == "insert"

@pytest.fixture
def parser():
    """Create a parser instance."""
    return TVTMSParser()

def test_parse_reference_standard():
    """Test parsing standard references."""
    parser = TVTMSParser()
    
    # Test standard reference
    refs = parser.parse_reference("Gen.1:1")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '1',
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }
    
    # Test reference with subverse
    refs = parser.parse_reference("Gen.1:1.1")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '1',
        'verse': 1,
        'subverse': '1',
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }

def test_parse_reference_letter_chapters():
    """Test parsing references with letter chapters."""
    parser = TVTMSParser()
    
    # Test Additions to Esther
    refs = parser.parse_reference("Est.A:1")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Est',
        'chapter': 'A',
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }
    
    # Test with subverse
    refs = parser.parse_reference("Est.A:1.1")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Est',
        'chapter': 'A',
        'verse': 1,
        'subverse': '1',
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }

def test_parse_reference_special_markers():
    """Test parsing references with special markers."""
    parser = TVTMSParser()
    
    # Test !a marker
    refs = parser.parse_reference("!a")
    assert len(refs) == 1
    assert refs[0] == {
        'book': None,
        'chapter': None,
        'verse': None,
        'subverse': None,
        'manuscript': '!a',
        'annotation': None,
        'range_note': None
    }
    
    # Test manuscript marker
    refs = parser.parse_reference("Gen.1:1 (LXX)")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '1',
        'verse': 1,
        'subverse': None,
        'manuscript': 'LXX',
        'annotation': None,
        'range_note': None
    }
    
    # Test annotation
    refs = parser.parse_reference("Gen.1:1 [=Gen.1:2]")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '1',
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': '[=Gen.1:2]',
        'range_note': None
    }

def test_parse_reference_ranges():
    """Test parsing reference ranges."""
    parser = TVTMSParser()
    
    # Test standard range
    refs = parser.parse_reference("Gen.1:1-3")
    assert len(refs) == 3
    for i, ref in enumerate(refs, 1):
        assert ref == {
            'book': 'Gen',
            'chapter': '1',
            'verse': i,
            'subverse': None,
            'manuscript': None,
            'annotation': None,
            'range_note': f"Part of range Gen.1:1-3"
        }
    
    # Test range with letter chapters
    refs = parser.parse_reference("Est.A:1-3")
    assert len(refs) == 3
    for i, ref in enumerate(refs, 1):
        assert ref == {
            'book': 'Est',
            'chapter': 'A',
            'verse': i,
            'subverse': None,
            'manuscript': None,
            'annotation': None,
            'range_note': f"Part of range Est.A:1-3"
        }
    
    # Test cross-chapter range
    refs = parser.parse_reference("Gen.1:1-2:3")
    assert len(refs) == 2
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '1',
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': "Start of range Gen.1:1-2:3"
    }
    assert refs[1] == {
        'book': 'Gen',
        'chapter': '2',
        'verse': 3,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': "End of range Gen.1:1-2:3"
    }

def test_parse_reference_relative():
    """Test parsing relative references."""
    parser = TVTMSParser()
    parser.current_book = 'Gen'
    
    # Test relative verse
    refs = parser.parse_reference("2", 'Gen')
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '1',
        'verse': 2,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }
    
    # Test relative chapter:verse
    refs = parser.parse_reference("2:3", 'Gen')
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '2',
        'verse': 3,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }

def test_parse_reference_invalid():
    """Test parsing invalid references."""
    parser = TVTMSParser()
    
    # Test empty reference
    assert parser.parse_reference("") == []
    
    # Test invalid format
    assert parser.parse_reference("invalid") == []
    
    # Test invalid chapter
    assert parser.parse_reference("Gen.invalid:1") == []
    
    # Test invalid verse
    assert parser.parse_reference("Gen.1:invalid") == []

def test_normalize_category():
    """Test category normalization."""
    parser = TVTMSParser()
    
    assert parser.normalize_category("Opt") == "Opt"
    assert parser.normalize_category("Opt.") == "Opt"
    assert parser.normalize_category("Optional") == "Opt"
    assert parser.normalize_category("Nec") == "Nec"
    assert parser.normalize_category("Necessary") == "Nec"
    assert parser.normalize_category("Acd") == "Acd"
    assert parser.normalize_category("Academic") == "Acd"
    assert parser.normalize_category("Inf") == "Inf"
    assert parser.normalize_category("Information") == "Inf"
    assert parser.normalize_category("") == "None"
    assert parser.normalize_category("Invalid") == "None"

def test_normalize_mapping_type():
    """Test mapping type normalization."""
    parser = TVTMSParser()
    
    assert parser.normalize_mapping_type("standard") == "standard"
    assert parser.normalize_mapping_type("Keep verse") == "standard"
    assert parser.normalize_mapping_type("renumbering") == "renumbering"
    assert parser.normalize_mapping_type("Renumber verse") == "renumbering"
    assert parser.normalize_mapping_type("merge_prev") == "merge_prev"
    assert parser.normalize_mapping_type("MergedPrev verse") == "merge_prev"
    assert parser.normalize_mapping_type("merge_next") == "merge_next"
    assert parser.normalize_mapping_type("MergedNext verse") == "merge_next"
    assert parser.normalize_mapping_type("omit") == "omit"
    assert parser.normalize_mapping_type("IfEmpty verse") == "omit"
    assert parser.normalize_mapping_type("split") == "split"
    assert parser.normalize_mapping_type("SubdividedVerse") == "split"
    assert parser.normalize_mapping_type("insert") == "insert"
    assert parser.normalize_mapping_type("LongVerse") == "insert"
    assert parser.normalize_mapping_type("") == "standard"
    assert parser.normalize_mapping_type("invalid") == "standard"

def test_parse_standard_reference():
    """Test parsing standard verse references."""
    parser = TVTMSParser()
    
    # Test basic reference
    refs = parser.parse_reference("Gen.1:1")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '1',
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }
    
    # Test with subverse
    refs = parser.parse_reference("Gen.1:1.a")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '1',
        'verse': 1,
        'subverse': 'a',
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }

def test_parse_letter_chapters():
    """Test parsing letter chapters."""
    parser = TVTMSParser()
    
    # Test Additions to Esther chapter A
    refs = parser.parse_reference("Est.A:1")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Est',
        'chapter': 'A',
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }
    
    # Test with subverse
    refs = parser.parse_reference("Est.A:1.a")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Est',
        'chapter': 'A',
        'verse': 1,
        'subverse': 'a',
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }
    
    # Test range with letter chapters
    refs = parser.parse_reference("Est.A:1-B:3")
    assert len(refs) == 2
    assert refs[0] == {
        'book': 'Est',
        'chapter': 'A',
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': 'Start of range Est.A:1-B:3'
    }
    assert refs[1] == {
        'book': 'Est',
        'chapter': 'B',
        'verse': 3,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': 'End of range Est.A:1-B:3'
    }

def test_parse_special_markers():
    """Test parsing special markers."""
    parser = TVTMSParser()
    
    # Test !a marker
    refs = parser.parse_reference("!a")
    assert len(refs) == 1
    assert refs[0] == {
        'book': None,
        'chapter': None,
        'verse': None,
        'subverse': None,
        'manuscript': '!a',
        'annotation': None,
        'range_note': None
    }
    
    # Test !b marker
    refs = parser.parse_reference("!b")
    assert len(refs) == 1
    assert refs[0] == {
        'book': None,
        'chapter': None,
        'verse': None,
        'subverse': None,
        'manuscript': '!b',
        'annotation': None,
        'range_note': None
    }
    
    # Test manuscript marker
    refs = parser.parse_reference("Gen.1:1(LXX)")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '1',
        'verse': 1,
        'subverse': None,
        'manuscript': 'LXX',
        'annotation': None,
        'range_note': None
    }

def test_parse_annotations():
    """Test parsing annotations."""
    parser = TVTMSParser()
    
    # Test basic annotation
    refs = parser.parse_reference("Gen.1:1[=Gen.2:3]")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '1',
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': '[=Gen.2:3]',
        'range_note': None
    }
    
    # Test annotation with manuscript marker
    refs = parser.parse_reference("Gen.1:1(LXX)[=Gen.2:3]")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '1',
        'verse': 1,
        'subverse': None,
        'manuscript': 'LXX',
        'annotation': '[=Gen.2:3]',
        'range_note': None
    }

def test_parse_ranges():
    """Test parsing verse ranges."""
    parser = TVTMSParser()
    
    # Test simple range
    refs = parser.parse_reference("Gen.1:1-3")
    assert len(refs) == 3
    for i, ref in enumerate(refs, 1):
        assert ref == {
            'book': 'Gen',
            'chapter': '1',
            'verse': i,
            'subverse': None,
            'manuscript': None,
            'annotation': None,
            'range_note': f"Part of range Gen.1:1-3"
        }
    
    # Test cross-chapter range
    refs = parser.parse_reference("Gen.1:1-2:3")
    assert len(refs) == 2
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '1',
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': 'Start of range Gen.1:1-2:3'
    }
    assert refs[1] == {
        'book': 'Gen',
        'chapter': '2',
        'verse': 3,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': 'End of range Gen.1:1-2:3'
    }
    
    # Test relative range
    refs = parser.parse_reference("Gen.1:1-3", "Gen")
    assert len(refs) == 3
    for i, ref in enumerate(refs, 1):
        assert ref == {
            'book': 'Gen',
            'chapter': '1',
            'verse': i,
            'subverse': None,
            'manuscript': None,
            'annotation': None,
            'range_note': f"Part of range Gen.1:1-3"
        }

def test_parse_relative_references():
    """Test parsing relative references."""
    parser = TVTMSParser()
    
    # Test relative verse
    refs = parser.parse_reference("2:3", "Gen")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '2',
        'verse': 3,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }
    
    # Test relative verse with subverse
    refs = parser.parse_reference("2:3.a", "Gen")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Gen',
        'chapter': '2',
        'verse': 3,
        'subverse': 'a',
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }

def test_parse_psalm_titles():
    """Test parsing Psalm titles."""
    parser = TVTMSParser()
    
    # Test basic title
    refs = parser.parse_reference("Psa.3:title")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Psa',
        'chapter': '3',
        'verse': 0,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }
    
    # Test title with subverse
    refs = parser.parse_reference("Psa.3:title.a")
    assert len(refs) == 1
    assert refs[0] == {
        'book': 'Psa',
        'chapter': '3',
        'verse': 0,
        'subverse': 'a',
        'manuscript': None,
        'annotation': None,
        'range_note': None
    }

def test_invalid_references():
    """Test handling of invalid references."""
    parser = TVTMSParser()
    
    # Test empty reference
    assert parser.parse_reference("") == []
    
    # Test invalid book
    assert parser.parse_reference("InvalidBook.1:1") == []
    
    # Test invalid chapter
    assert parser.parse_reference("Gen.0:1") == []
    
    # Test invalid verse
    assert parser.parse_reference("Gen.1:-1") == []
    
    # Test malformed reference
    assert parser.parse_reference("Gen1:1") == []
    assert parser.parse_reference("Gen.1.1") == []
    assert parser.parse_reference("Gen:1:1") == [] 