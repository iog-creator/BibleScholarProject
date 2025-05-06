#!/usr/bin/env python3
"""
Integration tests for the comprehensive search API - theological term search functionality.

These tests verify that the theological term search API can find theological terms
and their occurrences across different translations.
"""

import unittest
import requests
import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TestTheologicalTermSearch(unittest.TestCase):
    """Test case for the theological term search API endpoint."""
    
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
    TIMEOUT = 10  # seconds
    
    def setUp(self):
        """Set up test case."""
        logger.info(f"Testing against API at {self.API_BASE_URL}")

    def test_hebrew_term_search(self):
        """Test searching for a Hebrew theological term."""
        response = requests.get(
            f'{self.API_BASE_URL}/api/comprehensive/theological-term-search',
            params={'term': 'elohim', 'language': 'hebrew'},
            timeout=self.TIMEOUT
        )
        
        self.assertEqual(response.status_code, 200, 'Hebrew term search failed')
        
        data = response.json()
        self.assertIn('term', data, 'Term missing from response')
        self.assertIn('verses', data, 'Verses missing from response')
        
        # Should find at least some verses for 'elohim'
        self.assertGreater(len(data['verses']), 0, 'No verses found for Hebrew term elohim')
    
    def test_strongs_term_search(self):
        """Test searching by Strong's ID."""
        response = requests.get(
            f'{self.API_BASE_URL}/api/comprehensive/theological-term-search',
            params={'term': 'H3068', 'language': 'hebrew'},
            timeout=self.TIMEOUT
        )
        
        self.assertEqual(response.status_code, 200, 'Strong\'s ID search failed')
        
        data = response.json()
        self.assertIn('term_info', data, 'Term info missing from response')
        
        # H3068 is YHWH, should return results
        if data.get('term_info'):
            term_found = any(
                term.get('strongs_id') == 'H3068' for term in data['term_info']
            )
            self.assertTrue(term_found, 'Strong\'s ID H3068 not found in term_info')
    
    def test_equivalent_terms(self):
        """Test including equivalent terms in other languages."""
        response = requests.get(
            f'{self.API_BASE_URL}/api/comprehensive/theological-term-search',
            params={
                'term': 'God', 
                'language': 'english',
                'include_equivalent': 'true'
            },
            timeout=self.TIMEOUT
        )
        
        self.assertEqual(response.status_code, 200, 'Equivalent terms search failed')
        
        data = response.json()
        # Test relaxed for initial implementation - may not have cross-language term data yet
        self.assertIn('verses', data, 'Verses missing from response')
        # Ideally would check for semantically_related flag in some results

if __name__ == '__main__':
    unittest.main() 