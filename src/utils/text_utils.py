"""
Text processing utilities for the STEPBible Explorer project.

This module contains utility functions for text processing operations.
"""
import re
import logging
import unicodedata

logger = logging.getLogger(__name__)

def normalize_text(text):
    """
    Normalize Unicode text.
    
    Args:
        text (str): Input text
        
    Returns:
        str: Normalized text
    """
    return unicodedata.normalize('NFC', text) if text else text

def clean_strong_number(strongs_id):
    """
    Clean and standardize a Strong's number.
    
    Args:
        strongs_id (str): Strong's ID (e.g., "H1234", "G5678")
        
    Returns:
        str: Standardized Strong's ID
    """
    if not strongs_id:
        return None
        
    # Remove leading zeros after the letter
    strongs_id = re.sub(r'^([HG])0+', r'\1', strongs_id)
    
    # If there's no H/G prefix, check if it's numeric and add H/G
    if not strongs_id.startswith('H') and not strongs_id.startswith('G'):
        try:
            num = int(re.sub(r'[^\d]', '', strongs_id))
            if num < 5000:  # Arbitrary threshold - Hebrew typically < 5000
                strongs_id = f"H{num}"
            else:
                strongs_id = f"G{num}"
        except ValueError:
            pass
            
    return strongs_id

def parse_reference(ref_str):
    """
    Parse a Bible reference string.
    
    Args:
        ref_str (str): Reference string (e.g., "Gen.1.1", "Mat.5.3")
        
    Returns:
        tuple: (book, chapter, verse) or None if parsing fails
    """
    # Handle various reference formats
    simple_match = re.match(r'(\w+)\.(\d+)\.(\d+)', ref_str)
    if simple_match:
        book, chapter, verse = simple_match.groups()
        return book, int(chapter), int(verse)
        
    # Handle parenthetical alternates (e.g., "Mat.15.6(15.5)")
    paren_match = re.match(r'(\w+)\.(\d+)\.(\d+)\(\d+\.\d+\)', ref_str)
    if paren_match:
        book, chapter, verse = paren_match.groups()
        return book, int(chapter), int(verse)
        
    # Handle square bracket alternates (e.g., "Mat.17.15[17.14]")
    bracket_match = re.match(r'(\w+)\.(\d+)\.(\d+)\[\d+\.\d+\]', ref_str)
    if bracket_match:
        book, chapter, verse = bracket_match.groups()
        return book, int(chapter), int(verse)
        
    # Handle curly brace alternates (e.g., "Rom.16.25{14.24}")
    brace_match = re.match(r'(\w+)\.(\d+)\.(\d+)\{\d+\.\d+\}', ref_str)
    if brace_match:
        book, chapter, verse = brace_match.groups()
        return book, int(chapter), int(verse)
        
    logger.warning(f"Failed to parse reference: {ref_str}")
    return None 