"""
Unit tests for TVTMS parser functionality.
"""

import pytest
from tvtms.parser import TVTMSParser

@pytest.fixture
def parser():
    """Create a parser instance for testing."""
    return TVTMSParser(test_mode='unit')

def test_parse_reference_with_subverse(parser):
    """Test parsing of subverse references."""
    ref = "Gen.6:1.1"
    result = parser.parse_reference(ref, None)
    assert len(result) == 1
    assert result[0] == {
        'book': 'Gen',
        'chapter': 6,
        'verse': 1,
        'subverse': '1',
        'manuscript': None,
        'annotation': None,
        'range_note': None,
        'special_marker': None,
        'marker_type': None
    }

def test_parse_reference_with_title(parser):
    """Test parsing of title references."""
    ref = "Psa.142:Title"
    result = parser.parse_reference(ref, None)[0]
    assert result == {
        'book': 'Psa', 'chapter': 142, 'verse': 0, 'subverse': None,
        'manuscript': None, 'annotation': None, 'range_note': None,
        'special_marker': None, 'marker_type': None
    }

def test_parse_letter_chapter(parser):
    """Test parsing of letter chapter references."""
    # Test basic letter chapter
    ref = "Est.A:1"
    result = parser.parse_reference(ref, None)[0]
    assert result == {
        'book': 'Additions to Esther',
        'chapter': 'A',
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None,
        'special_marker': None,
        'marker_type': None
    }

    # Test letter chapter with subverse
    ref = "Est.A:1.a"
    result = parser.parse_reference(ref, None)[0]
    assert result == {
        'book': 'Additions to Esther',
        'chapter': 'A',
        'verse': 1,
        'subverse': 'a',
        'manuscript': None,
        'annotation': None,
        'range_note': None,
        'special_marker': None,
        'marker_type': None
    }

    # Test letter chapter range
    ref = "Est.A:1-3"
    result = parser.parse_reference(ref, None)
    assert len(result) == 3
    for i, verse in enumerate(range(1, 4), 0):
        assert result[i] == {
            'book': 'Additions to Esther',
            'chapter': 'A',
            'verse': verse,
            'subverse': None,
            'manuscript': None,
            'annotation': None,
            'range_note': f"Part of range {ref}",
            'special_marker': None,
            'marker_type': None
        }

def test_parse_special_markers(parser):
    """Test parsing of special markers."""
    # Test !a marker
    ref = "!a"
    result = parser.parse_reference(ref, None)[0]
    assert result == {
        'book': None,
        'chapter': None,
        'verse': None,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None,
        'special_marker': '!a',
        'marker_type': 'First alternative reading'
    }

    # Test !b marker
    ref = "!b"
    result = parser.parse_reference(ref, None)[0]
    assert result == {
        'book': None,
        'chapter': None,
        'verse': None,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None,
        'special_marker': '!b',
        'marker_type': 'Second alternative reading'
    }

    # Test !LXX marker
    ref = "!LXX"
    result = parser.parse_reference(ref, None)[0]
    assert result == {
        'book': None,
        'chapter': None,
        'verse': None,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None,
        'special_marker': '!LXX',
        'marker_type': 'Septuagint reading'
    }

def test_parse_manuscript_markers(parser):
    """Test parsing of manuscript markers."""
    # Test LXX manuscript
    ref = "Gen.1:1(LXX)"
    result = parser.parse_reference(ref, None)[0]
    assert result == {
        'book': 'Gen',
        'chapter': 1,
        'verse': 1,
        'subverse': None,
        'manuscript': 'LXX',
        'annotation': None,
        'range_note': None,
        'special_marker': None,
        'marker_type': None
    }

def test_parse_annotations(parser):
    """Test parsing of annotations."""
    # Test basic annotation
    ref = "Gen.1:1[=Gen.1:2]"
    result = parser.parse_reference(ref, None)[0]
    assert result == {
        'book': 'Gen',
        'chapter': 1,
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': 'Gen.1:2',
        'range_note': None,
        'special_marker': None,
        'marker_type': None
    }

