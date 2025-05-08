---
title: Processed Data
description: Processed data files ready for use in the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../raw/README.md
  - ../../docs/features/etl_pipeline.md
---
# Processed Data

This directory contains processed data files that are ready for use in the BibleScholarProject.

## Directory Structure

- `bible_training_data/` - Processed Bible text data for training
- `dspy_training_data/` - Training data for DSPy models
  - `bible_corpus/` - Bible corpus for DSPy training
  - `metrics/` - Metrics and evaluation data for models
- `embeddings/` - Vector embeddings for semantic search
- `metadata/` - Metadata for Bible texts and related resources

## Data Formats

Data is stored in various formats depending on the use case:

- CSV files for tabular data
- JSON files for structured data
- Parquet files for efficient storage and querying
- HDF5 files for vector embeddings
- SQLite databases for local testing

## Usage

Processed data is used by:

1. Model training and evaluation scripts
2. DSPy programs for semantic search and question answering
3. API endpoints for data retrieval
4. Web application for visualization and interaction

## Adding New Data

When adding new processed data:

1. Create a subdirectory with a descriptive name
2. Include a README.md file explaining the data format and contents
3. Document the processing workflow in the appropriate ETL script
4. Add validation tests to ensure data integrity

## Cross-References
- [Data Directory](../README.md)
- [Raw Data](../raw/README.md)
- [ETL Pipeline](../../docs/features/etl_pipeline.md) 