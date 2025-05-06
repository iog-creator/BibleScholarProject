# Database Test Skip Guidelines

## Overview

This document provides guidelines for skipping database-dependent tests in environments where a database connection is not available or should not be used.

## When to Skip Database Tests

Database tests should be skipped in the following scenarios:

1. **CI/CD Environments**: When running in CI/CD pipelines without database infrastructure
2. **Local Development**: When developing on a machine without the required database setup
3. **Quick Tests**: When running a quick test suite that should not depend on external services
4. **Offline Development**: When working in an offline environment

## Implementation Pattern

Use pytest's `skipif` decorator with a helper function to check database availability:

```python
import pytest
from src.database.connection import test_db_connection

def is_db_available():
    """Check if database is available for testing."""
    conn = test_db_connection()
    if conn:
        conn.close()
        return True
    return False

@pytest.mark.skipif(not is_db_available(), reason="Database not available")
def test_database_function():
    """Test that requires database access."""
    # Test implementation...
```

## Skip Configuration

Database test skipping can be configured via:

1. Environment variables:
   ```bash
   # Set to 1 to force skip all database tests regardless of availability
   export SKIP_DB_TESTS=1
   
   # Set to 1 to force run all database tests regardless of availability
   export FORCE_DB_TESTS=1
   ```

2. Pytest command line:
   ```bash
   # Skip all database tests
   pytest -m "not db"
   
   # Run only database tests
   pytest -m "db"
   ```

## Marking Database Tests

All database-dependent tests should be marked with the `db` marker:

```python
import pytest

@pytest.mark.db
def test_database_function():
    """Test that requires database access."""
    # Test implementation...
```

Register the marker in your `pytest.ini` file:
```ini
[pytest]
markers =
    db: marks tests that require database access
```

## Hybrid Testing Strategy

For critical components, implement both database-dependent and mock-based tests:

```python
import pytest
from unittest.mock import MagicMock

def test_function_with_mock():
    """Test using mocks instead of database."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [('expected result',)]
    
    result = function_under_test(mock_conn)
    assert result == 'expected result'

@pytest.mark.db
def test_function_with_db():
    """Test using actual database."""
    conn = get_db_connection()
    try:
        result = function_under_test(conn)
        assert result is not None
    finally:
        conn.close()
```

## Comprehensive Skip Function

Use this comprehensive function to determine if database tests should be skipped:

```python
import os
import pytest
from src.database.connection import test_db_connection

def should_skip_db_tests():
    """
    Determine if database tests should be skipped.
    
    Returns:
        tuple: (should_skip, reason)
    """
    # Check environment variable to force skip
    if os.environ.get('SKIP_DB_TESTS') == '1':
        return True, "SKIP_DB_TESTS is set"
    
    # Check environment variable to force run
    if os.environ.get('FORCE_DB_TESTS') == '1':
        return False, "FORCE_DB_TESTS is set"
    
    # Test actual connection
    conn = test_db_connection()
    if conn:
        conn.close()
        return False, "Database is available"
    
    return True, "Database is not available"

skip_db, skip_reason = should_skip_db_tests()

@pytest.mark.skipif(skip_db, reason=skip_reason)
@pytest.mark.db
def test_database_function():
    """Test that requires database access."""
    # Test implementation...
```

## Update History

- **2025-05-05**: Added comprehensive skip function
- **2025-04-10**: Added hybrid testing strategy
- **2025-03-01**: Added skip configuration options
- **2025-02-01**: Initial version created 