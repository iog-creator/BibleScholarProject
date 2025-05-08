#!/usr/bin/env python3
"""
Unit Tests for DSPy-Enhanced Semantic Search

These tests verify:
1. Basic functionality of DSPy semantic search
2. Query expansion capabilities
3. Result reranking
4. Multi-hop reasoning
5. Integration with pgvector
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import the semantic search functionality
from src.dspy_programs.semantic_search import (
    search_verses, 
    complex_search, 
    EnhancedSemanticSearch,
    BibleQueryExpansion,
    BibleVerseReranker,
    TopicHopping
)

class MockEmbedding:
    """Mock embedding response for testing."""
    
    @staticmethod
    def get_mock_embedding(text=None):
        """Return a mock embedding vector."""
        # Return a fixed-size vector of pseudo-random values
        import hashlib
        
        # Generate deterministic but different embeddings for different texts
        if text:
            seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % 10000
        else:
            seed = 42
            
        import random
        random.seed(seed)
        return [random.uniform(-1, 1) for _ in range(768)]

class MockDSPyPredictor:
    """Mock DSPy predictors for testing."""
    
    @staticmethod
    def mock_query_expansion(query):
        """Return mock expanded queries."""
        return MagicMock(
            expanded_queries=[
                query,
                f"{query} theological context",
                f"biblical passages about {query}"
            ]
        )
    
    @staticmethod
    def mock_reranker(query, verses):
        """Return mock reranked verses."""
        # Create mock reranked verses with scoring
        reranked = []
        for i, verse in enumerate(verses):
            # Extract reference from verse string
            parts = verse.split(":")
            if len(parts) >= 2:
                ref = parts[0]
                reranked.append({
                    "reference": ref,
                    "score": 0.9 - (i * 0.1)  # Mock scores
                })
        
        return MagicMock(reranked_verses=reranked)
    
    @staticmethod
    def mock_topic_hopper(query):
        """Return mock related topics."""
        if "creation" in query.lower():
            topics = ["Genesis creation narrative", "God as creator", "Nature in the Bible"]
        elif "love" in query.lower():
            topics = ["God's love", "Love in the New Testament", "Love your neighbor"]
        else:
            topics = ["Biblical theology", "Old Testament themes", "New Testament teachings"]
            
        return MagicMock(related_topics=topics)

class MockDbConnection:
    """Mock database connection for testing."""
    
    def __init__(self):
        self.cursor = MagicMock()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def close(self):
        pass

class MockCursor:
    """Mock database cursor for testing."""
    
    def __init__(self):
        self.results = []
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def execute(self, query, params=None):
        """Mock query execution."""
        # Store the query for later verification if needed
        self.last_query = query
        self.last_params = params
        
    def fetchall(self):
        """Return mock verse results."""
        return [
            {
                "book_name": "Genesis",
                "chapter_num": 1,
                "verse_num": 1,
                "verse_text": "In the beginning God created the heaven and the earth.",
                "translation_source": "KJV",
                "similarity": 0.95
            },
            {
                "book_name": "John",
                "chapter_num": 1,
                "verse_num": 1,
                "verse_text": "In the beginning was the Word, and the Word was with God, and the Word was God.",
                "translation_source": "KJV",
                "similarity": 0.85
            },
            {
                "book_name": "Psalms",
                "chapter_num": 19,
                "verse_num": 1,
                "verse_text": "The heavens declare the glory of God; and the firmament sheweth his handywork.",
                "translation_source": "KJV",
                "similarity": 0.75
            }
        ]

class TestDSPySemanticSearch(unittest.TestCase):
    """Test cases for DSPy-enhanced semantic search."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock DSPy components
        self.query_expander_patcher = patch('dspy.Predict')
        self.mock_predict = self.query_expander_patcher.start()
        self.mock_predict.side_effect = self._mock_predict_side_effect
        
        # Mock get_embedding function
        self.embedding_patcher = patch('src.dspy_programs.semantic_search.get_embedding')
        self.mock_get_embedding = self.embedding_patcher.start()
        self.mock_get_embedding.side_effect = MockEmbedding.get_mock_embedding
        
        # Mock database connection
        self.db_patcher = patch('src.dspy_programs.semantic_search.get_db_connection')
        self.mock_db = self.db_patcher.start()
        self.mock_cursor = MockCursor()
        self.mock_conn = MockDbConnection()
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.mock_db.return_value = self.mock_conn
    
    def tearDown(self):
        """Clean up after tests."""
        self.query_expander_patcher.stop()
        self.embedding_patcher.stop()
        self.db_patcher.stop()
    
    def _mock_predict_side_effect(self, signature):
        """Return appropriate mock based on signature."""
        if signature == BibleQueryExpansion:
            return lambda **kwargs: MockDSPyPredictor.mock_query_expansion(kwargs.get('query', ''))
        elif signature == BibleVerseReranker:
            return lambda **kwargs: MockDSPyPredictor.mock_reranker(
                kwargs.get('query', ''), 
                kwargs.get('verses', [])
            )
        elif signature == TopicHopping:
            return lambda **kwargs: MockDSPyPredictor.mock_topic_hopper(kwargs.get('query', ''))
        return MagicMock()
    
    def test_init_semantic_search(self):
        """Test initialization of semantic search class."""
        search = EnhancedSemanticSearch(use_dspy=True)
        self.assertTrue(hasattr(search, 'query_expander'))
        self.assertTrue(hasattr(search, 'reranker'))
        self.assertTrue(hasattr(search, 'topic_hopper'))
    
    def test_expand_query(self):
        """Test query expansion functionality."""
        search = EnhancedSemanticSearch(use_dspy=True)
        expanded = search.expand_query("creation")
        
        self.assertEqual(len(expanded), 3)
        self.assertEqual(expanded[0], "creation")
        self.assertIn("theological", expanded[1])
        self.assertIn("biblical", expanded[2])
    
    def test_search_verses_basic(self):
        """Test basic verse search functionality."""
        results = search_verses("creation", limit=3, use_dspy=False)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['reference'], "Genesis 1:1")
        self.assertEqual(results[0]['translation'], "KJV")
        self.assertTrue('similarity' in results[0])
    
    def test_search_verses_with_dspy(self):
        """Test verse search with DSPy enhancements."""
        results = search_verses("creation", limit=3, use_dspy=True)
        
        self.assertEqual(len(results), 3)
        # Results should be formatted with reference, text, translation, similarity
        for result in results:
            self.assertTrue('reference' in result)
            self.assertTrue('text' in result)
            self.assertTrue('translation' in result)
            self.assertTrue('similarity' in result)
    
    def test_rerank_results(self):
        """Test result reranking functionality."""
        search = EnhancedSemanticSearch(use_dspy=True)
        test_verses = [
            {
                "book_name": "Genesis",
                "chapter_num": 1,
                "verse_num": 1,
                "verse_text": "In the beginning God created the heaven and the earth.",
                "translation_source": "KJV",
                "similarity": 0.75  # Lower similarity to test reranking
            },
            {
                "book_name": "John",
                "chapter_num": 1,
                "verse_num": 1,
                "verse_text": "In the beginning was the Word, and the Word was with God, and the Word was God.",
                "translation_source": "KJV",
                "similarity": 0.85
            }
        ]
        
        reranked = search.rerank_results("creation", test_verses)
        
        # Verify that relevance scores were added
        self.assertTrue('relevance' in reranked[0])
    
    def test_get_related_topics(self):
        """Test related topics extraction."""
        search = EnhancedSemanticSearch(use_dspy=True)
        topics = search.get_related_topics("creation")
        
        self.assertEqual(len(topics), 3)
        self.assertIn("Genesis creation narrative", topics)
    
    def test_complex_search(self):
        """Test complex theological search with multi-hop reasoning."""
        results = complex_search("God's creation of the world", limit=3)
        
        # Check the structure of the response
        self.assertTrue('primary_results' in results)
        self.assertTrue('related_topics' in results)
        self.assertTrue('topic_results' in results)
        
        # Verify primary results
        self.assertEqual(len(results['primary_results']), 3)
        
        # Verify related topics
        self.assertGreater(len(results['related_topics']), 0)
    
    def test_search_without_dspy(self):
        """Test fallback to standard search when DSPy is disabled."""
        search = EnhancedSemanticSearch(use_dspy=False)
        
        # Query expansion should just return the original query
        expanded = search.expand_query("creation")
        self.assertEqual(len(expanded), 1)
        self.assertEqual(expanded[0], "creation")
        
        # Related topics should be empty
        topics = search.get_related_topics("creation")
        self.assertEqual(len(topics), 0)
        
        # Complex search should only return primary results
        result = search.multi_hop_search("creation")
        self.assertTrue('primary_results' in result)
        self.assertFalse('related_topics' in result)
        self.assertFalse('topic_results' in result)

if __name__ == '__main__':
    unittest.main() 