"""
Utility functions for vector search operations.

This module provides common functions used across different vector search implementations.
"""

import os
import logging
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

def get_embedding(text):
    """
    Get embedding vector for text using LM Studio API.
    
    Args:
        text: Text to encode
        
    Returns:
        List of floats representing the embedding vector or None on error
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

def format_vector_for_postgres(vector):
    """
    Format a vector for PostgreSQL's vector type.
    
    Args:
        vector: List of floats representing a vector
        
    Returns:
        String representation of the vector in PostgreSQL format
    """
    if not vector:
        return None
        
    # Format the embedding array in PostgreSQL syntax
    embedding_array = "["
    for i, value in enumerate(vector):
        if i > 0:
            embedding_array += ","
        embedding_array += str(value)
    embedding_array += "]"
    
    return embedding_array

def get_theological_term_strongs_ids(language='hebrew'):
    """
    Get important theological term Strong's IDs by language.
    
    Args:
        language: 'hebrew' or 'greek'
        
    Returns:
        List of Strong's IDs for important theological terms
    """
    if language == 'hebrew':
        return [
            'H430',   # Elohim (God)
            'H3068',  # YHWH (LORD)
            'H113',   # Adon (Lord)
            'H2617',  # Chesed (lovingkindness)
            'H539'    # Aman (believe, faithful)
        ]
    elif language == 'greek':
        return [
            'G2316',  # Theos (God)
            'G2962',  # Kyrios (Lord)
            'G26',    # Agape (love)
            'G4102',  # Pistis (faith)
            'G5485'   # Charis (grace)
        ]
    else:
        return []

def determine_language_from_translation(translation):
    """
    Determine the language based on translation code.
    
    Args:
        translation: Translation code (e.g., 'KJV', 'TAHOT')
        
    Returns:
        Language type: 'hebrew', 'greek', 'english', 'arabic', or None
    """
    if translation in ['TAHOT']:
        return 'hebrew'
    elif translation in ['TAGNT']:
        return 'greek'
    elif translation in ['KJV', 'ASV', 'ESV']:
        return 'english'
    elif translation in ['ARABIC']:
        return 'arabic'
    else:
        return None

def get_lexicon_and_word_tables(translation):
    """
    Get appropriate lexicon and word tables for a translation.
    
    Args:
        translation: Translation code (e.g., 'KJV', 'TAHOT')
        
    Returns:
        Tuple of (lexicon_table, word_table, language)
    """
    language = determine_language_from_translation(translation)
    
    if language == 'hebrew':
        return 'bible.hebrew_entries', 'bible.hebrew_ot_words', language
    elif language == 'greek':
        return 'bible.greek_entries', 'bible.greek_nt_words', language
    elif language == 'arabic':
        return None, None, language
    else:
        return None, None, language 