---
title: Test Data
description: Test data files for the BibleScholarProject tests
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../../data/README.md
  - ../../docs/guides/testing_framework.md
---
# Test Data

This directory contains test data files used by the BibleScholarProject test suite.

## Purpose

Test data files provide:

1. Sample inputs for unit and integration tests
2. Expected outputs for validation
3. Mock data for database tests
4. Fixtures for reproducible test scenarios

## Directory Structure

- `processed/` - Processed test data in the same format as production data
- `fixtures/` - Test fixtures for different test scenarios
- `mocks/` - Mock data for simulating external services
- `samples/` - Small sample datasets representing larger production data

## Adding Test Data

When adding new test data:

1. Keep files small and focused on specific test cases
2. Document the source and purpose of the data
3. Include expected outputs for validation tests
4. Ensure consistent formatting with production data

## Cross-References
- [Test Suite](../README.md)
- [Project Data Directory](../../data/README.md)
- [Testing Framework Guide](../../docs/guides/testing_framework.md) 