# Testing Framework

> Note: This file was relocated from `docs\TESTING_FRAMEWORK.md` as part of the documentation reorganization.

# Testing Framework

This document describes the testing framework used in the BibleScholarProject, including the integration tests and their usage.

## Overview

The BibleScholarProject includes a comprehensive test suite to verify data integrity, functionality, and performance of various components. Tests are organized by type and functionality, with a focus on ensuring the reliability of the data processing and storage.

## Test Types

### Unit Tests

Located in the `tests/unit` directory, these tests focus on individual functions and classes.

### Integration Tests

Located in the `tests/integration` directory, these tests verify the interaction between components and the end-to-end functionality of the system.

## Integration Test Framework

### Main Components

- **Test Runner**: `tests/integration/test_integration.py` - A central script for running all integration tests in the correct order.
- **Database Connection**: Tests use the database connection defined in `src/database/connection.py`.
- **Test Configuration**: Tests can be configured through environment variables (see `.env.example`).

### Test Modules

| Module | Description |
|--------|-------------|
| `test_verse_data.py` | Tests for Bible verse data extraction and loading |
| `test_lexicon_data.py` | Tests for lexicon data integrity |
| `test_morphology_data.py` | Tests for morphology code handling |
| `test_database_integrity.py` | Tests for overall database integrity |
| `test_esv_bible_data.py` | Tests for ESV Bible data integration |
| `test_arabic_bible_data.py` | Tests for Arabic Bible data integrity |
| `test_etl.py` | Tests for the ETL pipeline |
| `test_versification_data.py` | Tests for versification mapping |

## Multi-Translation Testing

The BibleScholarProject now supports multiple Bible translations in the database. The test framework has been enhanced to handle this scenario.

### Key Improvements

1. **Flexible Verse Count Validation**:
   - Changed from exact count matching to minimum count expectations
   - Tests now verify that at least the base translations are present
   - New translations can be added without breaking existing tests

2. **Translation-Specific Testing**:
   - Added dedicated test modules for specific translations (e.g., `test_esv_bible_data.py`)
   - Each translation has its own verification tests tailored to its characteristics
   - Common patterns are reused while allowing for translation-specific logic

3. **Translation Statistics Reporting**:
   - Tests now report detailed statistics on each translation
   - Verse counts by translation are logged for verification
   - Book coverage is analyzed for each translation

4. **Database Integrity with Multiple Translations**:
   - Modified constraints testing to accommodate multiple translations
   - Updated book verse count tests to handle translation-specific variations
   - Enhanced relationship testing between verses and words across translations

### Example: ESV Bible Tests

The `test_esv_bible_data.py` module demonstrates the approach for translation-specific testing:

```python
def test_esv_verses_existence(db_engine):
    """Test that ESV verses exist in the database."""
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM bible.verses
            WHERE translation_source = 'ESV'
        """))
        esv_count = result.scalar()
        
    logger.info(f"Found {esv_count} ESV verses in the database")
    assert esv_count > 0, "No ESV verses found in the database"
```

### Adding Tests for New Translations

When adding a new translation to the database, follow these steps to create the corresponding tests:

1. **Create a Dedicated Test Module**:
   - Copy the pattern from `test_esv_bible_data.py`
   - Rename functions and variables to match the new translation
   - Adjust expected values based on the characteristics of the translation

2. **Update the Test Runner**:
   - Add the new test module to the list in `test_integration.py`

3. **Update Database Integrity Tests**:
   - Ensure `test_database_integrity.py` is aware of the new translation
   - Update any translation-specific assertions if needed

## Running Tests

### Running All Tests

```bash
cd tests/integration
python test_integration.py
```

### Running Specific Test Modules

```bash
python -m pytest tests/integration/test_esv_bible_data.py -v
```

### Running Individual Tests

```bash
python -m pytest tests/integration/test_esv_bible_data.py::test_esv_verses_existence -v
```

## Test Environment

Tests require a properly configured environment with:

1. A PostgreSQL database with the proper schema
2. Environment variables set in `.env` file
3. All required Python dependencies installed

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify `.env` file has correct database connection settings
   - Ensure PostgreSQL is running and accessible

2. **Missing Test Data**:
   - Run ETL scripts to load required data
   - Check database for expected tables and records

3. **Failing Translation-Specific Tests**:
   - Verify the translation is properly loaded
   - Check if the translation source identifier matches in tests

### Skipping Database Tests

If you want to skip database-dependent tests, you can unset the DATABASE_URL environment variable:

```bash
unset DATABASE_URL
python -m pytest tests/integration/
```

These tests will be marked as skipped with the reason "DATABASE_URL not set; skipping DB-dependent integration tests." 