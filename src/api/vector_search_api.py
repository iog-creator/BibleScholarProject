#!/usr/bin/env python3
"""
Vector Search API

This module provides API endpoints for semantic search using pgvector:
- /api/vector-search - Search verses by semantic similarity
- /api/similar-verses - Find verses similar to a reference verse
- /api/compare-translations - Compare different translations of a verse
"""

import os
import logging
import json
from flask import Blueprint, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from dotenv import load_dotenv

# Import secure connection (if available, otherwise fall back to direct connection)
try:
    from src.database.secure_connection import get_secure_connection
    USE_SECURE_CONNECTION = True
except ImportError:
    USE_SECURE_CONNECTION = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
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

# Create Flask Blueprint
vector_search_api = Blueprint('vector_search_api', __name__)

def get_db_connection():
    """Get a connection to the database with dictionary cursor."""
    try:
        # Use secure connection if available (read-only mode for API)
        if USE_SECURE_CONNECTION:
            conn = get_secure_connection(mode='read')
            logger.info("Using secure READ-ONLY database connection")
            return conn
        
        # Fall back to direct connection
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        logger.info("Using direct database connection (not secure)")
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

def validate_translation(translation):
    """Validate and normalize translation code."""
    # Get list of valid translations
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT translation_source FROM bible.verse_embeddings")
        valid_translations = [row['translation_source'] for row in cursor.fetchall()]
        conn.close()
        
        # Check if the provided translation is valid
        if translation in valid_translations:
            return translation
        
        # If not valid, normalize and check again
        normalized = translation.upper()
        if normalized in valid_translations:
            return normalized
        
        # Return default translation if not found
        logger.warning(f"Invalid translation: {translation}, using KJV")
        return "KJV"
    except Exception as e:
        logger.error(f"Error validating translation: {e}")
        return "KJV"

@vector_search_api.route('/vector-search', methods=['GET'])
def vector_search():
    """
    Search for verses semantically related to the query.
    
    Parameters:
    - q: Search query
    - translation: Bible translation (default: KJV)
    - limit: Maximum number of results (default: 10)
    
    Returns:
    - JSON with results array
    """
    try:
        # Get parameters
        query = request.args.get('q', '')
        translation = validate_translation(request.args.get('translation', 'KJV'))
        limit = min(int(request.args.get('limit', 10)), 50)  # Cap at 50 results
        
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400
        
        # Get embedding for the query
        embedding = get_embedding(query)
        if not embedding:
            return jsonify({"error": "Failed to generate embedding for query"}), 500
        
        # Convert embedding to string format for PostgreSQL
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search for semantically similar verses
        search_query = """
        SELECT e.verse_id, e.book_name, e.chapter_num, e.verse_num, 
               v.verse_text, e.translation_source,
               1 - (e.embedding <=> %s::vector) as similarity
        FROM bible.verse_embeddings e
        JOIN bible.verses v ON e.verse_id = v.id
        WHERE e.translation_source = %s
        ORDER BY e.embedding <=> %s::vector
        LIMIT %s
        """
        
        cursor.execute(search_query, (embedding_str, translation, embedding_str, limit))
        results = cursor.fetchall()
        
        # Close the connection
        conn.close()
        
        # Convert decimal values to float for JSON serialization
        for result in results:
            result['similarity'] = float(result['similarity'])
        
        return jsonify({"results": results})
    
    except Exception as e:
        logger.error(f"Error in vector search: {e}")
        return jsonify({"error": str(e)}), 500

@vector_search_api.route('/similar-verses', methods=['GET'])
def similar_verses():
    """
    Find verses similar to a reference verse.
    
    Parameters:
    - reference: Verse reference (e.g., "John 3:16")
    - translation: Bible translation (default: KJV)
    - limit: Maximum number of results (default: 10)
    
    Returns:
    - JSON with results array
    """
    try:
        # Get parameters
        reference = request.args.get('reference', '')
        translation = validate_translation(request.args.get('translation', 'KJV'))
        limit = min(int(request.args.get('limit', 10)), 50)  # Cap at 50 results
        
        if not reference:
            return jsonify({"error": "Parameter 'reference' is required"}), 400
        
        # Parse the verse reference
        parts = reference.strip().split()
        if len(parts) < 2:
            return jsonify({"error": "Invalid verse reference format"}), 400
        
        book_name = " ".join(parts[:-1])
        chapter_verse = parts[-1].split(":")
        
        if len(chapter_verse) != 2:
            return jsonify({"error": "Invalid verse reference format"}), 400
        
        try:
            chapter_num = int(chapter_verse[0])
            verse_num = int(chapter_verse[1])
        except ValueError:
            return jsonify({"error": "Invalid chapter or verse number"}), 400
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First find the verse to ensure it exists
        verse_query = """
        SELECT v.id as verse_id 
        FROM bible.verses v
        WHERE v.translation_source = %s
        AND v.chapter = %s
        AND v.verse = %s
        AND LOWER(v.book) = LOWER(%s)
        LIMIT 1
        """
        
        cursor.execute(verse_query, (translation, chapter_num, verse_num, book_name))
        verse_result = cursor.fetchone()
        
        if not verse_result:
            return jsonify({"error": f"Verse not found: {reference}"}), 404
        
        verse_id = verse_result['verse_id']
            
        # Get the embedding for the reference verse
        ref_query = """
        SELECT e.embedding
        FROM bible.verse_embeddings e
        WHERE e.verse_id = %s
        AND e.translation_source = %s
        LIMIT 1
        """
        
        cursor.execute(ref_query, (verse_id, translation))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": f"No embedding found for verse: {reference}"}), 404
        
        # Search for similar verses
        search_query = """
        SELECT e.verse_id, e.book_name, e.chapter_num, e.verse_num, 
               v.verse_text, e.translation_source,
               1 - (e.embedding <=> %s) as similarity
        FROM bible.verse_embeddings e
        JOIN bible.verses v ON e.verse_id = v.id
        WHERE e.translation_source = %s
        AND e.verse_id != %s
        ORDER BY e.embedding <=> %s
        LIMIT %s
        """
        
        cursor.execute(search_query, (result['embedding'], translation, 
                                     verse_id, result['embedding'], limit))
        results = cursor.fetchall()
        
        # Close the connection
        conn.close()
        
        # Convert decimal values to float for JSON serialization
        for result in results:
            result['similarity'] = float(result['similarity'])
        
        return jsonify({"reference": reference, "results": results})
    
    except Exception as e:
        logger.error(f"Error finding similar verses: {e}")
        return jsonify({"error": str(e)}), 500

