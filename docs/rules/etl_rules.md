# ETL Rules for BibleScholarProject

## Overview

This document describes the ETL (Extract, Transform, Load) rules and patterns for the BibleScholarProject. These rules ensure consistent data processing across all components.

## Data Source Authority

### [2025-06-05] Data Source Fallback Rule

- The data source fallback rule is now formalized and must be followed by all ETL and integration test scripts.
- If versification mapping or TVTMS source files are missing in the main data directory, scripts MUST automatically search for and use files from the secondary data source (STEPBible-Datav2 repo) at:
  
  ```
  C:\Users\mccoy\Documents\Projects\Projects\AiBibleProject\SecondBibleData\STEPBible-Datav2
  ```

- All ETL and test scripts must check the main data directory first, then the secondary source if files are missing. This ensures robust operation even if the main data directory is incomplete.

### TVTMS Data Source Authority

> **⚠️ Important: Only `data/raw/TVTMS_expanded.txt` is the authoritative source for versification mappings in the ETL pipeline.**
> 
> Do **not** use the `.tsv` file for ETL or integration. The `.tsv` is for reference or manual inspection only.

## File Naming Conventions

- ETL scripts should be named with a `etl_` prefix: `etl_hebrew_ot.py`, `etl_lexicons.py`
- Data fix scripts should have a descriptive name with a `fix_` prefix: `fix_hebrew_strongs_ids.py`
- Verification scripts should be named with a `verify_` or `check_` prefix: `verify_data_processing.py`

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

## Parser Strictness Levels

When designing ETL parsers, three strictness levels should be available:

1. **Strict**: Throw exceptions for any formatting issues. Use for initial development and format validation.
   ```python
   parser = BibleParser(strictness="strict")
   ```

2. **Tolerant**: Attempt to recover from minor formatting issues, log warnings. Use for production.
   ```python
   parser = BibleParser(strictness="tolerant")
   ```

3. **Permissive**: Accept almost any input, make best guess, log errors. Use only for data recovery.
   ```python
   parser = BibleParser(strictness="permissive")
   ```

Always default to **Tolerant** mode for most ETL processes unless there's a specific reason to change.

## Hebrew Strong's ID Handling

1. Hebrew Strong's IDs are stored in the `strongs_id` column of `bible.hebrew_ot_words`
2. The original grammar code formatting is preserved in the `grammar_code` column
3. Valid Strong's IDs are extracted from patterns like `{H1234}` in the `grammar_code`
4. Critical theological terms require special handling to ensure proper counts
5. Run the `fix_hebrew_strongs_ids.py` script to repair missing Strong's IDs

See [theological_terms.md](theological_terms.md) for detailed theological term handling requirements.

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

## Integration Test and Fixture Standards

- All TVTMS test fixtures and sample files must use the correct column headers and row format for the TVTMSParser: `SourceType, SourceRef, StandardRef, Action, NoteMarker, NoteA, NoteB, Ancient Versions, Tests`.
- All count-based tests should allow a ±1% margin of error unless strict equality is required for theological or regulatory reasons.
- Versification book coverage threshold is set to 80%. If coverage falls below 90%, a warning should be logged.
- Tests that require external data (e.g., Arabic Bible files) must be skipped if the data is missing, using `pytest.skipif` or equivalent.
- SQL queries in tests should use explicit type casts for chapter and verse fields to ensure cross-database compatibility (e.g., `source_chapter::integer`).

## Pandas DataFrame Handling

### Type Enforcement

- Always enforce specific data types for DataFrame columns:
  ```python
  df = df.astype({
      'strongs_id': 'str', 
      'verse_id': 'int',
      'position': 'int'
  })
  ```

- Use appropriate types for numeric IDs (int) vs. text fields (str)
- Add explicit type validation before database operations

### Null Handling

- Always check for and handle NULL/NaN values explicitly:
  ```python
  # Replace NaN with None for database compatibility
  df = df.where(pd.notnull(df), None)
  
  # Or for specific columns
  df['column'] = df['column'].fillna('')
  ```

- Prefer explicit NULL values (`None`) over empty strings (`''`) for database operations
- Document the NULL handling approach for each DataFrame

## Greek Morphology Count Tolerance

When validating Greek morphology codes during ETL or testing:

- Expected count for Greek morphology codes is approximately 1,730
- Actual count may vary between 1,670 and 1,740
- Current count (as of 2025-05-05): 1,676

This variation is acceptable due to:
1. Ongoing refinements in the morphology tagging
2. Different handling of rare/disputed forms
3. Variations in how compound forms are counted

If count falls outside this range, run additional validation checks.

## Update History

- **2025-06-05**: Added Data Source Fallback Rule
- **2025-05-05**: Updated Greek morphology count tolerance
- **2025-04-20**: Added pandas DataFrame handling guidelines
- **2025-03-15**: Added parser strictness levels
- **2025-02-10**: Initial document created 