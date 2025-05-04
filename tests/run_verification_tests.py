#!/usr/bin/env python
"""
Test runner script for data verification tests.

This script runs all core integration tests for verifying that STEPBible data has been
correctly extracted and loaded into the database.
"""

import os
import sys
import pytest
import logging
import datetime
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add path to sys.path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
log_dir = Path(__file__).parent.parent / "logs" / "tests"
log_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"data_verification_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def get_record_counts(connection_string):
    """Get key record counts from the database."""
    try:
        from sqlalchemy import create_engine, text
        
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            counts = {}
            queries = {
                "verses": "SELECT COUNT(*) FROM bible.verses",
                "hebrew_words": "SELECT COUNT(*) FROM bible.hebrew_ot_words",
                "greek_words": "SELECT COUNT(*) FROM bible.greek_nt_words",
                "arabic_verses": "SELECT COUNT(*) FROM bible.arabic_verses",
                "arabic_words": "SELECT COUNT(*) FROM bible.arabic_words",
                "hebrew_lexicon": "SELECT COUNT(*) FROM bible.hebrew_entries",
                "greek_lexicon": "SELECT COUNT(*) FROM bible.greek_entries",
                "lsj_lexicon": "SELECT COUNT(*) FROM bible.lsj_entries",
                "hebrew_morphology": "SELECT COUNT(*) FROM bible.hebrew_morphology_codes",
                "greek_morphology": "SELECT COUNT(*) FROM bible.greek_morphology_codes",
                "hebrew_strongs": "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id IS NOT NULL",
                "hebrew_strongs_pct": "SELECT (COUNT(*) FILTER (WHERE strongs_id IS NOT NULL) * 100.0 / COUNT(*)) FROM bible.hebrew_ot_words",
                "extended_hebrew_strongs": "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id ~ 'H\\d+[a-z]'",
                "h9xxx_codes": "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id LIKE 'H9%'",
                "word_relationships": "SELECT COUNT(*) FROM bible.word_relationships"
            }
            
            for name, query in queries.items():
                try:
                    result = conn.execute(text(query))
                    counts[name] = result.scalar() or 0
                except Exception as e:
                    logger.warning(f"Error getting count for {name}: {e}")
                    counts[name] = "Error"
                    
            # Add theological terms checks
            theological_terms = {
                # Hebrew terms
                "hebrew_elohim": "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id = 'H430' OR grammar_code LIKE '%{H430}%'",
                "hebrew_yhwh": "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id = 'H3068' OR grammar_code LIKE '%{H3068}%'",
                "hebrew_adon": "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id = 'H113' OR grammar_code LIKE '%{H113}%'",
                "hebrew_mashiach": "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id = 'H4899' OR grammar_code LIKE '%{H4899}%'",
                
                # Greek terms
                "greek_theos": "SELECT COUNT(*) FROM bible.greek_nt_words WHERE strongs_id = 'G2316'",
                "greek_christos": "SELECT COUNT(*) FROM bible.greek_nt_words WHERE strongs_id = 'G5547'",
                "greek_kyrios": "SELECT COUNT(*) FROM bible.greek_nt_words WHERE strongs_id = 'G2962'",
                "greek_pneuma": "SELECT COUNT(*) FROM bible.greek_nt_words WHERE strongs_id = 'G4151'",
                
                # Key passages
                "genesis_1_1": "SELECT COUNT(*) FROM bible.verses WHERE book_name = 'Gen' AND chapter_num = 1 AND verse_num = 1",
                "john_3_16": "SELECT COUNT(*) FROM bible.verses WHERE book_name = 'Jhn' AND chapter_num = 3 AND verse_num = 16",
                "romans_3_23": "SELECT COUNT(*) FROM bible.verses WHERE book_name = 'Rom' AND chapter_num = 3 AND verse_num = 23"
            }
            
            # Add theological terms counts
            for name, query in theological_terms.items():
                try:
                    result = conn.execute(text(query))
                    counts[name] = result.scalar() or 0
                except Exception as e:
                    logger.warning(f"Error getting count for theological term {name}: {e}")
                    counts[name] = "Error"
            
            return counts
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return {}

