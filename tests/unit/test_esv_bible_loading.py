#!/usr/bin/env python
"""
Unit tests for the ESV Bible ETL process.
Tests the functionality of parsing and loading ESV Bible data.
"""

import unittest
import os
import tempfile
from io import StringIO
import sys
import psycopg2
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.etl.etl_english_bible import parse_esv_bible_file, load_esv_bible_data

class TestESVBibleLoading(unittest.TestCase):
    """Test case for the ESV Bible loading functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a sample ESV Bible content for testing
        self.sample_esv_content = """
TTESV - Tyndale Translation tags for ESV - TyndaleHouse.com STEPBible.org CC BY-NC.txt
============================================================================================
Data created by www.STEPBible.org based on work at Tyndale House Cambridge (CC BY 4.0)
============================================================================================

Gen.1.1 In the beginning, God created the heavens and the earth.
# Strong's: {H7225} {H430} {H1254} {H853} {H8064} {H853} {H776}
# Grammar: PREP N-ms VERB-qal.perf.3ms DDO N-mp DDO N-fs

Gen.1.2 The earth was without form and void, and darkness was over the face of the deep. And the Spirit of God was hovering over the face of the waters.
# Strong's: {H776} {H1961} {H8414} {H922} {H2822} {H5921} {H6440} {H8415} {H7307} {H430} {H7363} {H5921} {H6440} {H4325}

Jhn.3.16 For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.
# Strong's: {G1063} {G3779} {G25} {G2316} {G3588} {G2889} {G5620} {G1325} {G3588} {G3439} {G5207} {G2443}

Rev.22.21 The grace of the Lord Jesus be with all. Amen.
# Strong's: {G5485} {G2962} {G2424} {G5547} {G3326} {G3956} {G281}
"""
        # Create a temporary file with the sample content
        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False)
        self.temp_file.write(self.sample_esv_content)
        self.temp_file.close()

    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary file
        os.unlink(self.temp_file.name)

    def test_parse_esv_bible_file(self):
        """Test parsing an ESV Bible file."""
        # Parse the sample file
        bible_data = parse_esv_bible_file(self.temp_file.name)
        
        # Assert the structure of the returned data
        self.assertIsInstance(bible_data, dict)
        self.assertIn('verses', bible_data)
        self.assertIsInstance(bible_data['verses'], list)
        
        # Assert we got the expected number of verses
        self.assertEqual(len(bible_data['verses']), 4)
        
        # Check the content of the first verse
        self.assertEqual(bible_data['verses'][0]['book_name'], 'Genesis')
        self.assertEqual(bible_data['verses'][0]['chapter_num'], 1)
        self.assertEqual(bible_data['verses'][0]['verse_num'], 1)
        self.assertEqual(bible_data['verses'][0]['verse_text'], 'In the beginning, God created the heavens and the earth.')
        self.assertEqual(bible_data['verses'][0]['translation_source'], 'ESV')
        
        # Check the content of the John 3:16 verse
        jhn_verse = None
        for verse in bible_data['verses']:
            if verse['book_name'] == 'John' and verse['chapter_num'] == 3 and verse['verse_num'] == 16:
                jhn_verse = verse
                break
        
        self.assertIsNotNone(jhn_verse)
        self.assertEqual(jhn_verse['verse_text'], 'For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.')
        self.assertEqual(jhn_verse['translation_source'], 'ESV')

    @patch('src.etl.etl_english_bible.logger')
    def test_parse_esv_bible_file_with_empty_file(self, mock_logger):
        """Test parsing an empty ESV Bible file."""
        # Create an empty temporary file
        empty_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False)
        empty_file.close()
        
        try:
            # Parse the empty file
            bible_data = parse_esv_bible_file(empty_file.name)
            
            # Assert we got an empty verses list
            self.assertEqual(len(bible_data['verses']), 0)
            
            # Check that a warning was logged
            mock_logger.info.assert_called_with(f"Parsed 0 verses from file {empty_file.name}")
        finally:
            # Clean up
            os.unlink(empty_file.name)

    @patch('psycopg2.connect')
    @patch('src.etl.etl_english_bible.logger')
    def test_load_esv_bible_data(self, mock_logger, mock_connect):
        """Test loading ESV Bible data into the database."""
        # Create mock database objects
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock the fetchone method to return a count of 0 (no existing verses)
        mock_cursor.fetchone.return_value = [0]
        
        # Create sample Bible data
        bible_data = {
            'verses': [
                {
                    'book_name': 'Genesis',
                    'chapter_num': 1,
                    'verse_num': 1,
                    'verse_text': 'In the beginning, God created the heavens and the earth.',
                    'translation_source': 'ESV'
                },
                {
                    'book_name': 'John',
                    'chapter_num': 3,
                    'verse_num': 16,
                    'verse_text': 'For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.',
                    'translation_source': 'ESV'
                }
            ]
        }
        
        # Call the function
        load_esv_bible_data(mock_conn, bible_data)
        
        # Assert the connection was used correctly
        mock_conn.cursor.assert_called_once()
        mock_conn.commit.assert_called_once()
        
        # Assert the cursor was used to execute SQL statements for each verse
        self.assertEqual(mock_cursor.execute.call_count, 4)  # 2 SELECT + 2 INSERT statements
        
        # Assert that a success message was logged
        mock_logger.info.assert_called_with(f"Successfully loaded {len(bible_data['verses'])} ESV verses into the database")

    @patch('psycopg2.connect')
    @patch('src.etl.etl_english_bible.logger')
    def test_load_esv_bible_data_with_existing_verses(self, mock_logger, mock_connect):
        """Test loading ESV Bible data with existing verses that need to be updated."""
        # Create mock database objects
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock the fetchone method to return a count of 1 (existing verse)
        mock_cursor.fetchone.return_value = [1]
        
        # Create sample Bible data with one verse
        bible_data = {
            'verses': [
                {
                    'book_name': 'John',
                    'chapter_num': 3,
                    'verse_num': 16,
                    'verse_text': 'For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.',
                    'translation_source': 'ESV'
                }
            ]
        }
        
        # Call the function
        load_esv_bible_data(mock_conn, bible_data)
        
        # Assert the connection was used correctly
        mock_conn.cursor.assert_called_once()
        mock_conn.commit.assert_called_once()
        
        # Assert the cursor was used to execute SQL statements
        self.assertEqual(mock_cursor.execute.call_count, 2)  # 1 SELECT + 1 UPDATE statement
        
        # Assert that a success message was logged
        mock_logger.info.assert_called_with(f"Successfully loaded {len(bible_data['verses'])} ESV verses into the database")

    @patch('psycopg2.connect')
    @patch('src.etl.etl_english_bible.logger')
    def test_load_esv_bible_data_with_database_error(self, mock_logger, mock_connect):
        """Test handling of database errors during ESV Bible data loading."""
        # Create mock database objects
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Make the cursor raise an exception when execute is called
        mock_cursor.execute.side_effect = psycopg2.Error("Database error")
        
        # Create sample Bible data
        bible_data = {
            'verses': [
                {
                    'book_name': 'Genesis',
                    'chapter_num': 1,
                    'verse_num': 1,
                    'verse_text': 'In the beginning, God created the heavens and the earth.',
                    'translation_source': 'ESV'
                }
            ]
        }
        
        # Call the function and expect an exception
        with self.assertRaises(Exception):
            load_esv_bible_data(mock_conn, bible_data)
        
        # Assert that a rollback was performed
        mock_conn.rollback.assert_called_once()
        
        # Assert that an error was logged
        mock_logger.error.assert_called()

if __name__ == '__main__':
    unittest.main() 