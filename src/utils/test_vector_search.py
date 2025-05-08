#!/usr/bin/env python3
"""
Test Vector Search Functionality

This script tests the vector search functionality by:
1. Checking if the pgvector extension is installed
2. Checking if the verse_embeddings table exists
3. Testing a simple vector search query
4. Testing the similarity search between verses
"""

import os
import sys
import logging
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/vector_search_test.log", mode="a"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# LM Studio API settings
LM_STUDIO_API_URL = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
EMBEDDING_MODEL = os.getenv("LM_STUDIO_EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5@q8_0")

# Database connection settings
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "bible_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")

def get_db_connection():
    """Get a connection to the database with dictionary cursor."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def test_extension_installed():
    """Test if the vector extension is installed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        result = cursor.fetchone()
        
        if result:
            logger.info("Vector extension is installed")
            return True
        else:
            logger.error("Vector extension is NOT installed")
            return False
    except Exception as e:
        logger.error(f"Error checking vector extension: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def test_table_exists():
    """Test if the verse_embeddings table exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'bible' AND table_name = 'verse_embeddings'
        )
        """)
        result = cursor.fetchone()
        
        if result and result['exists']:
            logger.info("verse_embeddings table exists")
            
            # Check the count of embeddings
            cursor.execute("SELECT COUNT(*) FROM bible.verse_embeddings")
            count = cursor.fetchone()['count']
            logger.info(f"Found {count} verse embeddings in the database")
            
            # Check the available translations
            cursor.execute("""
            SELECT translation_source, COUNT(*) as count 
            FROM bible.verse_embeddings 
            GROUP BY translation_source
            ORDER BY translation_source
            """)
            translations = cursor.fetchall()
            
            if translations:
                logger.info("Available translations:")
                for trans in translations:
                    logger.info(f"  {trans['translation_source']}: {trans['count']} verses")
            else:
                logger.warning("No translations found in the database")
            
            return count > 0
        else:
            logger.error("verse_embeddings table does NOT exist")
            return False
    except Exception as e:
        logger.error(f"Error checking verse_embeddings table: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

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

def test_vector_search():
    """Test basic vector search functionality."""
    logger.info("Testing vector search...")
    
    # Choose a translation to test
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First, let's understand the table structure
        cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'bible' AND table_name = 'verse_embeddings'
        ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        logger.info("verse_embeddings table structure:")
        for col in columns:
            logger.info(f"  {col['column_name']} ({col['data_type']})")
        
        # Get available translation with the most embeddings
        cursor.execute("""
        SELECT translation_source, COUNT(*) as count 
        FROM bible.verse_embeddings 
        GROUP BY translation_source 
        ORDER BY count DESC
        LIMIT 1
        """)
        
        result = cursor.fetchone()
        if not result:
            logger.error("No translations found with embeddings")
            return False
        
        translation = result['translation_source']
        logger.info(f"Using translation: {translation} for testing")
        
        # Test query
        test_query = "The beginning of creation"
        
        # Get embedding for the query
        embedding = get_embedding(test_query)
        if not embedding:
            logger.error("Failed to get embedding for test query")
            return False
        
        # Convert embedding to string format for PostgreSQL
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        # Perform search
        search_query = """
        SELECT e.verse_id, e.book_name, e.chapter_num, e.verse_num, 
               v.verse_text, e.translation_source,
               1 - (e.embedding <=> %s::vector) as similarity
        FROM bible.verse_embeddings e
        JOIN bible.verses v ON e.verse_id = v.id
        WHERE e.translation_source = %s
        ORDER BY e.embedding <=> %s::vector
        LIMIT 5
        """
        
        cursor.execute(search_query, (embedding_str, translation, embedding_str))
        results = cursor.fetchall()
        
        if results:
            logger.info(f"Vector search successful for query: '{test_query}'")
            logger.info("Top results:")
            
            for i, result in enumerate(results):
                logger.info(f"{i+1}. {result['book_name']} {result['chapter_num']}:{result['verse_num']} - "
                           f"Similarity: {float(result['similarity']):.4f}")
                logger.info(f"   Text: {result['verse_text']}")
            
            return True
        else:
            logger.error("No results returned from vector search")
            return False
    
    except Exception as e:
        logger.error(f"Error in vector search test: {e}")
        return False
    
    finally:
        cursor.close()
        conn.close()

def test_verse_similarity():
    """Test verse similarity functionality."""
    logger.info("Testing verse similarity...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Debug the issue by checking what translations are available
        cursor.execute("""
        SELECT translation_source, COUNT(*) as count 
        FROM bible.verse_embeddings 
        GROUP BY translation_source 
        ORDER BY count DESC
        LIMIT 1
        """)
        
        translation_result = cursor.fetchone()
        if not translation_result:
            logger.error("No translations found with embeddings")
            return False
        
        translation = translation_result['translation_source']
        logger.info(f"Using translation: {translation} for similarity test")
        
        # Get the first verse in the database that has embeddings
        cursor.execute("""
        SELECT e.verse_id, e.embedding, e.book_name, e.chapter_num, e.verse_num, v.verse_text
        FROM bible.verse_embeddings e
        JOIN bible.verses v ON e.verse_id = v.id
        WHERE e.translation_source = %s
        ORDER BY e.id
        LIMIT 1
        """, (translation,))
        
        verse_result = cursor.fetchone()
        if not verse_result:
            logger.error("No verses found with embeddings")
            return False
        
        logger.info(f"Testing similarity to: {verse_result['book_name']} {verse_result['chapter_num']}:{verse_result['verse_num']}")
        logger.info(f"Verse text: {verse_result['verse_text']}")
        
        # Search for similar verses using that verse's embedding
        search_query = """
        SELECT e.verse_id, e.book_name, e.chapter_num, e.verse_num, 
               v.verse_text, e.translation_source,
               1 - (e.embedding <=> %s) as similarity
        FROM bible.verse_embeddings e
        JOIN bible.verses v ON e.verse_id = v.id
        WHERE e.translation_source = %s
        AND e.verse_id != %s
        ORDER BY e.embedding <=> %s
        LIMIT 5
        """
        
        cursor.execute(search_query, (
            verse_result['embedding'], 
            translation,
            verse_result['verse_id'],
            verse_result['embedding']
        ))
        
        similar_verses = cursor.fetchall()
        
        if similar_verses:
            logger.info(f"Verse similarity search successful")
            logger.info("Most similar verses:")
            
            for i, result in enumerate(similar_verses):
                logger.info(f"{i+1}. {result['book_name']} {result['chapter_num']}:{result['verse_num']} - "
                           f"Similarity: {float(result['similarity']):.4f}")
                logger.info(f"   Text: {result['verse_text']}")
            
            return True
        else:
            logger.error("No similar verses found")
            return False
    
    except Exception as e:
        logger.error(f"Error in verse similarity test: {e}")
        logger.exception("Detailed traceback")
        return False
    
    finally:
        cursor.close()
        conn.close()

def main():
    """Run all tests."""
    logger.info("Starting vector search tests")
    
    # Track test results
    tests_passed = 0
    tests_failed = 0
    
    # Test if extension is installed
    if test_extension_installed():
        tests_passed += 1
    else:
        tests_failed += 1
        logger.error("Vector extension test failed, aborting further tests")
        return False
    
    # Test if table exists
    if test_table_exists():
        tests_passed += 1
    else:
        tests_failed += 1
        logger.warning("Table test failed, but continuing with other tests")
    
    # Test vector search
    if test_vector_search():
        tests_passed += 1
    else:
        tests_failed += 1
        logger.warning("Vector search test failed, but continuing with other tests")
    
    # Test verse similarity
    if test_verse_similarity():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Summary
    logger.info(f"Tests completed: {tests_passed} passed, {tests_failed} failed")
    
    if tests_failed == 0:
        logger.info("All vector search tests passed successfully!")
        return True
    else:
        logger.warning(f"{tests_failed} tests failed")
        return False

if __name__ == "__main__":
    successful = main()
    sys.exit(0 if successful else 1) 