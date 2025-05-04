#!/usr/bin/env python3
"""
Test suite for TVTMS processing functionality.
"""

import unittest
import tempfile
import os
from pathlib import Path
from tvtms.parser import TVTMSParser
import pandas as pd
from unittest.mock import patch, MagicMock, PropertyMock
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from tvtms.database import get_db_connection, store_mappings, store_rules, store_documentation
from tvtms.models import Mapping, Rule, Documentation
import sys
import pytest

# Patch store_mappings, store_rules, and store_documentation to no-ops for integration tests
import src.tvtms.database as db_mod

pytestmark = pytest.mark.skipif(
    not os.getenv('DATABASE_URL'),
    reason='DATABASE_URL not set; skipping DB-dependent integration tests (see Cursor rule db_test_skip.mdc)'
)

def noop_store_mappings(conn, mappings):
    pass

def noop_store_rules(conn, rules):
    pass

def noop_store_documentation(conn, docs):
    pass

@patch('tests.test_process_tvtms.store_mappings', new=noop_store_mappings)
@patch('tests.test_process_tvtms.store_rules', new=noop_store_rules)
@patch('tests.test_process_tvtms.store_documentation', new=noop_store_documentation)
@patch('src.tvtms.database.store_mappings', new=noop_store_mappings)
@patch('src.tvtms.database.store_rules', new=noop_store_rules)
@patch('src.tvtms.database.store_documentation', new=noop_store_documentation)
class TestTVTMSProcessing(unittest.TestCase):
    """Test the TVTMS processing functionality."""

    def setUp(self):
        """Set up test environment."""
        self.parser = TVTMSParser(test_mode='integration')
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def create_test_file(self, content):
        """Helper to create a temporary test file."""
        file_path = os.path.join(self.temp_dir, 'test_tvtms.txt')
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content.strip() + '\n')
        return file_path
    
    def test_parse_reference_with_subverse(self):
        """Test parsing of subverse references."""
        ref = "Gen.6:1.1"
        result = self.parser.parse_reference(ref, None)[0]
        self.assertEqual(result, {
            'book': 'Gen', 'chapter': 6, 'verse': 1, 'subverse': '1',
            'manuscript': None, 'annotation': None, 'range_note': None
        })
    
    def test_parse_reference_with_title(self):
        """Test parsing of title references."""
        ref = "Psa.142:Title"
        result = self.parser.parse_reference(ref, None)[0]
        self.assertEqual(result, {
            'book': 'Psa', 'chapter': 142, 'verse': 0, 'subverse': None,
            'manuscript': None, 'annotation': None, 'range_note': None
        })
    
    def test_parse_range_reference(self):
        """Test parsing of range references."""
        ref = "Psa.68:1-3"
        result = self.parser.parse_reference(ref, None)
        expected = [
            {'book': 'Psa', 'chapter': 68, 'verse': 1, 'subverse': None, 'manuscript': None,
             'annotation': None, 'range_note': 'Part of range Psa.68:1-3'},
            {'book': 'Psa', 'chapter': 68, 'verse': 2, 'subverse': None, 'manuscript': None,
             'annotation': None, 'range_note': 'Part of range Psa.68:1-3'},
            {'book': 'Psa', 'chapter': 68, 'verse': 3, 'subverse': None, 'manuscript': None,
             'annotation': None, 'range_note': 'Part of range Psa.68:1-3'}
        ]
        self.assertEqual(result, expected)
    
    def test_parse_annotated_reference(self):
        """Test parsing of annotated references."""
        ref = "Gen.2:25[=Gen.3:1]"
        result = self.parser.parse_reference(ref, None)[0]
        self.assertEqual(result, {
            'book': 'Gen', 'chapter': 2, 'verse': 25, 'subverse': None,
            'manuscript': None, 'annotation': '[=Gen.3:1]', 'range_note': None
        })
    
    def test_parse_manuscript_reference(self):
        """Test parsing of manuscript references."""
        ref = "Rev.13:18(A)"
        result = self.parser.parse_reference(ref, None)[0]
        self.assertEqual(result, {
            'book': 'Rev', 'chapter': 13, 'verse': 18, 'subverse': None,
            'manuscript': 'A', 'annotation': None, 'range_note': None
        })
    
    def test_parse_complex_reference(self):
        """Test parsing of complex references with manuscript and annotation."""
        ref = "Rev.13:18(A)[=Rev.13:17]"
        result = self.parser.parse_reference(ref, None)[0]
        self.assertEqual(result, {
            'book': 'Rev', 'chapter': 13, 'verse': 18, 'subverse': None,
            'manuscript': 'A', 'annotation': '[=Rev.13:17]', 'range_note': None
        })
    
    def test_parse_file_basic(self):
        """Test basic CSV file parsing."""
        content = """2) EXPANDED VERSION
=== Header ===
Gen.1:1\tGen.1:1\tNec\tKeep verse\tNo change
Gen.1:2\tGen.1:2 Gen.1:3\tOpt\tMergedNext verse\tMerged verses"""
        file_path = self.create_test_file(content)
        mappings, rules, docs = self.parser.parse_file(file_path)
        self.assertEqual(len(mappings), 2)  # One mapping for Gen 1:1->1:1 and one for Gen 1:2->1:2,1:3
        self.assertEqual(mappings[0].source_verse, 1)  # First mapping should be verse 1
        self.assertEqual(mappings[1].source_verse, 2)  # Second mapping should be verse 2
        self.assertEqual(mappings[1].category, 'Opt')
        self.assertEqual(mappings[1].mapping_type, 'merge_next')  # Changed from 'merge' to 'merge_next' to match MAPPING_TYPES
    
    def test_parse_file_with_comments(self):
        """Test CSV file parsing with comments."""
        content = """=== Header ===
# This is a comment
Gen.1:1\tGen.1:1\tNec\tKeep verse\tNo change
'Another comment
Gen.1:2\tGen.1:2\tOpt\tKeep verse\tNo change"""
        file_path = self.create_test_file(content)
        mappings, rules, docs = self.parser.parse_file(file_path)
        self.assertEqual(len(mappings), 2)
    
    def test_parse_file_with_invalid_rows(self):
        """Test CSV file parsing with invalid rows."""
        content = """=== Header ===
Invalid line
Gen.1:1\tGen.1:1\tNec\tKeep verse\tNo change
Gen.1:invalid\tGen.1:2\tOpt\tKeep verse\tNo change"""
        file_path = self.create_test_file(content)
        mappings, rules, docs = self.parser.parse_file(file_path)
        self.assertEqual(len(mappings), 1)  # Only one valid mapping should be processed
    
    def test_parse_file_with_empty_fields(self):
        """Test CSV file parsing with empty fields."""
        content = """=== Header ===
Gen.1:1\tGen.1:1\t\t\t
Gen.1:2\tGen.1:2\tOpt\t\tNo notes"""
        file_path = self.create_test_file(content)
        mappings, rules, docs = self.parser.parse_file(file_path)
        self.assertEqual(len(mappings), 2)
        self.assertEqual(mappings[0].category, 'None')  # Default category
        self.assertEqual(mappings[0].mapping_type, 'standard')  # Default mapping type
    
    def test_parse_pandas_line(self):
        """Test parsing a TVTMS.txt line with pandas."""
        test_file = os.path.join(self.temp_dir, 'test_tvtms.txt')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("2) EXPANDED VERSION\n")  # Header
            f.write("Latin\tPsa.142:12\tPsa.143:12\tRenumber verse\tOpt.\tNote1\tNote2\tNote3\tTestCondition\n")
        
        mappings, rules, docs = self.parser.parse_file(test_file)
        self.assertTrue(len(mappings) >= 1)
        self.assertEqual(mappings[0].source_tradition, "Latin")
        self.assertEqual(mappings[0].source_book, "Psa")
        self.assertEqual(mappings[0].source_chapter, 142)
        self.assertEqual(mappings[0].source_verse, 12)
        self.assertEqual(mappings[0].category, "Opt")
        self.assertEqual(len(rules), 1)
        self.assertEqual(len(docs), 3)
    
    def test_parse_pandas_multiple_lines(self):
        """Test parsing multiple lines with pandas."""
        test_file = os.path.join(self.temp_dir, 'test_tvtms.txt')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("2) EXPANDED VERSION\n")
            f.write("Latin\tPsa.142:12\tPsa.143:12\tRenumber verse\tOpt.\tNote1\tNote2\tNote3\tTestCondition\n")
            f.write("Greek\tGen.1:1\tGen.1:1\tKeep verse\tNec.\tNote4\tNote5\tNote6\tTestCondition2\n")
        
        mappings, rules, docs = self.parser.parse_file(test_file)
        self.assertEqual(len(mappings), 2)
        self.assertEqual(mappings[1].source_tradition, "Greek")
        self.assertEqual(mappings[1].source_book, "Gen")
        self.assertEqual(len(rules), 2)
        self.assertEqual(len(docs), 6)
    
    def test_parse_pandas_missing_fields(self):
        """Test parsing with missing fields."""
        test_file = os.path.join(self.temp_dir, 'test_tvtms.txt')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("2) EXPANDED VERSION\n")
            f.write("Latin\tPsa.142:12\tPsa.143:12\n")  # Missing fields
        
        mappings, rules, docs = self.parser.parse_file(test_file)
        self.assertEqual(len(mappings), 1)
        self.assertEqual(mappings[0].category, "None")  # Default category
        self.assertEqual(mappings[0].mapping_type, "standard")  # Default type
    
    def test_parse_pandas_invalid_lines(self):
        """Test handling of invalid lines with pandas."""
        test_file = os.path.join(self.temp_dir, 'test_tvtms.txt')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("2) EXPANDED VERSION\n")
            f.write("# Comment line\n")
            f.write("Invalid line without proper format\n")
            f.write("Latin\tPsa.142:12\tPsa.143:12\tRenumber verse\tOpt.\n")
        
        mappings, rules, docs = self.parser.parse_file(test_file)
        self.assertEqual(len(mappings), 1)
        self.assertEqual(mappings[0].source_tradition, "Latin")
    
    def test_parse_reference_with_range_notes(self):
        """Test parsing references with range notes."""
        ref = "Psa.142:12-143:12"
        refs = self.parser.parse_reference(ref, None)
        self.assertEqual(len(refs), 2)  # Start and end points
        self.assertEqual(refs[0]['book'], "Psa")
        self.assertEqual(refs[0]['chapter'], 142)
        self.assertEqual(refs[0]['verse'], 12)
        self.assertIsNotNone(refs[0]['range_note'])
        self.assertTrue("Part of range" in refs[0]['range_note'])
    
    def test_parse_reference_with_manuscript(self):
        """Test parsing references with manuscript markers."""
        ref = "Gen.1:1(LXX)"
        refs = self.parser.parse_reference(ref, None)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]['book'], "Gen")
        self.assertEqual(refs[0]['manuscript'], "LXX")
    
    def test_database_connection_error(self):
        """Test database connection error handling."""
        # Create test mapping
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

        # Mock SQLAlchemy engine
        with patch('sqlalchemy.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_conn = MagicMock()

            # Set up mock connection to raise error
            mock_conn.execute.side_effect = SQLAlchemyError("Test error")
            mock_engine.begin.return_value.__enter__.return_value = mock_conn
            mock_create_engine.return_value = mock_engine

            # Test error handling
            with self.assertRaises(SQLAlchemyError):
                store_mappings([mapping], mock_engine)

    def test_store_mappings_sqlalchemy(self):
        """Test storing mappings with SQLAlchemy."""
        # Create mock engine and connection
        with patch('sqlalchemy.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_conn = MagicMock()

            # Set up mock connection
            mock_conn.execute.return_value = MagicMock()
            mock_engine.begin.return_value.__enter__.return_value = mock_conn
            mock_create_engine.return_value = mock_engine

            # Create test mapping
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

            # Store mapping
            store_mappings([mapping], mock_engine)

            # Verify the mock was called
            mock_engine.begin.assert_called_once()
            mock_conn.execute.assert_called()

    def test_store_rules_sqlalchemy(self):
        """Test storing rules with SQLAlchemy."""
        with patch('sqlalchemy.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_conn = MagicMock()

            # Set up mock connection
            mock_conn.execute.return_value = MagicMock()
            mock_engine.begin.return_value.__enter__.return_value = mock_conn
            mock_create_engine.return_value = mock_engine

            rule = Rule(
                rule_id=None,
                rule_type="conditional",
                source_tradition="Latin",
                target_tradition="Greek",
                pattern="Test condition",
                description=None
            )

            store_rules([rule], mock_engine)
            mock_engine.begin.assert_called_once()
            mock_conn.execute.assert_called()

    def test_store_documentation_sqlalchemy(self):
        """Test storing documentation with SQLAlchemy."""
        with patch('sqlalchemy.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_conn = MagicMock()

            # Set up mock connection
            mock_conn.execute.return_value = MagicMock()
            mock_engine.begin.return_value.__enter__.return_value = mock_conn
            mock_create_engine.return_value = mock_engine

            doc = Documentation(
                section=None,
                content="Test note"
            )

            store_documentation([doc], mock_engine)
            mock_engine.begin.assert_called_once()
            mock_conn.execute.assert_called()

    def test_sqlalchemy_array_handling(self):
        """Test SQLAlchemy handling of TEXT[] arrays."""
        # Create test rule with array field
        rule = Rule(
            rule_type="conditional",
            content="Test condition",
            section_title=None,
            applies_to=["Latin", "Greek", "Hebrew"],
            notes=""
        )

        # Mock SQLAlchemy engine
        with patch('sqlalchemy.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_conn = MagicMock()

            # Set up mock connection
            mock_conn.execute.return_value = MagicMock()
            mock_engine.begin.return_value.__enter__.return_value = mock_conn
            mock_create_engine.return_value = mock_engine

            # Store rule
            store_rules([rule], mock_engine)

            # Verify the mock was called
            mock_engine.begin.assert_called_once()
            mock_conn.execute.assert_called()

    def test_parse_file_with_range_notes(self):
        """Test parsing file with range notes."""
        content = """2) EXPANDED VERSION
Latin\tPsa.68:1-3\tPsa.68:1-3\tKeep verse\tNec.\tNote1\tNote2\tNote3\tTestCondition"""
        file_path = self.create_test_file(content)
        
        mappings, rules, docs = self.parser.parse_file(file_path)
        
        # Should create 3 mappings for the range
        self.assertEqual(len(mappings), 3)
        
        # Check range notes
        expected_note = "Part of range Psa.68:1-3"
        for mapping in mappings:
            self.assertEqual(mapping.source_range_note, expected_note)
            self.assertEqual(mapping.target_range_note, expected_note)

    def test_category_normalization(self):
        """Test category normalization in pandas processing."""
        content = """2) EXPANDED VERSION
Latin\tPsa.142:12\tPsa.143:12\tRenumber verse\tOpt.\tNote1\tNote2\tNote3\tTestCondition
Greek\tGen.1:1\tGen.1:1\tKeep verse\tNec.\tNote4\tNote5\tNote6\tTestCondition2
Hebrew\tExo.1:1\tExo.1:1\tKeep verse\tAcd.\tNote7\tNote8\tNote9\tTestCondition3"""
        file_path = self.create_test_file(content)
        
        mappings, rules, docs = self.parser.parse_file(file_path)
        
        # Check that categories are normalized (no trailing periods)
        expected_categories = {'Opt', 'Nec', 'Acd'}
        actual_categories = {m.category for m in mappings}
        self.assertEqual(actual_categories, expected_categories)
        
        # Verify no categories have trailing periods
        self.assertTrue(all(not m.category.endswith('.') for m in mappings))

if __name__ == '__main__':
    unittest.main() 