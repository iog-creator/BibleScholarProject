"""
Main integration test runner for all integration tests.

This file is used to run all integration tests in the correct order.
"""

import pytest
import logging
import os
import sys
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# First load environment variables
load_dotenv()

if __name__ == "__main__":
    logger.info("Starting integration tests")
    
    # Add paths for imports
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    
    # List of test modules to run
    test_modules = [
        "tests/integration/test_verse_data.py",
        "tests/integration/test_lexicon_data.py",
        "tests/integration/test_morphology_data.py",
        "tests/integration/test_database_integrity.py",
        "tests/integration/test_esv_bible_data.py"  # Add our new ESV test module
    ]
    
    # Run pytest with our test modules
    exit_code = pytest.main(["-v"] + test_modules)
    
    logger.info(f"Integration tests completed with exit code {exit_code}")
    sys.exit(exit_code) 