---
title: Test Suite
description: Tests for the BibleScholarProject including unit, integration, and benchmarks
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../docs/guides/testing_framework.md
  - ./unit/README.md
  - ./integration/README.md
---
# Test Suite

This directory contains tests for the BibleScholarProject including unit tests, integration tests, and benchmarks.

## Directory Structure

- [`unit/`](unit/) - Unit tests for individual components
- [`integration/`](integration/) - Integration tests for system components
- [`templates/`](templates/) - Test templates and shared fixtures
- [`data/`](data/) - Test data files
- [`.benchmarks/`](.benchmarks/) - Performance benchmark results

## Running Tests

Tests can be run using pytest:

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit

# Run integration tests only
pytest tests/integration

# Run with coverage
pytest --cov=src tests/
```

## Writing Tests

When writing tests:

1. Place unit tests in `unit/` directory
2. Place integration tests in `integration/` directory
3. Use fixtures from `templates/` directory
4. Follow the naming convention `test_*.py`
5. Use appropriate decorators for skipping database tests if necessary

## Benchmarking

Performance benchmarks are run and stored in the `.benchmarks/` directory.

```bash
# Run benchmarks
pytest tests/ --benchmark-autosave
```

## Cross-References
- [Main Project Documentation](../README.md)
- [Testing Framework Guide](../docs/guides/testing_framework.md)
- [Unit Tests](./unit/README.md)
- [Integration Tests](./integration/README.md) 