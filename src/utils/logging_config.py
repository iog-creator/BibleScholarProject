"""
Logging configuration for the STEPBible Explorer project.

This module provides consistent logging configuration across all components.
"""
import os
import logging
import logging.handlers
from .file_utils import ensure_directory_exists

def configure_logging(logger_name, log_file=None, log_level=logging.INFO):
    """
    Configure logging for a component.
    
    Args:
        logger_name (str): Name of the logger
        log_file (str, optional): Path to log file
        log_level (int): Logging level (default: INFO)
        
    Returns:
        logger: Configured logger
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Always add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log_file is provided
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        ensure_directory_exists(log_dir)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def configure_etl_logging(component_name):
    """
    Configure logging for ETL components.
    
    Args:
        component_name (str): Name of the ETL component
        
    Returns:
        logger: Configured logger
    """
    log_file = f"logs/etl/{component_name}.log"
    return configure_logging(f"etl.{component_name}", log_file)

def configure_api_logging(component_name):
    """
    Configure logging for API components.
    
    Args:
        component_name (str): Name of the API component
        
    Returns:
        logger: Configured logger
    """
    log_file = f"logs/api/{component_name}.log"
    return configure_logging(f"api.{component_name}", log_file) 