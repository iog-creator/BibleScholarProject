#!/usr/bin/env python3
"""
Vector-based semantic search API using pgvector.

This module provides endpoints for:
1. Searching Bible verses semantically using vector embeddings
2. Finding similar verses to a given verse
3. Comparing translations of the same verse

All searches use cosine similarity with the pgvector extension.
"""

import os
import re
import logging
import requests
from flask import Blueprint, request, jsonify
import psycopg
from psycopg.rows import dict_row
import numpy as np
from dotenv import load_dotenv

# Initialize blueprint
vector_search_api = Blueprint('vector_search_api', __name__)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/vector_search_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

@vector_search_api.route('/vector-search')
def vector_search():
    """
    Search for Bible verses using vector similarity.
    
    Query parameters:
        q: Search query
        translation: Bible translation to search (KJV, ASV)
        limit: Number of results to return (default: 10)
        
    Returns:
        JSON response with search results
    """
    query = request.args.get('q', '')
    translation = request.args.get('translation', 'KJV')
    limit = min(int(request.args.get('limit', 10)), 100)  # Limit to 100 max results
    
    if not query:
        return jsonify({
            'error': 'No search query provided'
        }), 400
        
    # Get query embedding
    query_embedding = get_embedding(query)
    if not query_embedding:
        return jsonify({
            'error': 'Failed to generate embedding for query'
        }), 500
    
    # Convert the Python list to a PostgreSQL array format
    embedding_array = "["
    for i, value in enumerate(query_embedding):
        if i > 0:
            embedding_array += ","
        embedding_array += str(value)
    embedding_array += "]"
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
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
            
        return jsonify({
            'query': query,
            'translation': translation,
            'results': results
        })
    except Exception as e:
        logger.error(f"Error in vector search: {e}")
        return jsonify({
            'error': f'Database error: {str(e)}'
        }), 500
    finally:
        conn.close()

@vector_search_api.route('/similar-verses')
def similar_verses():
    """
    Find verses similar to a reference verse.
    
    Query parameters:
        book: Bible book name
        chapter: Chapter number
        verse: Verse number
        translation: Bible translation (KJV, ASV)
        limit: Number of results to return (default: 10)
        
    Returns:
        JSON response with similar verses
    """
    book = request.args.get('book', '')
    chapter = request.args.get('chapter', '')
    verse = request.args.get('verse', '')
    translation = request.args.get('translation', 'KJV')
    limit = min(int(request.args.get('limit', 10)), 100)  # Limit to 100 max results
    
    if not book or not chapter or not verse:
        return jsonify({
            'error': 'Book, chapter, and verse parameters are required'
        }), 400
    
    conn = get_db_connection()
    try:
        # First, get the reference verse embedding
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    e.embedding
                FROM 
                    bible.verse_embeddings e
                    JOIN bible.verses v ON e.verse_id = v.id
                WHERE 
                    v.book_name = %s
                    AND v.chapter_num = %s
                    AND v.verse_num = %s
                    AND v.translation_source = %s
                LIMIT 1
                """,
                (book, int(chapter), int(verse), translation)
            )
            result = cur.fetchone()
            
            if not result:
                return jsonify({
                    'error': f'Verse not found: {book} {chapter}:{verse} ({translation})'
                }), 404
                
            reference_embedding = result['embedding']
            
            # Convert the embedding to the correct format
            embedding_array = "["
            for i, value in enumerate(reference_embedding):
                if i > 0:
                    embedding_array += ","
                embedding_array += str(value)
            embedding_array += "]"
            
            # Get similar verses
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
                    AND NOT (v.book_name = %s AND v.chapter_num = %s AND v.verse_num = %s)
                ORDER BY 
                    e.embedding <=> %s::vector
                LIMIT %s
                """,
                (embedding_array, translation, book, int(chapter), int(verse), embedding_array, limit)
            )
            results = cur.fetchall()
            
        # Get the reference verse text
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    book_name, 
                    chapter_num, 
                    verse_num, 
                    verse_text,
                    translation_source
                FROM 
                    bible.verses
                WHERE 
                    book_name = %s
                    AND chapter_num = %s
                    AND verse_num = %s
                    AND translation_source = %s
                LIMIT 1
                """,
                (book, int(chapter), int(verse), translation)
            )
            reference_verse = cur.fetchone()
            
        return jsonify({
            'reference_verse': reference_verse,
            'similar_verses': results
        })
    except Exception as e:
        logger.error(f"Error finding similar verses: {e}")
        return jsonify({
            'error': f'Database error: {str(e)}'
        }), 500
    finally:
        conn.close()

@vector_search_api.route('/compare-translations')
def compare_translations():
    """
    Compare different translations of the same verse.
    
    Query parameters:
        book: Bible book name
        chapter: Chapter number
        verse: Verse number
        
    Returns:
        JSON response with different translations of the verse
    """
    book = request.args.get('book', '')
    chapter = request.args.get('chapter', '')
    verse = request.args.get('verse', '')
    
    if not book or not chapter or not verse:
        return jsonify({
            'error': 'Book, chapter, and verse parameters are required'
        }), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    book_name, 
                    chapter_num, 
                    verse_num, 
                    verse_text,
                    translation_source
                FROM 
                    bible.verses
                WHERE 
                    book_name = %s
                    AND chapter_num = %s
                    AND verse_num = %s
                ORDER BY
                    translation_source
                """,
                (book, int(chapter), int(verse))
            )
            translations = cur.fetchall()
            
            if not translations:
                return jsonify({
                    'error': f'Verse not found: {book} {chapter}:{verse}'
                }), 404
                
        return jsonify({
            'reference': f'{book} {chapter}:{verse}',
            'translations': translations
        })
    except Exception as e:
        logger.error(f"Error comparing translations: {e}")
        return jsonify({
            'error': f'Database error: {str(e)}'
        }), 500
    finally:
        conn.close()

# Health check endpoint
@vector_search_api.route('/vector-search/health')
def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    # Check database connection
    db_connection = False
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.close()
        db_connection = True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    # Check LM Studio connection
    lm_studio_connection = False
    try:
        response = requests.get(f"{LM_STUDIO_API_URL}/v1/models", timeout=5)
        lm_studio_connection = response.status_code == 200
    except Exception as e:
        logger.error(f"LM Studio connection failed: {e}")
    
    status = "healthy" if db_connection and lm_studio_connection else "unhealthy"
    
    return jsonify({
        'status': status,
        'database_connection': db_connection,
        'lm_studio_connection': lm_studio_connection
    }) 