def test_parse_complex_references(parser):
    """Test parsing of complex references with multiple features."""
    # Test letter chapter with manuscript and annotation
    ref = "Est.A:1(LXX)[=Est.1:1]"
    result = parser.parse_reference(ref, None)[0]
    assert result == {
        'book': 'Additions to Esther',
        'chapter': 'A',
        'verse': 1,
        'subverse': None,
        'manuscript': 'LXX',
        'annotation': 'Est.1:1',
        'range_note': None,
        'special_marker': None,
        'marker_type': None
    }

    # Test letter chapter range with manuscript
    ref = "Est.A:1-B:3(LXX)"
    result = parser.parse_reference(ref, None)
    assert len(result) == 2
    assert result[0] == {
        'book': 'Additions to Esther',
        'chapter': 'A',
        'verse': 1,
        'subverse': None,
        'manuscript': 'LXX',
        'annotation': None,
        'range_note': f"Start of range {ref}",
        'special_marker': None,
        'marker_type': None
    }
    assert result[1] == {
        'book': 'Additions to Esther',
        'chapter': 'B',
        'verse': 3,
        'subverse': None,
        'manuscript': 'LXX',
        'annotation': None,
        'range_note': f"End of range {ref}",
        'special_marker': None,
        'marker_type': None
    }

def test_parse_invalid_references(parser):
    """Test handling of invalid references."""
    # Test empty reference
    assert parser.parse_reference("") == []
    
    # Test invalid book
    assert parser.parse_reference("InvalidBook.1:1") == []
    
    # Test invalid chapter
    assert parser.parse_reference("Gen.0:1") == []
    
    # Test invalid verse
    assert parser.parse_reference("Gen.1:-1") == []
    
    # Test invalid letter chapter
    assert parser.parse_reference("Est.G:1") == []  # Only A-F allowed
    
    # Test invalid special marker
    assert parser.parse_reference("!invalid") == [{
        'book': None,
        'chapter': None,
        'verse': None,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None,
        'special_marker': '!invalid',
        'marker_type': 'Unknown marker'
    }]

def test_parse_range_reference(parser):
    """Test parsing of range references."""
    ref = "Psa.68:1-3"
    result = parser.parse_reference(ref, None)
    assert len(result) == 3
    for i, verse in enumerate(range(1, 4), 0):
        assert result[i] == {
            'book': 'Psa',
            'chapter': 68,
            'verse': verse,
            'subverse': None,
            'manuscript': None,
            'annotation': None,
            'range_note': f"Part of range {ref}",
            'special_marker': None,
            'marker_type': None
        }

def test_parse_cross_chapter_range(parser):
    """Test parsing of ranges that cross chapter boundaries."""
    ref = "Psa.119:175-120:2"
    result = parser.parse_reference(ref, None)
    assert len(result) == 2
    assert result[0] == {
        'book': 'Psa',
        'chapter': 119,
        'verse': 175,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': f"Start of range {ref}",
        'special_marker': None,
        'marker_type': None
    }
    assert result[1] == {
        'book': 'Psa',
        'chapter': 120,
        'verse': 2,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': f"End of range {ref}",
        'special_marker': None,
        'marker_type': None
    }

def test_parse_cross_book_range(parser):
    """Test parsing of ranges that cross book boundaries."""
    ref = "Mal.4:5-Mat.1:1"
    result = parser.parse_reference(ref, None)
    assert len(result) == 2
    assert result[0] == {
        'book': 'Mal',
        'chapter': 4,
        'verse': 5,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': f"Start of range {ref}",
        'special_marker': None,
        'marker_type': None
    }
    assert result[1] == {
        'book': 'Mat',
        'chapter': 1,
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': f"End of range {ref}",
        'special_marker': None,
        'marker_type': None
    }

