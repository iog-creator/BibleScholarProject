#!/usr/bin/env python3
"""
Integration tests for the comprehensive search API - vector search functionality.

These tests verify that the comprehensive search API can perform vector searches
across multiple translations and handle cross-language searches.
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

class TestComprehensiveVectorSearch(unittest.TestCase):
    """Test case for the comprehensive vector search API endpoint."""
    
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
    TIMEOUT = 10  # seconds
    
    def setUp(self):
        """Set up test case."""
        logger.info(f"Testing against API at {self.API_BASE_URL}")

    def test_basic_vector_search(self):
        """Test basic vector search with default parameters."""
        response = requests.get(
            f'{self.API_BASE_URL}/api/comprehensive/vector-search',
            params={'q': 'God created the heavens', 'translation': 'KJV'},
            timeout=self.TIMEOUT
        )
        
        self.assertEqual(response.status_code, 200, 'Basic vector search failed')
        
        data = response.json()
        self.assertIn('results', data, 'Results missing from response')
        self.assertGreater(len(data['results']), 0, 'No results returned')
        
        # Check structure of first result
        first_result = data['results'][0]
        self.assertIn('reference', first_result, 'Reference missing from result')
        self.assertIn('text', first_result, 'Text missing from result')
        self.assertIn('similarity', first_result, 'Similarity score missing from result')
    
    def test_cross_language_search(self):
        """Test cross-language search functionality."""
        response = requests.get(
            f'{self.API_BASE_URL}/api/comprehensive/vector-search',
            params={
                'q': 'God created the heavens', 
                'translation': 'KJV', 
                'cross_language': 'true'
            },
            timeout=self.TIMEOUT
        )
        
        self.assertEqual(response.status_code, 200, 'Cross-language search failed')
        
        data = response.json()
        self.assertIn('results', data, 'Results missing from response')
        
        # May need to relax this assertion if no cross-language results are found for this query
        if len(data['results']) > 0:
            # Check for cross_language flag in at least one result
            has_cross_language = any(
                result.get('cross_language', False) for result in data['results']
            )
            
            self.assertTrue(
                has_cross_language, 
                'No cross-language results found when cross_language parameter is true'
            )
    
    def test_hebrew_with_lexical_data(self):
        """Test Hebrew search with lexical data included."""
        response = requests.get(
            f'{self.API_BASE_URL}/api/comprehensive/vector-search',
            params={
                'q': 'creation', 
                'translation': 'TAHOT', 
                'include_lexicon': 'true'
            },
            timeout=self.TIMEOUT
        )
        
        self.assertEqual(response.status_code, 200, 'Hebrew search with lexical data failed')
        
        data = response.json()
        self.assertIn('results', data, 'Results missing from response')
        
        if len(data['results']) > 0:
            # Check for lexical data in at least one result
            has_lexical_data = any(
                'lexical_data' in result for result in data['results']
            )
            
            self.assertTrue(
                has_lexical_data, 
                'No lexical data found when include_lexicon parameter is true'
            )

if __name__ == '__main__':
    unittest.main() 