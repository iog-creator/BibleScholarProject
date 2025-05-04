"""
File utilities for the STEPBible Explorer project.

This module contains utility functions for file operations.
"""
import os
import logging
import codecs

logger = logging.getLogger(__name__)

def ensure_directory_exists(directory_path):
    """
    Create a directory if it doesn't exist.
    
    Args:
        directory_path (str): Path to directory
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            logger.info(f"Created directory: {directory_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {str(e)}")
            return False
    return True

def open_file_with_encoding(file_path, mode='r', encoding='utf-8-sig', errors='replace'):
    """
    Open a file with proper encoding handling.
    
    Args:
        file_path (str): Path to file
        mode (str): File mode ('r', 'w', etc.)
        encoding (str): File encoding (default: utf-8-sig)
        errors (str): Error handling strategy (default: replace)
        
    Returns:
        file: File object
    """
    return codecs.open(file_path, mode=mode, encoding=encoding, errors=errors)

def get_file_basename(file_path):
    """
    Get the base filename without extension.
    
    Args:
        file_path (str): Path to file
        
    Returns:
        str: Base filename without extension
    """
    return os.path.splitext(os.path.basename(file_path))[0] 