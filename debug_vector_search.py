#!/usr/bin/env python3
"""
Debug script for testing vector search with TAHOT translation.
This script directly uses the search_verses function without the Flask app.
"""

import os
import logging
import psycopg2
import psycopg2.extras
import requests
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
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "bible_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        cursor_factory=psycopg2.extras.DictCursor
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
        logger.info(f"Getting embedding from LM Studio for: '{text}'")
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
            logger.info(f"Successfully generated embedding with {len(embedding)} dimensions")
            return embedding
        else:
            logger.error(f"Unexpected response format: {data}")
            return None
    except Exception as e:
        logger.error(f"Error getting embedding from LM Studio: {e}")
        return None

def search_verses_direct(query, translation="TAHOT", limit=3):
    """
    Direct search for verses similar to the query using vector similarity.
    
    Args:
        query: Text query
        translation: Bible translation to search
        limit: Number of results to return
        
    Returns:
        List of similar verses
    """
    query_embedding = get_embedding(query)
    if not query_embedding:
        logger.error("Failed to generate embedding for query")
        return []
    
    # Format the embedding array in PostgreSQL syntax
    embedding_array = "["
    for i, value in enumerate(query_embedding):
        if i > 0:
            embedding_array += ","
        embedding_array += str(value)
    embedding_array += "]"
    
    # Output statistics for debugging
    logger.info(f"Searching for verses similar to: '{query}' in translation: '{translation}'")
    
    # Search for similar verses
    conn = get_db_connection()
    try:
        # Get count first to verify query works
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    SELECT COUNT(*) 
                    FROM bible.verse_embeddings e
                    JOIN bible.verses v ON e.verse_id = v.id
                    WHERE v.translation_source = %s
                    """,
                    (translation,)
                )
                count_result = cur.fetchone()
                verse_count = count_result["count"] if count_result else 0
                logger.info(f"Found {verse_count} verses in {translation} translation")
                
                if verse_count == 0:
                    logger.warning(f"No verses found for translation: {translation}")
                    return []
                
                # Just get one sample verse to test the embedding format
                cur.execute(
                    """
                    SELECT e.verse_id, v.book_name, v.chapter_num, v.verse_num, v.verse_text, e.embedding
                    FROM bible.verse_embeddings e
                    JOIN bible.verses v ON e.verse_id = v.id
                    WHERE v.translation_source = %s
                    LIMIT 1
                    """,
                    (translation,)
                )
                sample = cur.fetchone()
                if sample:
                    logger.info(f"Sample verse: {sample['book_name']} {sample['chapter_num']}:{sample['verse_num']}")
                    logger.info(f"Embedding type: {type(sample['embedding'])}")
                
                # Try self-similarity test
                cur.execute(
                    """
                    SELECT 1 - (e.embedding <=> e.embedding) as self_similarity
                    FROM bible.verse_embeddings e
                    JOIN bible.verses v ON e.verse_id = v.id
                    WHERE v.translation_source = %s
                    LIMIT 1
                    """,
                    (translation,)
                )
                sim_test = cur.fetchone()
                logger.info(f"Self-similarity test result: {sim_test['self_similarity']}")
                
                # Use a simple direct pgvector similarity search
                embedding_query = """
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
                """
                
                cur.execute(embedding_query, (embedding_array, translation, embedding_array, limit))
                results = cur.fetchall()
                
                logger.info(f"Found {len(results)} similar verses in {translation}")
                
                # Format results for display
                formatted_results = []
                for r in results:
                    result = {
                        'reference': f"{r['book_name']} {r['chapter_num']}:{r['verse_num']}",
                        'text': r['verse_text'],
                        'translation': r['translation_source'],
                        'similarity': round(float(r['similarity']) * 100, 2)
                    }
                    formatted_results.append(result)
                    logger.info(f"Match: {result['reference']} (Similarity: {result['similarity']}%)")
                    
                return formatted_results
            except Exception as e:
                logger.error(f"Error in vector search query: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return []
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Testing KJV search...")
    results_kjv = search_verses_direct("God created the heavens and the earth", "KJV", 3)
    
    logger.info("\nTesting TAHOT search...")
    results_tahot = search_verses_direct("God created the heavens and the earth", "TAHOT", 3)
    
    if not results_tahot:
        logger.info("Trying different query for TAHOT...")
        results_tahot = search_verses_direct("בְּ/רֵאשִׁ֖ית", "TAHOT", 3)
        
    logger.info("\nDone testing vector search") 