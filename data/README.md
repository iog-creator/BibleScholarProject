---
title: Data Directory
description: Data files and resources for the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../docs/features/etl_pipeline.md
  - ./processed/README.md
  - ./raw/README.md
---
# Data Directory

This directory contains data files and resources for the BibleScholarProject.

## Directory Structure

- [`processed/`](processed/) - Processed data files ready for use
- [`raw/`](raw/) - Raw data files before processing
- [`Tagged-Bibles/`](Tagged-Bibles/) - Tagged Bible files from STEP Bible Project

## Data Flow

1. Raw data is stored in the `raw/` directory
2. ETL scripts process the raw data
3. Processed data is stored in the `processed/` directory
4. Applications access the processed data

## Data Types

- Bible text files
- Strong's concordance data
- Morphology data
- Training data for models
- Validation datasets
- Vector embeddings

## Data Management

The project follows these data management principles:

1. Raw data is never modified directly
2. All data transformations are scripted and reproducible
3. Processed data should be validated against expected formats
4. Large binary files should be stored using Git LFS
5. Sensitive data should be properly secured

## Cross-References
- [Main Project Documentation](../README.md)
- [ETL Pipeline](../docs/features/etl_pipeline.md)
- [Processed Data](./processed/README.md)
- [Raw Data](./raw/README.md)
