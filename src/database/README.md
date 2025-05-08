---
title: Database Modules
description: Database connection and management modules for the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../../README.md
  - ../../docs/reference/DATABASE_SCHEMA.md
  - ../api/README.md
  - ../utils/README.md
---
# Database Modules

This directory contains database connection and management modules for the BibleScholarProject.

## Module Structure

- `connection.py` - Database connection management
- `models.py` - SQLAlchemy models for database tables
- `queries.py` - Common database queries
- `migrations.py` - Database migration utilities
- `secure_connection.py` - Secure database connection utilities

## Database Schema

The database schema is defined in the models and follows a structured approach to storing:

1. Bible text and verses
2. Strong's numbers and lexical data
3. Morphological information
4. Names and proper nouns
5. Vector embeddings for semantic search

Full schema documentation is available in [Database Schema](../../docs/reference/DATABASE_SCHEMA.md).

## Connection Management

Database connections are managed using a connection pool to ensure efficient use of resources. Connection utilities include:

- Connection pooling
- Secure connection handling
- Transaction management
- Error handling and retries

## Usage

Database modules are used by:

1. API endpoints for data retrieval
2. ETL scripts for data loading
3. Search modules for data querying
4. Testing utilities for database validation

## Cross-References
- [Main Project Documentation](../../README.md)
- [Database Schema](../../docs/reference/DATABASE_SCHEMA.md)
- [API Modules](../api/README.md)
- [Utility Modules](../utils/README.md) 