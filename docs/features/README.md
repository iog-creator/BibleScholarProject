---
title: Features Documentation
description: Documentation of all major features and capabilities in the BibleScholarProject.
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ./etl_pipeline.md
  - ./theological_terms.md
  - ../guides/system_build_guide.md
---
# Features Directory

This directory contains documentation of all major features and capabilities in the BibleScholarProject.

See the [Documentation Index](../README.md) for the full documentation structure.

## Available Features

### Vector Search

- [Vector Search Web Integration](vector_search_web_integration.md) - Integration of pgvector semantic search with web applications
- [PgVector Semantic Search](../../README_VECTOR_SEARCH.md) - Core implementation of semantic search using PostgreSQL's pgvector extension

### Bible Processing

- [Public Domain Bible Processing](../../README_BIBLE_CORPUS.md) - Guidelines for processing public domain Bible translations
- [Bible QA System](../../README_BIBLE_QA.md) - Question answering system for Bible content

### Data Processing

- [ETL Pipeline](etl_pipeline.md) - Extraction, transformation, and loading of Bible data
- [DSPy Integration](../../README_DSPY.md) - Integration with DSPy for training language models

## Adding New Features

When adding documentation for a new feature:

1. Create a new markdown file in this directory
2. Update this README.md to include a reference to the new file
3. Follow the standard documentation format (Overview, Components, API, Usage, Examples)
4. Add appropriate cross-references to related documentation 

## Cross-References
- [Documentation Index](../README.md)
- [ETL Pipeline](./etl_pipeline.md)
- [Theological Terms](./theological_terms.md)
- [System Build Guide](../guides/system_build_guide.md) 