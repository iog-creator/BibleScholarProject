#!/usr/bin/env python3
"""
Test script for pgvector search functionality.

This script:
1. Connects to the database
2. Generates an embedding for a test query using LM Studio
3. Searches for similar verses using pgvector
4. Prints the results

Usage:
    python -m src.utils.test_vector_search
"""

import os
import requests
import logging
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# LM Studio API settings
LM_STUDIO_API_URL = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234")
EMBEDDING_MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0:2"

def get_db_connection():
    """Get a database connection with the appropriate configuration."""
    conn = psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "bible_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        row_factory=dict_row
    )
    return conn

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
            f"{LM_STUDIO_API_URL}/v1/embeddings",
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

def search_similar_verses(query, translation="KJV", limit=5):
    """
    Search for verses similar to the query using vector similarity.
    
    Args:
        query: Text query
        translation: Bible translation to search
        limit: Number of results to return
        
    Returns:
        List of similar verses
    """
    # Get query embedding
    query_embedding = get_embedding(query)
    if not query_embedding:
        logger.error("Failed to generate embedding for query")
        return None
    
    logger.info(f"Generated embedding for query: {query} (length: {len(query_embedding)})")
    
    # Search for similar verses
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Format the embedding array in PostgreSQL syntax
            # Convert the Python list directly to a string representation in Postgres array format
            embedding_array = "["
            for i, value in enumerate(query_embedding):
                if i > 0:
                    embedding_array += ","
                embedding_array += str(value)
            embedding_array += "]"
            
            # Run the query with properly formatted vector
            cur.execute(
                """
                SELECT 
                    v.book_name, 
                    v.chapter_num, 
                    v.verse_num, 
                    v.verse_text,
                    v.translation_source,
                    1 - (e.embedding <=> %s::vector) AS similarity
                FROM 
                    bible.verse_embeddings e
                    JOIN bible.verses v ON e.verse_id = v.id
                WHERE 
                    v.translation_source = %s
                ORDER BY 
                    e.embedding <=> %s::vector
                LIMIT %s
                """,
                (embedding_array, translation, embedding_array, limit)
            )
            results = cur.fetchall()
            
            # Format results for display
            formatted_results = []
            for r in results:
                formatted_results.append({
                    'reference': f"{r['book_name']} {r['chapter_num']}:{r['verse_num']}",
                    'text': r['verse_text'],
                    'translation': r['translation_source'],
                    'similarity': round(float(r['similarity']) * 100, 2)
                })
                
            return formatted_results
    except Exception as e:
        logger.error(f"Error searching similar verses: {e}")
        return None
    finally:
        conn.close()

def main():
    """Main entry point."""
    try:
        # Test queries
        queries = [
            "God created the heavens and the earth",
            "Love your neighbor as yourself",
            "The wages of sin is death"
        ]
        
        # Search for similar verses
        for query in queries:
            logger.info(f"\nSearching for verses similar to: '{query}'")
            results = search_similar_verses(query)
            
            if results:
                logger.info(f"Found {len(results)} similar verses:")
                for i, result in enumerate(results):
                    logger.info(f"{i+1}. {result['reference']} ({result['similarity']}% similarity)")
                    logger.info(f"   {result['text']}")
            else:
                logger.info("No results found")
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main() 