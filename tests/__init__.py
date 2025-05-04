"""
Test package for STEPBible-Datav2 TVTMS processing.
"""

import os
import tempfile
import logging

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
if not os.path.exists(TEST_DATA_DIR):
    os.makedirs(TEST_DATA_DIR) 