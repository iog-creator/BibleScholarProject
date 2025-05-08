---
title: API Modules
description: API endpoints and services for the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../../README.md
  - ../../docs/reference/API_REFERENCE.md
  - ../database/README.md
  - ../utils/README.md
---
# API Modules

This directory contains API endpoints and services for the BibleScholarProject.

## API Structure

- `bible_qa_api.py` - Bible question-answering API endpoints
- `search_api.py` - Search API endpoints for text and semantic search
- `vector_search_api.py` - Vector search API endpoints for semantic search
- `data_api.py` - Data retrieval API endpoints
- `authentication.py` - Authentication and authorization utilities

## Endpoint Documentation

Detailed API documentation is available in [API Reference](../../docs/reference/API_REFERENCE.md).

Key endpoints include:

- `/api/bible/qa` - Bible question-answering endpoint
- `/api/search/text` - Text search endpoint
- `/api/search/vector` - Vector search endpoint
- `/api/verses` - Verse retrieval endpoint
- `/api/strongs` - Strong's concordance endpoint

## Usage

API endpoints are used by:

1. Web application for user interface
2. Command-line tools for testing and debugging
3. Integration with external services
4. Client applications

## Adding New Endpoints

When adding new endpoints:

1. Follow the existing patterns and conventions
2. Document the endpoint in the API reference
3. Add appropriate tests in `tests/integration/test_api/`
4. Ensure proper error handling and validation

## Cross-References
- [Main Project Documentation](../../README.md)
- [API Reference](../../docs/reference/API_REFERENCE.md)
- [Database Documentation](../database/README.md)
- [Utility Modules](../utils/README.md) 