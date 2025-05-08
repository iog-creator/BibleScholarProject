"""
Utility functions and helpers for the STEPBible Explorer project.

This module contains shared utility functions used across different components.
"""

# Import common utilities to be available directly from src.utils
from .file_utils import ensure_directory_exists, open_file_with_encoding, get_file_basename
from .db_utils import get_connection_from_env, execute_query, batch_insert
from .text_utils import normalize_text, clean_strong_number
from .logging_config import configure_logging, configure_etl_logging, configure_api_logging

# Import Bible reference parsing
from .bible_reference_parser import parse_reference, extract_references, is_valid_reference

# Import vector search functions
from .vector_search import search_verses_by_semantic_similarity, get_verse_by_reference

__all__ = [
    # File utilities
    'ensure_directory_exists', 
    'open_file_with_encoding', 
    'get_file_basename',
    
    # DB utilities
    'get_connection_from_env', 
    'execute_query', 
    'batch_insert',
    
    # Text utilities
    'normalize_text', 
    'clean_strong_number',
    
    # Bible reference utilities
    'parse_reference',
    'extract_references',
    'is_valid_reference',
    
    # Vector search utilities
    'search_verses_by_semantic_similarity',
    'get_verse_by_reference',
    
    # Logging utilities
    'configure_logging',
    'configure_etl_logging',
    'configure_api_logging'
] 