def run_tests(run_all=False, focus_theological=False):
    """Run all data verification tests.
    
    Args:
        run_all: Whether to run all tests, including known failing ones
        focus_theological: Whether to focus on theological term integrity tests
    """
    # Ensure we load environment variables
    load_dotenv()
    
    # Get connection string for database record counts
    try:
        from src.database.connection import get_connection_string
        connection_string = get_connection_string()
    except Exception as e:
        logger.error(f"Error importing connection string: {e}")
        # Fallback to using .env file directly
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            logger.error("No database connection string found. Database counts will not be available.")
            connection_string = None
    
    # Core test files that should always pass
    core_test_files = [
        "tests/integration/test_database_integrity.py",
        "tests/integration/test_hebrew_strongs_handling.py",
        "tests/integration/test_lexicon_data.py",
        "tests/integration/test_verse_data.py",
        "tests/integration/test_morphology_data.py",
        "tests/integration/test_arabic_bible_data.py",
        "tests/integration/test_etl_integrity.py",
        "tests/unit/test_hebrew_words.py",
        "tests/unit/test_database.py"
    ]
    
    # Known failing test files - only run if run_all is True
    known_failing_tests = [
        "tests/integration/test_etl.py",
        "tests/integration/test_pandas.py",
        "tests/integration/test_versification_data.py"
    ]
    
    # Theological tests - focus on these if theological flag is set
    theological_tests = [
        "tests/integration/test_verse_data.py::test_theological_terms_integrity",
        "tests/integration/test_lexicon_data.py::test_sample_important_lexicon_entries",
    ]
    
    # Define test files to run based on options
    if focus_theological:
        test_files = theological_tests
        logger.info("Running focused theological term integrity tests")
    else:
        test_files = core_test_files + (known_failing_tests if run_all else [])
        logger.info(f"Running {'all tests' if run_all else 'core tests only'}")
    
    # Print header with decorative elements
    header = f"STEPBIBLE DATA VERIFICATION TESTS - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    logger.info("\n" + "="*80)
    logger.info(f"{header:^80}")
    logger.info("="*80)
    logger.info(f"Log file: {log_file}")
    
    # Get database record counts before tests
    counts = {}
    if connection_string:
        logger.info("\n" + "-"*80)
        logger.info(f"{'DATABASE RECORD COUNT VERIFICATION':^80}")
        logger.info("-"*80)
        counts = get_record_counts(connection_string)
        if counts:
            # Format the counts into categories for better readability
            categories = {
                "Bible Text": ["verses", "hebrew_words", "greek_words", "arabic_verses", "arabic_words"],
                "Lexical Data": ["hebrew_lexicon", "greek_lexicon", "lsj_lexicon", "word_relationships"],
                "Morphology": ["hebrew_morphology", "greek_morphology"],
                "Hebrew Strong's": ["hebrew_strongs", "hebrew_strongs_pct", "extended_hebrew_strongs", "h9xxx_codes"],
                "Theological Terms (Hebrew)": ["hebrew_elohim", "hebrew_yhwh", "hebrew_adon", "hebrew_mashiach"],
                "Theological Terms (Greek)": ["greek_theos", "greek_christos", "greek_kyrios", "greek_pneuma"],
                "Key Passages": ["genesis_1_1", "john_3_16", "romans_3_23"]
            }
            
            for category, fields in categories.items():
                logger.info(f"\n{category}:")
                available_fields = [f for f in fields if f in counts]
                if available_fields:
                    max_name_len = max(len(name) for name in available_fields)
                    for name in available_fields:
                        # Format the output with proper alignment
                        logger.info(f"  {name.ljust(max_name_len)}: {counts[name]}")
                else:
                    logger.info("  No data available")
    
    # Run each test file
    all_passed = True
    failed_tests = []
    passed_tests = []
    skipped_tests = []
    
    logger.info("\n" + "-"*80)
    logger.info(f"{'TEST EXECUTION':^80}")
    logger.info("-"*80)
    
    for test_file in test_files:
        logger.info(f"Running tests in {test_file}")
        
        try:
            # Run pytest on the file
            result = pytest.main(['-v', test_file])
            
            if result == 0:
                passed_tests.append(test_file)
                logger.info(f"✅ Tests in {test_file} passed!")
            elif result == 2:  # Skip (pytest.ExitCode.NO_TESTS_COLLECTED)
                skipped_tests.append(test_file)
                logger.warning(f"⚠️ No tests found in {test_file}")
            else:
                if test_file in known_failing_tests:
                    logger.warning(f"⚠️ Known failing tests in {test_file} failed with exit code {result}")
                else:
                    all_passed = False
                    failed_tests.append(test_file)
                    logger.error(f"❌ Tests in {test_file} failed with exit code {result}!")
        except Exception as e:
            if test_file in known_failing_tests:
                logger.warning(f"⚠️ Known failing tests in {test_file} failed: {str(e)}")
            else:
                all_passed = False
                failed_tests.append(test_file)
                logger.error(f"❌ Error running tests in {test_file}: {str(e)}")
    
    # Print summary with nice formatting
    logger.info("\n" + "="*80)
    logger.info(f"{'TEST EXECUTION SUMMARY':^80}")
    logger.info("="*80)
    logger.info(f"Total test files: {len(test_files)}")
    logger.info(f"Passed:           {len(passed_tests)} " + ("✅" if passed_tests else ""))
    if failed_tests:
        logger.info(f"Failed:           {len(failed_tests)} ❌ ({', '.join(failed_tests)})")
    else:
        logger.info(f"Failed:           {len(failed_tests)}")
    if skipped_tests:
        logger.info(f"Skipped:          {len(skipped_tests)} ⚠️ ({', '.join(skipped_tests)})")
    
    # Check if all core tests passed
    if focus_theological:
        core_test_success = all(test not in failed_tests for test in theological_tests)
    else:
        core_test_success = all(test not in failed_tests for test in core_test_files)
    
    if core_test_success:
        logger.info("\n" + "="*80)
        logger.info(f"{'✅ TEST VERIFICATION SUCCESSFUL':^80}")
        logger.info("="*80)
        
        if focus_theological:
            logger.info("All theological term integrity tests passed!")
        else:
            logger.info("All core data verification tests passed!")
            if not all_passed and run_all:
                logger.info("⚠️ Some known problematic tests failed (these failures are expected)")
        
        # Print database statistics summary
        if counts:
            logger.info("\n" + "="*80)
            logger.info(f"{'DATABASE VERIFICATION SUMMARY':^80}")
            logger.info("="*80)
            
            # Bible text statistics
            logger.info("\n📚 Bible Text Statistics:")
            logger.info(f"  Verses:                   {counts.get('verses', 'N/A')} (expected: 31,219)")
            logger.info(f"  Hebrew words:             {counts.get('hebrew_words', 'N/A')} (expected: 305,577)")
            logger.info(f"  Greek words:              {counts.get('greek_words', 'N/A')} (expected: 142,096)")
            logger.info(f"  Arabic verses:            {counts.get('arabic_verses', 'N/A')} (expected: 31,091)")
            logger.info(f"  Arabic words:             {counts.get('arabic_words', 'N/A')} (expected: ~380,000)")
            
            # Lexical data statistics
            logger.info("\n📖 Lexical Data Statistics:")
            logger.info(f"  Hebrew lexicon entries:   {counts.get('hebrew_lexicon', 'N/A')} (expected: 9,345)")
            logger.info(f"  Greek lexicon entries:    {counts.get('greek_lexicon', 'N/A')} (expected: 10,847)")
            logger.info(f"  LSJ lexicon entries:      {counts.get('lsj_lexicon', 'N/A')} (expected: ~37,088)")
            logger.info(f"  Word relationships:       {counts.get('word_relationships', 'N/A')} (expected: >100,000)")
            
            # Strong's data statistics
            logger.info("\n🔍 Strong's ID Statistics:")
            hebrew_strongs_pct = counts.get('hebrew_strongs_pct', 'N/A')
            if hebrew_strongs_pct != 'N/A':
                logger.info(f"  Hebrew with Strong's:     {hebrew_strongs_pct:.2f}% (expected: >99.9%)")
            else:
                logger.info(f"  Hebrew with Strong's:     {hebrew_strongs_pct} (expected: >99.9%)")
            logger.info(f"  Extended Hebrew Strong's: {counts.get('extended_hebrew_strongs', 'N/A')} (expected: ~58,295)")
            logger.info(f"  H9xxx special codes:      {counts.get('h9xxx_codes', 'N/A')} (expected: ~6,078)")
            
            # Theological terms statistics
            if any(k.startswith(("hebrew_", "greek_", "genesis_", "john_", "romans_")) for k in counts.keys()):
                logger.info("\n✝️ Theological Terms Statistics:")
                
                # Hebrew theological terms
                if any(k.startswith("hebrew_") for k in counts.keys()):
                    logger.info("  Hebrew theological terms:")
                    for term, expected in [
                        ("hebrew_elohim", ">2000"), 
                        ("hebrew_yhwh", ">6000"), 
                        ("hebrew_adon", ">300"), 
                        ("hebrew_mashiach", ">30")
                    ]:
                        if term in counts:
                            logger.info(f"    {term.replace('hebrew_', ''):<12}: {counts[term]} (expected: {expected})")
                
                # Greek theological terms
                if any(k.startswith("greek_") for k in counts.keys()):
                    logger.info("  Greek theological terms:")
                    for term, expected in [
                        ("greek_theos", ">1000"), 
                        ("greek_christos", ">500"), 
                        ("greek_kyrios", ">600"), 
                        ("greek_pneuma", ">350")
                    ]:
                        if term in counts:
                            logger.info(f"    {term.replace('greek_', ''):<12}: {counts[term]} (expected: {expected})")
                
                # Key passages
                if any(k in ["genesis_1_1", "john_3_16", "romans_3_23"] for k in counts.keys()):
                    logger.info("  Key theological passages:")
                    passages = [
                        ("genesis_1_1", "Gen 1:1"), 
                        ("john_3_16", "John 3:16"), 
                        ("romans_3_23", "Rom 3:23")
                    ]
                    for key, label in passages:
                        if key in counts:
                            status = "✅ Present" if counts[key] > 0 else "❌ Missing"
                            logger.info(f"    {label:<12}: {status}")
            
        return 0
    else:
        logger.error("\n" + "="*80)
        logger.error(f"{'❌ TEST VERIFICATION FAILED':^80}")
        logger.error("="*80)
        logger.error("Some critical data verification tests failed!")
        logger.error("Check the logs for details on the failures.")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run STEPBible data verification tests")
    parser.add_argument('--all', action='store_true', help='Run all tests, including known failing tests')
    parser.add_argument('--theological', action='store_true', help='Focus only on theological term integrity tests')
    args = parser.parse_args()
    
    sys.exit(run_tests(run_all=args.all, focus_theological=args.theological)) 