@vector_search_api.route('/compare-translations', methods=['GET'])
def compare_translations():
    """
    Compare translations of a verse using vector similarity.
    
    Parameters:
    - reference: Verse reference (e.g., "John 3:16")
    - base_translation: Base translation to compare against (default: KJV)
    
    Returns:
    - JSON with translations array
    """
    try:
        # Get parameters
        reference = request.args.get('reference', '')
        base_translation = validate_translation(request.args.get('base_translation', 'KJV'))
        
        if not reference:
            return jsonify({"error": "Parameter 'reference' is required"}), 400
        
        # Parse the verse reference
        parts = reference.strip().split()
        if len(parts) < 2:
            return jsonify({"error": "Invalid verse reference format"}), 400
        
        book_name = " ".join(parts[:-1])
        chapter_verse = parts[-1].split(":")
        
        if len(chapter_verse) != 2:
            return jsonify({"error": "Invalid verse reference format"}), 400
        
        try:
            chapter_num = int(chapter_verse[0])
            verse_num = int(chapter_verse[1])
        except ValueError:
            return jsonify({"error": "Invalid chapter or verse number"}), 400
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the base verse embedding
        base_query = """
        SELECT e.verse_id, e.book_name, e.chapter_num, e.verse_num, 
               v.verse_text, e.translation_source, e.embedding
        FROM bible.verse_embeddings e
        JOIN bible.verses v ON e.verse_id = v.id
        WHERE e.book_name = %s
        AND e.chapter_num = %s
        AND e.verse_num = %s
        AND e.translation_source = %s
        LIMIT 1
        """
        
        cursor.execute(base_query, (book_name, chapter_num, verse_num, base_translation))
        base_verse = cursor.fetchone()
        
        if not base_verse:
            return jsonify({"error": f"Verse not found: {reference} in {base_translation}"}), 404
        
        # Get all translations of the verse
        trans_query = """
        SELECT e.verse_id, e.book_name, e.chapter_num, e.verse_num, 
               v.verse_text, e.translation_source, e.embedding
        FROM bible.verse_embeddings e
        JOIN bible.verses v ON e.verse_id = v.id
        WHERE e.book_name = %s
        AND e.chapter_num = %s
        AND e.verse_num = %s
        AND e.translation_source != %s
        """
        
        cursor.execute(trans_query, (book_name, chapter_num, verse_num, base_translation))
        translations = cursor.fetchall()
        
        # Close the connection
        conn.close()
        
        # Calculate similarity scores
        results = []
        base_embedding = base_verse['embedding']
        
        # Add the base translation first
        base_result = dict(base_verse)
        base_result.pop('embedding', None)  # Remove embedding from response
        base_result['similarity'] = 1.0  # Perfect match with itself
        results.append(base_result)
        
        # Calculate similarity for other translations
        import numpy as np
        for trans in translations:
            trans_result = dict(trans)
            trans_embedding = trans_result.pop('embedding', None)
            
            # Calculate cosine similarity
            similarity = float(1 - (np.array(trans_embedding) - np.array(base_embedding)).dot(
                (np.array(trans_embedding) - np.array(base_embedding))
            ) / 2)
            
            trans_result['similarity'] = similarity
            results.append(trans_result)
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return jsonify({
            "reference": reference,
            "base_translation": base_translation,
            "translations": results
        })
    
    except Exception as e:
        logger.error(f"Error comparing translations: {e}")
        return jsonify({"error": str(e)}), 500

@vector_search_api.route('/available-translations', methods=['GET'])
def available_translations():
    """
    Get a list of available translations with vector embeddings.
    
    Returns:
    - JSON with translations array
    """
    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get available translations
        cursor.execute("""
        SELECT DISTINCT translation_source, 
               COUNT(*) as verse_count
        FROM bible.verse_embeddings
        GROUP BY translation_source
        ORDER BY translation_source
        """)
        
        translations = cursor.fetchall()
        
        # Close the connection
        conn.close()
        
        return jsonify({"translations": translations})
    
    except Exception as e:
        logger.error(f"Error getting available translations: {e}")
        return jsonify({"error": str(e)}), 500 