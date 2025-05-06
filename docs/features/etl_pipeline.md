# ETL Pipeline

This document provides comprehensive information about the Extract, Transform, Load (ETL) pipeline in the BibleScholarProject.

## Overview and Purpose

The ETL pipeline handles the ingestion, processing, and loading of biblical texts and related data into the BibleScholarProject database. This document serves as the single source of truth for all ETL processes, standards, and patterns to ensure consistent data processing across all components.

## Technical Implementation Details

### Data Sources

The ETL pipeline processes data from the following sources:

1. **Public Domain Bible Texts**
   - King James Version (KJV)
   - American Standard Version (ASV)
   - World English Bible (WEB)

2. **Original Language Texts**
   - Translators Amalgamated Hebrew OT (TAHOT)
   - Translators Amalgamated Greek NT (TAGNT)

3. **Licensed Texts**
   - English Standard Version (ESV) - sample verses only

4. **Supplementary Data**
   - Strong's Lexicon
   - Greek and Hebrew morphology data
   - Versification mapping (TVTMS)

### Data Source Authority

#### [2025-06-05] Data Source Fallback Rule

- The data source fallback rule is formalized for all ETL and integration test scripts.
- If versification mapping or TVTMS source files are missing in the main data directory, scripts MUST automatically search for and use files from the secondary data source (STEPBible-Datav2 repo) at:
  
  ```
  C:\Users\mccoy\Documents\Projects\Projects\AiBibleProject\SecondBibleData\STEPBible-Datav2
  ```

- All ETL and test scripts must check the main data directory first, then the secondary source if files are missing, ensuring robust operation even if the main data directory is incomplete.

#### TVTMS Data Source Authority

> **⚠️ Important: Only `data/raw/TVTMS_expanded.txt` is the authoritative source for versification mappings in the ETL pipeline.**
> 
> Do **not** use the `.tsv` file for ETL or integration. The `.tsv` is for reference or manual inspection only.

### Common ETL Pattern

Each ETL script follows this basic pattern:

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

### Parser Strictness Levels

When designing ETL parsers, three strictness levels are available:

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

### File Naming Conventions

- ETL scripts should be named with a `etl_` prefix: `etl_hebrew_ot.py`, `etl_lexicons.py`
- Data fix scripts should have a descriptive name with a `fix_` prefix: `fix_hebrew_strongs_ids.py`
- Verification scripts should be named with a `verify_` or `check_` prefix: `verify_data_processing.py`

## Special Data Processing Rules

### Hebrew Strong's ID Handling

1. Hebrew Strong's IDs are stored in the `strongs_id` column of `bible.hebrew_ot_words`
2. The original grammar code formatting is preserved in the `grammar_code` column
3. Valid Strong's IDs are extracted from patterns like `{H1234}` in the `grammar_code`
4. Critical theological terms require special handling to ensure proper counts
5. Run the `fix_hebrew_strongs_ids.py` script to repair missing Strong's IDs

### Pandas DataFrame Handling

#### Type Enforcement

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

#### Null Handling

- Always check for and handle NULL/NaN values explicitly:
  ```python
  # Replace NaN with None for database compatibility
  df = df.where(pd.notnull(df), None)
  
  # Or for specific columns
  df['column'] = df['column'].fillna('')
  ```

- Prefer explicit NULL values (`None`) over empty strings (`''`) for database operations
- Document the NULL handling approach for each DataFrame

### Greek Morphology Count Tolerance

When validating Greek morphology codes during ETL or testing:

- Expected count for Greek morphology codes is approximately 1,730
- Actual count may vary between 1,670 and 1,740
- Current count (as of 2025-05-05): 1,676

This variation is acceptable due to:
1. Ongoing refinements in the morphology tagging
2. Different handling of rare/disputed forms
3. Variations in how compound forms are counted

If count falls outside this range, run additional validation checks.

## Usage Examples

### Example 1: Loading Public Domain Bible Text

```python
from src.etl.public_domain_bible import load_public_domain_bible
from src.database.db_connector import get_db_connection

def load_kjv_bible():
    """
    Load the KJV Bible from the source JSON file
    """
    source_url = "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_kjv.json"
    conn = get_db_connection()
    
    try:
        load_public_domain_bible(conn, source_url, "KJV")
        print("KJV Bible loaded successfully")
    except Exception as e:
        print(f"Error loading KJV Bible: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    load_kjv_bible()
```

### Example 2: Validating Data After ETL

```python
from src.utils.data_validator import validate_theological_terms
from src.database.db_connector import get_db_connection

def validate_hebrew_theological_terms():
    """
    Validate that all required Hebrew theological terms are properly loaded
    """
    conn = get_db_connection()
    
    try:
        validation_results = validate_theological_terms(conn, "hebrew")
        
        for term, result in validation_results.items():
            if result["status"] == "PASS":
                print(f"✓ {term}: {result['count']} occurrences (expected: {result['expected']})")
            else:
                print(f"✗ {term}: {result['count']} occurrences (expected: {result['expected']})")
                
    except Exception as e:
        print(f"Error during validation: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    validate_hebrew_theological_terms()
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

## Data Validation Rules

1. Implement validation checks after ETL processes:
   - Verify minimum word counts for critical theological terms
   - Ensure cross-language mappings are complete
   - Check for duplicate word references

2. Log validation results with statistics:
   ```python
   logger.info(f"Validated {term_name} ({strongs_id}): {count} occurrences")
   ```

## Related Documentation

- See [Bible Translations](./bible_translations.md) for details on translation-specific ETL processes
- See [Theological Terms](./theological_terms.md) for theological term handling requirements
- See [Database Schema](../reference/DATABASE_SCHEMA.md) for the database schema that ETL processes must conform to
- See [Testing Framework](../guides/testing_framework.md) for ETL testing standards and practices

This document is complemented by the [etl_rules](.cursor/rules/features/etl_pipeline.mdc) and [etl_parser_strictness](.cursor/rules/standards/parser_strictness.mdc) cursor rules.

## Modification History

| Date | Author | Description |
|------|--------|-------------|
| 2025-06-05 | Project Team | Added Data Source Fallback Rule clarification |
| 2025-05-05 | Project Team | Updated Greek morphology count tolerance |
| 2025-04-20 | Project Team | Added pandas DataFrame handling guidelines |
| 2025-03-15 | Project Team | Added parser strictness levels |
| 2025-03-12 | Development Team | Added integration test and fixture standards |
| 2024-09-18 | Project Team | Enhanced error handling and logging guidelines |
| 2024-06-20 | Initial Author | Initial ETL pipeline documentation |
| 2024-02-10 | Initial Author | Initial document created |
| 2025-06-10 | Documentation Team | Consolidated ETL rules documentation | 