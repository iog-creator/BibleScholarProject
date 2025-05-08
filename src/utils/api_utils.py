"""
API Utilities for Standardizing Response Formats

This module provides utilities for standardizing API responses across the application,
particularly for vector search and similar verse endpoints.
"""

from flask import jsonify
from typing import List, Dict, Any, Optional

def format_vector_search_response(
    results: List[Dict[str, Any]], 
    query: str, 
    translation: str
) -> Dict[str, Any]:
    """
    Format vector search results into a standardized response format.
    
    Args:
        results: List of search results from the database
        query: The original search query
        translation: The Bible translation used
        
    Returns:
        Standardized response dictionary
    """
    # Count occurrences of each book for distribution stats
    book_distribution = {}
    for result in results:
        book = result.get('book_name', '')
        if book in book_distribution:
            book_distribution[book] += 1
        else:
            book_distribution[book] = 1
    
    # Format results with additional fields
    formatted_results = []
    for result in results:
        # Calculate similarity percentage (0-100 scale instead of 0-1)
        similarity_pct = round(float(result.get('similarity', 0)) * 100, 1)
        
        # Add reference field for convenience
        reference = f"{result.get('book_name', '')} {result.get('chapter_num', '')}:{result.get('verse_num', '')}"
        
        # Format the result with standardized fields
        formatted_result = {
            'book_name': result.get('book_name', ''),
            'chapter_num': result.get('chapter_num', ''),
            'verse_num': result.get('verse_num', ''),
            'verse_id': result.get('verse_id', ''),
            'verse_text': result.get('verse_text', ''),
            'translation_source': result.get('translation_source', translation),
            'similarity': similarity_pct,
            'reference': reference,
            'context': {
                'previous': '',  # Could be populated if context is available
                'next': ''       # Could be populated if context is available
            }
        }
        formatted_results.append(formatted_result)
    
    # Construct the standardized response
    response = {
        'query': query,
        'translation': translation,
        'total_matches': len(results),
        'results': formatted_results,
        'metadata': {
            'book_distribution': book_distribution
        }
    }
    
    return response

def format_similar_verses_response(
    source_verse: Dict[str, Any],
    similar_verses: List[Dict[str, Any]],
    translation: str
) -> Dict[str, Any]:
    """
    Format similar verses results into a standardized response format.
    
    Args:
        source_verse: The reference verse
        similar_verses: List of similar verses
        translation: The Bible translation used
        
    Returns:
        Standardized response dictionary
    """
    # Format the source verse
    source_reference = f"{source_verse.get('book_name', '')} {source_verse.get('chapter_num', '')}:{source_verse.get('verse_num', '')}"
    formatted_source = {
        'reference': source_reference,
        'text': source_verse.get('verse_text', ''),
        'translation': translation,
        'book_name': source_verse.get('book_name', ''),
        'chapter_num': source_verse.get('chapter_num', ''),
        'verse_num': source_verse.get('verse_num', '')
    }
    
    # Format similar verses
    formatted_similar = []
    for verse in similar_verses:
        # Calculate similarity percentage (0-100 scale instead of 0-1)
        similarity_pct = round(float(verse.get('similarity', 0)) * 100, 1)
        
        # Add reference field for convenience
        reference = f"{verse.get('book_name', '')} {verse.get('chapter_num', '')}:{verse.get('verse_num', '')}"
        
        formatted_verse = {
            'reference': reference,
            'verse_text': verse.get('verse_text', ''),
            'similarity': similarity_pct,
            'book_name': verse.get('book_name', ''),
            'chapter_num': verse.get('chapter_num', ''),
            'verse_num': verse.get('verse_num', ''),
            'translation_source': verse.get('translation_source', translation)
        }
        formatted_similar.append(formatted_verse)
    
    # Construct the standardized response
    response = {
        'source_verse': formatted_source,
        'similar_verses': formatted_similar,
        'total_matches': len(similar_verses)
    }
    
    return response

def error_response(message: str, status_code: int = 400) -> tuple:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        
    Returns:
        Tuple of (response_json, status_code)
    """
    return jsonify({'error': message}), status_code 