def test_parse_relative_references(parser):
    """Test parsing of relative references."""
    # Set current book context
    current_book = "Gen"
    
    # Test relative verse reference
    ref = "1:1"
    result = parser.parse_reference(ref, current_book)[0]
    assert result == {
        'book': 'Gen',
        'chapter': 1,
        'verse': 1,
        'subverse': None,
        'manuscript': None,
        'annotation': None,
        'range_note': None,
        'special_marker': None,
        'marker_type': None
    }
    
    # Test relative verse with subverse
    ref = "1:1.a"
    result = parser.parse_reference(ref, current_book)[0]
    assert result == {
        'book': 'Gen',
        'chapter': 1,
        'verse': 1,
        'subverse': 'a',
        'manuscript': None,
        'annotation': None,
        'range_note': None,
        'special_marker': None,
        'marker_type': None
    }
    
    # Test relative range
    ref = "1:1-3"
    result = parser.parse_reference(ref, current_book)
    assert len(result) == 3
    for i, verse in enumerate(range(1, 4), 0):
        assert result[i] == {
            'book': 'Gen',
            'chapter': 1,
            'verse': verse,
            'subverse': None,
            'manuscript': None,
            'annotation': None,
            'range_note': f"Part of range Gen.{ref}",
            'special_marker': None,
            'marker_type': None
        }

def test_parse_manuscript_reference(parser):
    """Test parsing of manuscript references."""
    ref = "Rev.13:18(A)"
    result = parser.parse_reference(ref, None)[0]
    assert result == {
        'book': 'Rev', 'chapter': 13, 'verse': 18, 'subverse': None,
        'manuscript': 'A', 'annotation': None, 'range_note': None
    }

def test_parse_complex_reference(parser):
    """Test parsing of complex references with manuscript and annotation."""
    ref = "Rev.13:18(A)[=Rev.13:17]"
    result = parser.parse_reference(ref, None)
    assert len(result) == 1
    assert result[0] == {
        'book': 'Rev',
        'chapter': 13,
        'verse': 18,
        'subverse': None,
        'manuscript': 'A',
        'annotation': '=Rev.13:17',
        'range_note': None
    }

def test_parse_annotated_reference(parser):
    """Test parsing of annotated references."""
    ref = "Gen.2:25[=Gen.3:1]"
    result = parser.parse_reference(ref, None)
    assert len(result) == 1
    assert result[0] == {
        'book': 'Gen',
        'chapter': 2,
        'verse': 25,
        'subverse': None,
        'manuscript': None,
        'annotation': '=Gen.3:1',
        'range_note': None
    }

def test_parse_reference_with_current_book(parser):
    """Test parsing references with current book context."""
    current_book = "Gen"
    refs = [
        "1:1",  # Simple verse
        "2:3-5",  # Verse range
        "3:1a",  # Verse with subverse
        "4:1-6:8",  # Chapter range
    ]
    expected = [
        [{'book': 'Gen', 'chapter': 1, 'verse': 1, 'subverse': None, 'manuscript': None, 'annotation': None, 'range_note': None}],
        [
            {'book': 'Gen', 'chapter': 2, 'verse': 3, 'subverse': None, 'manuscript': None, 'annotation': None, 'range_note': 'Part of range Gen.2:3-5'},
            {'book': 'Gen', 'chapter': 2, 'verse': 4, 'subverse': None, 'manuscript': None, 'annotation': None, 'range_note': 'Part of range Gen.2:3-5'},
            {'book': 'Gen', 'chapter': 2, 'verse': 5, 'subverse': None, 'manuscript': None, 'annotation': None, 'range_note': 'Part of range Gen.2:3-5'}
        ],
        [{'book': 'Gen', 'chapter': 3, 'verse': 1, 'subverse': 'a', 'manuscript': None, 'annotation': None, 'range_note': None}],
        [
            {'book': 'Gen', 'chapter': 4, 'verse': 1, 'subverse': None, 'manuscript': None, 'annotation': None, 'range_note': 'Part of range Gen.4:1-6:8'},
            {'book': 'Gen', 'chapter': 6, 'verse': 8, 'subverse': None, 'manuscript': None, 'annotation': None, 'range_note': 'Part of range Gen.4:1-6:8'}
        ]
    ]
    for ref, exp in zip(refs, expected):
        result = parser.parse_reference(ref, current_book)
        assert result == exp, f"Failed to parse reference: {ref}" 