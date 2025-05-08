---
title: Data Scripts
description: Scripts for data processing and management in the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../../data/README.md
  - ../../docs/features/etl_pipeline.md
---
# Data Scripts

This directory contains scripts for data processing and management in the BibleScholarProject.

## Scripts

- `process_bible_data.py` - Process raw Bible data into structured formats
- `generate_embeddings.py` - Generate embeddings for Bible texts
- `validate_data.py` - Validate processed data for integrity and completeness
- `export_data.py` - Export processed data to various formats
- `import_external_datasets.py` - Import external datasets for training

## Purpose

These scripts are used to:

1. Transform raw Bible texts into structured formats
2. Generate embeddings for semantic search
3. Validate data integrity and completeness
4. Export data for use in models and APIs
5. Import and process external datasets

## Usage

Most scripts can be run directly with Python. For example:

```
python process_bible_data.py --input path/to/input --output path/to/output
```

## Cross-References
- [Scripts Directory](../README.md)
- [Data Directory](../../data/README.md)
- [ETL Pipeline](../../docs/features/etl_pipeline.md) 