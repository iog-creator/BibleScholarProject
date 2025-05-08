---
title: Utility Modules
description: Utility functions and helpers for the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../../README.md
  - ../api/README.md
  - ../database/README.md
  - ../dspy_programs/README.md
---
# Utility Modules

This directory contains utility functions and helpers used throughout the BibleScholarProject.

## Modules

- **`database_utils.py`**: Database connection and query utilities
- **`logging_utils.py`**: Logging configuration and helpers
- **`file_utils.py`**: File operations and path management
- **`text_processing.py`**: Text processing and normalization utilities
- **`vector_utils.py`**: Vector operations for semantic search

## Usage

These utility functions are imported by other modules in the project to avoid code duplication and maintain consistency in common operations.

## Adding New Utilities

When adding new utility functions:

1. Use the appropriate existing module or create a new one for a specific domain
2. Document each function with docstrings
3. Add tests for the new functions in the `tests/unit` directory
4. Update this README if adding new modules

## Cross-References
- [Main Project Documentation](../../README.md)
- [API Documentation](../api/README.md)
- [Database Documentation](../database/README.md)
- [DSPy Programs](../dspy_programs/README.md) 