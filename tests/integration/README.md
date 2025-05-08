---
title: Integration Tests
description: Integration tests for the BibleScholarProject components
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../unit/README.md
  - ../../docs/guides/testing_framework.md
---
# Integration Tests

This directory contains integration tests for the BibleScholarProject components.

## Purpose

Integration tests validate that different components work together correctly, including:

1. API and database interactions
2. ETL pipeline workflows
3. Model training and inference pipelines
4. Web application functionality
5. Vector search integration with database

## Test Structure

- `test_api/` - Tests for API endpoints and integration
- `test_comprehensive_search/` - Tests for the comprehensive search functionality
- `test_database/` - Tests for database operations and transactions
- `test_models/` - Tests for model loading and inference
- `test_web/` - Tests for web application functionality

## Running Tests

Integration tests can be run using pytest:

```bash
# Run all integration tests
pytest tests/integration

# Run specific test module
pytest tests/integration/test_api

# Skip database-dependent tests
pytest tests/integration -k "not database"
```

## Adding Tests

When adding new integration tests:

1. Create a new file with the `test_` prefix
2. Add necessary fixtures or use existing ones from `templates/`
3. Document test requirements (database, external services, etc.)
4. Add appropriate decorators for skipping tests that require specific resources

## Cross-References
- [Test Suite](../README.md)
- [Unit Tests](../unit/README.md)
- [Testing Framework Guide](../../docs/guides/testing_framework.md) 