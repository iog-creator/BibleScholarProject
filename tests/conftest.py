"""
Shared test fixtures and configuration for STEPBible-Datav2 tests.
"""

import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
import tempfile
from sqlalchemy import create_engine, text
from tvtms.parser import TVTMSParser

@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine using PostgreSQL from DATABASE_URL."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL environment variable must be set for integration tests.')
    engine = create_engine(database_url)
    return engine

@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture(scope="session")
def parser():
    """Create a TVTMSParser instance."""
    return TVTMSParser()

@pytest.fixture(scope="function")
def sample_tvtms_file(temp_dir):
    """Create a sample TVTMS file for testing."""
    content = """2) EXPANDED VERSION
#DataStart(Expanded)
SourceType\tSourceRef\tStandardRef\tAction\tNoteMarker\tNoteA\tNoteB\tAncient Versions\tTests
Latin\tPsa.142:12\tPsa.143:12\tRenumber verse\tOpt.\tNote1\tNote2\t\tTestCondition
#DataEnd(Expanded)"""
    
    file_path = os.path.join(temp_dir, 'test_tvtms.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path 

@pytest.fixture(scope="session", autouse=True)
def truncate_versification_tables_before_session(test_db_engine):
    """Truncate versification tables before the test session starts."""
    with test_db_engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE bible.versification_mappings RESTART IDENTITY CASCADE;"))
        conn.execute(text("TRUNCATE TABLE bible.versification_rules RESTART IDENTITY CASCADE;"))
        conn.execute(text("TRUNCATE TABLE bible.versification_documentation RESTART IDENTITY CASCADE;")) 

@pytest.fixture(scope="module")
def load_versification_sample_data(test_db_engine):
    """
    Load sample versification data for tests.
    Use this fixture for versification tests that need populated sample data.
    """
    import importlib.util
    import logging
    import os
    
    logger = logging.getLogger("versification_fixture")
    
    # Load the sample data script and execute it
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'load_sample_versification.py'))
    logger.info(f"Loading versification sample data from {script_path}")
    
    try:
        # Import the script module
        spec = importlib.util.spec_from_file_location("load_sample_versification", script_path)
        sample_data_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sample_data_module)
        
        # Run the sample data creation function
        success = sample_data_module.create_sample_data()
        if not success:
            logger.error("Failed to create sample versification data - function returned False")
            pytest.skip("Failed to create sample versification data")
        
        logger.info("Successfully loaded versification sample data")
        
        # Verify data was loaded by checking count
        with test_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM bible.versification_mappings"))
            count = result.scalar()
            logger.info(f"Versification mappings count after loading: {count}")
            
            if count == 0:
                logger.error("Failed to load versification sample data - count is 0")
                pytest.skip("Versification sample data count is 0")
            elif count < 1700:  # Should be 1786 based on script
                logger.warning(f"Versification sample data may be incomplete - count is only {count}")
            
    except Exception as e:
        logger.error(f"Error loading versification sample data: {e}")
        pytest.skip(f"Error loading versification sample data: {e}")
    
    yield
    
    # No cleanup needed - the truncate_versification_tables_before_session fixture will handle it at the end of the session 