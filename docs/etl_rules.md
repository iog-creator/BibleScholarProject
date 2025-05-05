# BibleScholarProject ETL Rules

## [2025-06-05] Data Source Fallback Rule Clarification
- The data source fallback rule is now formalized and must be followed by all ETL and integration test scripts.
- If versification mapping or TVTMS source files are missing in the main data directory, scripts MUST automatically search for and use files from the secondary data source (STEPBible-Datav2 repo) at:
  
      C:\Users\mccoy\Documents\Projects\Projects\AiBibleProject\SecondBibleData\STEPBible-Datav2

- All ETL and test scripts must check the main data directory first, then the secondary source if files are missing. This ensures robust operation even if the main data directory is incomplete.
- This rule is now a required part of the ETL and test process and must be documented in all relevant scripts and documentation.

## Overview

This document describes the ETL (Extract, Transform, Load) rules and patterns for the BibleScholarProject.

## File Naming Conventions

- ETL scripts should be named with a `etl_` prefix: `etl_hebrew_ot.py`, `etl_lexicons.py`
- Data fix scripts should have a descriptive name with a `fix_` prefix: `fix_hebrew_strongs_ids.py`

## Common ETL Pattern

Each ETL script should follow this basic pattern:

```python
def extract_data(source_path):
    """
    Extract data from source file.
    """
    # Implementation...
    return extracted_data

def transform_data(extracted_data):
    """
    Transform data into the target format.
    """
    # Implementation...
    return transformed_data

def load_data(conn, transformed_data):
    """
    Load transformed data into the database.
    """
    try:
        cursor = conn.cursor()
        # Database operations...
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading data: {e}")
        raise
    finally:
        cursor.close()

def main(source_path):
    """
    Main ETL process.
    """
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return
        
        # Extract data
        extracted_data = extract_data(source_path)
        
        # Transform data
        transformed_data = transform_data(extracted_data)
        
        # Load data
        load_data(conn, transformed_data)
        
        logger.info(f"Successfully processed {source_path}")
    except Exception as e:
        logger.error(f"ETL process failed: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Command-line argument parsing
    main(source_path)
```

## Hebrew Strong's ID Handling

1. Hebrew Strong's IDs are stored in the `strongs_id` column of `bible.hebrew_ot_words`
2. The original grammar code formatting is preserved in the `grammar_code` column
3. Valid Strong's IDs are extracted from patterns like `{H1234}` in the `grammar_code`
4. Critical theological terms require special handling to ensure proper counts
5. Run the `fix_hebrew_strongs_ids.py` script to repair missing Strong's IDs

## Data Validation Rules

1. Implement validation checks after ETL processes:
   - Verify minimum word counts for critical theological terms
   - Ensure cross-language mappings are complete
   - Check for duplicate word references

2. Log validation results with statistics:
   ```python
   logger.info(f"Validated {term_name} ({strongs_id}): {count} occurrences")
   ```

## Error Handling and Logging

1. Each ETL script should have its own log file:
   ```python
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('etl_hebrew_ot.log'),
           logging.StreamHandler()
       ]
   )
   logger = logging.getLogger('etl_hebrew_ot')
   ```

2. Use consistent error handling:
   ```python
   try:
       # Operations...
   except Exception as e:
       logger.error(f"Error during operation: {e}")
       raise
   ```

3. Log statistics at the end of each ETL process:
   ```python
   logger.info(f"Processed {len(verses)} verses and {len(words)} words")
   ```

## Integration Test and Fixture Standards (2024-05-04)

- All TVTMS test fixtures and sample files must use the correct column headers and row format for the TVTMSParser: `SourceType, SourceRef, StandardRef, Action, NoteMarker, NoteA, NoteB, Ancient Versions, Tests`.
- All count-based tests should allow a ±1% margin of error unless strict equality is required for theological or regulatory reasons.
- Versification book coverage threshold is set to 80%. If coverage falls below 90%, a warning should be logged.
- Tests that require external data (e.g., Arabic Bible files) must be skipped if the data is missing, using `pytest.skipif` or equivalent.
- SQL queries in tests should use explicit type casts for chapter and verse fields to ensure cross-database compatibility (e.g., `source_chapter::integer`).

## Data Source Fallback Rule (2024-05-04)

- If versification mapping or TVTMS source files are missing in the main data directory, automatically search for and use files from the secondary data source (e.g., STEPBible-Datav2 repo) at C:\Users\mccoy\Documents\Projects\Projects\AiBibleProject\SecondBibleData\STEPBible-Datav2.
- This is the fallback location for all ETL and integration test data loads.
- All ETL and test scripts should check the main data directory first, then the secondary source if files are missing. 