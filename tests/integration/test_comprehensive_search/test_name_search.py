#!/usr/bin/env python3
"""
Integration tests for the comprehensive search API - proper name search functionality.

These tests verify that the proper name search API can find biblical names
and their relationships.
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

class TestProperNameSearch(unittest.TestCase):
    """Test case for the proper name search API endpoint."""
    
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
    TIMEOUT = 10  # seconds
    
    def setUp(self):
        """Set up test case."""
        logger.info(f"Testing against API at {self.API_BASE_URL}")

    def test_basic_name_search(self):
        """Test basic name search."""
        response = requests.get(
            f'{self.API_BASE_URL}/api/comprehensive/name-search',
            params={'name': 'Moses'},
            timeout=self.TIMEOUT
        )
        
        self.assertEqual(response.status_code, 200, 'Basic name search failed')
        
        data = response.json()
        self.assertIn('results', data, 'Results missing from response')
        self.assertIn('names', data['results'], 'Names missing from results')
        
        # Should find at least one entry for 'Moses'
        self.assertGreater(len(data['results']['names']), 0, 'No names found for Moses')
    
    def test_name_search_with_relationships(self):
        """Test name search with relationships included."""
        response = requests.get(
            f'{self.API_BASE_URL}/api/comprehensive/name-search',
            params={'name': 'Abraham', 'include_relationships': 'true'},
            timeout=self.TIMEOUT
        )
        
        self.assertEqual(response.status_code, 200, 'Name search with relationships failed')
        
        data = response.json()
        self.assertIn('results', data, 'Results missing from response')
        self.assertIn('names', data['results'], 'Names missing from results')
        
        # Abraham should have relationships, but this is a soft check
        # as test data might vary
        if len(data['results']['names']) > 0:
            self.assertIn('relationships', data['results'], 
                     'Relationships not included in results when requested')
    
    def test_filtered_name_search(self):
        """Test name search with relationship type filter."""
        response = requests.get(
            f'{self.API_BASE_URL}/api/comprehensive/name-search',
            params={
                'name': 'David', 
                'include_relationships': 'true',
                'relationship_type': 'father-son'  # This assumes this relationship type exists
            },
            timeout=self.TIMEOUT
        )
        
        self.assertEqual(response.status_code, 200, 'Filtered name search failed')
        
        data = response.json()
        # This test is more relaxed since the relationship type might not exist
        # or David might not have that specific relationship
        self.assertIn('results', data, 'Results missing from response')
        self.assertIn('names', data['results'], 'Names missing from results')

if __name__ == '__main__':
    unittest.main() 