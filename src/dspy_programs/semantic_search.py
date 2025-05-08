#!/usr/bin/env python3
"""
Enhanced Semantic Search for Bible Verses with DSPy and pgvector

This module provides advanced semantic search capabilities by combining:
1. pgvector database search for initial verse retrieval
2. DSPy-powered query expansion and reranking for better results

Key features:
- Query expansion to generate related theological concepts
- Contextual reranking to improve relevance
- Multi-hop reasoning for complex theological queries
- Integration with existing vector embeddings
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import requests
import psycopg
from psycopg.rows import dict_row
import numpy as np
from dotenv import load_dotenv
import dspy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/semantic_search.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# LM Studio API settings
LM_STUDIO_API_URL = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
EMBEDDING_MODEL = os.getenv("LM_STUDIO_EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5@q8_0")

# Define signatures for DSPy components
class BibleQueryExpansion(dspy.Signature):
    """Expand a Bible query with related theological concepts and terms."""
    query = dspy.InputField(desc="Original query about Bible content")
    expanded_queries = dspy.OutputField(desc="List of expanded queries including theological concepts", 
                                       format=List[str])

class BibleVerseReranker(dspy.Signature):
    """Rerank Bible verses based on relevance to the query."""
    query = dspy.InputField(desc="The user's query")
    verses = dspy.InputField(desc="List of Bible verses with references")
    reranked_verses = dspy.OutputField(desc="Reranked list of Bible verses with relevance scores",
                                     format=List[Dict[str, Any]])

class TopicHopping(dspy.Signature):
    """Identify related Bible topics to search for complex theological queries."""
    query = dspy.InputField(desc="Theological or biblical query")
    related_topics = dspy.OutputField(desc="List of related biblical topics to search",
                                     format=List[str])

# Database connection functions
def get_db_connection():
    """Get a database connection with the appropriate configuration."""
    try:
        conn = psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            dbname=os.getenv("POSTGRES_DB", "bible_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            row_factory=dict_row
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def get_embedding(text):
    """
    Get embedding vector for text using LM Studio API.
    
    Args:
        text: Text to encode
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        response = requests.post(
            f"{LM_STUDIO_API_URL}/embeddings",
            headers={"Content-Type": "application/json"},
            json={
                "model": EMBEDDING_MODEL,
                "input": text
            },
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"Error from LM Studio API: {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        if "data" in data and len(data["data"]) > 0 and "embedding" in data["data"][0]:
            # Ensure all values in the embedding are floats
            embedding = [float(val) for val in data["data"][0]["embedding"]]
            return embedding
        else:
            logger.error(f"Unexpected response format: {data}")
            return None
    except Exception as e:
        logger.error(f"Error getting embedding from LM Studio: {e}")
        return None

# Main semantic search module 
class EnhancedSemanticSearch:
    """Enhanced semantic search for Bible verses using DSPy and pgvector."""
    
    def __init__(self, use_dspy=True):
        """
        Initialize the semantic search module.
        
        Args:
            use_dspy: Whether to use DSPy enhancements
        """
        self.use_dspy = use_dspy
        
        # Initialize DSPy if needed
        if self.use_dspy:
            self._init_dspy()
    
    def _init_dspy(self):
        """Initialize DSPy components."""
        try:
            # Configure DSPy
            lm_studio_api = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
            lm_studio_model = os.getenv("LM_STUDIO_CHAT_MODEL", "llama3")
            
            # Set environment variables for openai compatibility
            os.environ["OPENAI_API_KEY"] = "dummy-key"
            os.environ["OPENAI_API_BASE"] = lm_studio_api
            
            # Use the proper provider configuration
            lm = dspy.LM(
                provider="openai",
                model=lm_studio_model,
                api_base=lm_studio_api,
                api_key="dummy-key"
            )
            dspy.settings.configure(lm=lm)
            
            # Initialize DSPy modules
            self.query_expander = dspy.Predict(BibleQueryExpansion)
            self.reranker = dspy.Predict(BibleVerseReranker)
            self.topic_hopper = dspy.Predict(TopicHopping)
            
            # Try to load trained models if available
            try:
                from .load_semantic_search_models import load_models, configure_semantic_search
                
                # Load and configure trained models
                models = load_models()
                if models:
                    # Replace the default predictors with trained ones
                    self = configure_semantic_search(self, models)
                    logger.info("Using trained semantic search models")
            except (ImportError, Exception) as e:
                logger.warning(f"Could not load trained models: {e}")
                logger.info("Using default semantic search components")
            
            logger.info("DSPy components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing DSPy: {e}")
            self.use_dspy = False
    
    def expand_query(self, query):
        """
        Expand a query with related theological concepts using DSPy.
        
        Args:
            query: Original search query
            
        Returns:
            List of expanded queries
        """
        if not self.use_dspy:
            return [query]
        
        try:
            result = self.query_expander(query=query)
            expanded_queries = result.expanded_queries
            
            # Validate each expanded query - ensure it's not just a single character
            valid_queries = [q for q in expanded_queries 
                            if q and len(q.strip()) > 3 and q.strip() != query]
            
            # Add the original query to the list
            valid_queries = [query] + valid_queries
            
            # Deduplicate
            unique_queries = []
            seen = set()
            for q in valid_queries:
                if q.lower().strip() not in seen:
                    seen.add(q.lower().strip())
                    unique_queries.append(q)
            
            # Limit to at most 5 expanded queries to prevent performance issues
            if len(unique_queries) > 5:
                unique_queries = unique_queries[:5]
                
            logger.info(f"Expanded query '{query}' to {len(unique_queries)} queries: {unique_queries}")
            return unique_queries
        except Exception as e:
            logger.error(f"Error expanding query: {e}")
            return [query]
    
    def rerank_results(self, query, verses):
        """
        Rerank search results using DSPy.
        
        Args:
            query: Original search query
            verses: List of verse dictionaries
            
        Returns:
            Reranked list of verses
        """
        if not self.use_dspy or not verses:
            return verses
        
        # Limit to top 15 verses for reranking to improve performance
        orig_verses = verses
        verses_to_rerank = sorted(verses, key=lambda x: x.get('similarity', 0), reverse=True)[:15]
        
        logger.info(f"Reranking top {len(verses_to_rerank)} of {len(verses)} verses")
        
        try:
            # Format verses for the reranker
            formatted_verses = []
            for v in verses_to_rerank:
                ref = f"{v['book_name']} {v['chapter_num']}:{v['verse_num']}"
                formatted_verses.append(f"{ref}: {v['verse_text']}")
            
            # Get reranked results
            result = self.reranker(query=query, verses=formatted_verses)
            
            # Check if reranking was successful
            if not hasattr(result, 'reranked_verses') or not result.reranked_verses:
                logger.warning("Reranker returned no results, using original verses")
                return orig_verses
            
            # Process the reranked results
            reranked_results = []
            verse_map = {f"{v['book_name']} {v['chapter_num']}:{v['verse_num']}": v 
                        for v in verses_to_rerank}
            
            for rank_result in result.reranked_verses:
                # Extract references and scores
                if isinstance(rank_result, dict) and 'reference' in rank_result and 'score' in rank_result:
                    ref = rank_result['reference']
                    score = float(rank_result['score'])
                    
                    # Find the verse in our original results
                    if ref in verse_map:
                        verse = verse_map[ref]
                        # Create a new verse object with updated similarity score
                        new_verse = verse.copy()
                        new_verse['similarity'] = score
                        reranked_results.append(new_verse)
                    else:
                        # Parse reference if not exact match
                        for orig_ref, verse in verse_map.items():
                            if ref.lower().startswith(orig_ref.lower()):
                                new_verse = verse.copy()
                                new_verse['similarity'] = score
                                reranked_results.append(new_verse)
                                break
            
            # Add any missing verses from the original top results
            if reranked_results:
                reranked_refs = {f"{v['book_name']} {v['chapter_num']}:{v['verse_num']}" 
                                for v in reranked_results}
                
                for verse in verses_to_rerank:
                    ref = f"{verse['book_name']} {verse['chapter_num']}:{verse['verse_num']}"
                    if ref not in reranked_refs:
                        reranked_results.append(verse)
                
                logger.info(f"Reranked {len(reranked_results)} verses successfully")
                
                # Sort by new similarity scores
                reranked_results = sorted(reranked_results, key=lambda x: x.get('similarity', 0), 
                                         reverse=True)
                
                # Combine with any remaining verses from the original results
                reranked_ids = {v['verse_id'] for v in reranked_results}
                remaining = [v for v in orig_verses if v['verse_id'] not in reranked_ids]
                final_results = reranked_results + remaining
                return final_results
            else:
                logger.warning("Reranking produced no valid results, using original order")
                return orig_verses
        except Exception as e:
            logger.error(f"Error reranking results: {e}")
            return orig_verses
    
    def get_related_topics(self, query):
        """
        Get related Bible topics for complex theological queries.
        
        Args:
            query: Original search query
            
        Returns:
            List of related topics
        """
        if not self.use_dspy:
            return [query]
        
        try:
            result = self.topic_hopper(query=query)
            related_topics = result.related_topics
            
            # Add the original query and deduplicate
            all_topics = [query] + related_topics
            unique_topics = []
            seen = set()
            
            for topic in all_topics:
                if topic.lower().strip() not in seen:
                    seen.add(topic.lower().strip())
                    unique_topics.append(topic)
            
            return unique_topics
        except Exception as e:
            logger.error(f"Error finding related topics: {e}")
            return [query]
    
    def search_verses(self, query, translation="KJV", limit=10, use_expansion=True):
        """
        Search for Bible verses semantically related to the query.
        
        Args:
            query: Search query
            translation: Bible translation to search
            limit: Maximum number of results to return
            use_expansion: Whether to use query expansion
            
        Returns:
            List of verse dictionaries
        """
        # Validate inputs
        if not query or not query.strip():
            return []
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        try:
            # Get database connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Apply query expansion if enabled
            queries = self.expand_query(query) if self.use_dspy and use_expansion else [query]
            
            # Get embeddings for all queries
            embeddings = []
            for q in queries:
                embedding = get_embedding(q)
                if embedding:
                    embeddings.append((q, embedding))
            
            # If no embeddings were generated, return empty results
            if not embeddings:
                logger.error("Could not generate embeddings for the query")
                return []
            
            # Search for each embedding and collect results
            all_results = []
            seen_verse_ids = set()
            
            for q, embedding in embeddings:
                # Convert embedding to PostgreSQL vector format
                embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
                
                # Execute semantic search query
                search_query = """
                SELECT v.verse_id, b.book_name, v.chapter_num, v.verse_num, 
                       v.verse_text, ve.translation_source,
                       1 - (ve.embedding <=> %s::vector) as similarity
                FROM bible.verses v
                JOIN bible.books b ON v.book_id = b.book_id
                JOIN bible.verse_embeddings ve ON v.verse_id = ve.verse_id
                WHERE ve.translation_source = %s
                ORDER BY ve.embedding <=> %s::vector
                LIMIT %s;
                """
                
                cursor.execute(search_query, (embedding_str, translation, embedding_str, limit * 2))
                results = cursor.fetchall()
                
                # Add results to the collection, avoiding duplicates
                for result in results:
                    if result['verse_id'] not in seen_verse_ids:
                        seen_verse_ids.add(result['verse_id'])
                        all_results.append(dict(result))
            
            # Close database connection
            conn.close()
            
            # Sort by similarity and limit results
            if all_results:
                all_results = sorted(all_results, key=lambda x: x['similarity'], reverse=True)
                all_results = all_results[:limit]
                
                # Apply reranking if DSPy is enabled
                if self.use_dspy:
                    all_results = self.rerank_results(query, all_results)
                    
                    # Ensure we don't exceed the limit after reranking
                    if len(all_results) > limit:
                        all_results = all_results[:limit]
            
            logger.info(f"Found {len(all_results)} verses for query: {query}")
            return all_results
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def multi_hop_search(self, query, translation="KJV", limit=10):
        """
        Perform multi-hop search for complex theological queries.
        
        Args:
            query: Complex theological query
            translation: Bible translation to search
            limit: Maximum number of results to return
            
        Returns:
            List of verse dictionaries
        """
        if not self.use_dspy:
            # Fall back to regular search if DSPy is not enabled
            return self.search_verses(query, translation, limit)
            
        # Get related topics
        topics = self.get_related_topics(query)
        
        # Search for each topic
        all_results = []
        seen_verse_ids = set()
        
        for topic in topics:
            results = self.search_verses(topic, translation, limit=limit//2, use_expansion=False)
            
            # Add to collection, avoiding duplicates
            for result in results:
                if result['verse_id'] not in seen_verse_ids:
                    seen_verse_ids.add(result['verse_id'])
                    all_results.append(result)
        
        # Sort by similarity and limit results
        if all_results:
            all_results = sorted(all_results, key=lambda x: x['similarity'], reverse=True)
            all_results = all_results[:limit]
            
            # Final reranking with original query
            all_results = self.rerank_results(query, all_results)
        
        logger.info(f"Multi-hop search found {len(all_results)} verses for query: {query}")
        return all_results

# Convenience functions for direct API usage
def search_verses(query, translation="KJV", limit=10, use_dspy=True):
    """
    Search for Bible verses semantically related to the query.
    
    Args:
        query: Search query
        translation: Bible translation to search
        limit: Maximum number of results to return
        use_dspy: Whether to use DSPy enhancements
        
    Returns:
        List of verse dictionaries
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    search = EnhancedSemanticSearch(use_dspy=use_dspy)
    return search.search_verses(query, translation, limit)

def complex_search(query, translation="KJV", limit=10, use_dspy=True):
    """
    Perform multi-hop search for complex theological queries.
    
    Args:
        query: Complex theological query
        translation: Bible translation to search
        limit: Maximum number of results to return
        use_dspy: Whether to use DSPy enhancements
        
    Returns:
        List of verse dictionaries
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    search = EnhancedSemanticSearch(use_dspy=use_dspy)
    
    if use_dspy:
        return search.multi_hop_search(query, translation, limit)
    else:
        return search.search_verses(query, translation, limit)

# For direct execution (testing)
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Bible Semantic Search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--translation", default="KJV", help="Bible translation to search")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results")
    parser.add_argument("--no-dspy", action="store_true", help="Disable DSPy enhancements")
    parser.add_argument("--complex", action="store_true", help="Use complex multi-hop search")
    args = parser.parse_args()
    
    # Perform the search
    if args.complex:
        results = complex_search(args.query, args.translation, args.limit, not args.no_dspy)
    else:
        results = search_verses(args.query, args.translation, args.limit, not args.no_dspy)
    
    # Display results
    print(f"\nResults for: {args.query}\n")
    for i, verse in enumerate(results, 1):
        ref = f"{verse['book_name']} {verse['chapter_num']}:{verse['verse_num']}"
        score = verse.get('similarity', 0)
        print(f"{i}. {ref} ({score:.4f})")
        print(f"   {verse['verse_text']}")
        print() 