---
title: Raw Data
description: Raw data files before processing in the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../processed/README.md
  - ../../docs/features/etl_pipeline.md
---
# Raw Data

This directory contains raw data files before processing in the BibleScholarProject.

## Directory Structure

- `external_datasets/` - External datasets for training and evaluation
- `parallel_corpus/` - Parallel corpus data for Bible translations
- `step_bible/` - Raw data from STEP Bible Project
- `strong_concordance/` - Strong's concordance data
- `morphology/` - Morphological data for Bible texts

## Data Sources

Raw data comes from various sources:

1. STEP Bible Project (https://github.com/STEPBible/STEPBible-Data)
2. Public domain Bible translations
3. Strong's concordance and lexicons
4. Hebrew and Greek morphology resources
5. External datasets for training and evaluation

## Data Usage

Raw data should never be modified directly. Instead:

1. Create ETL scripts to process the raw data
2. Store the processed data in the `processed/` directory
3. Document the data transformation process
4. Validate the processed data against expected formats

## Adding New Data

When adding new raw data:

1. Create a subdirectory with a descriptive name
2. Include a README.md file explaining the data source and format
3. Document any licensing or attribution requirements
4. Create appropriate ETL scripts for processing

## Cross-References
- [Data Directory](../README.md)
- [Processed Data](../processed/README.md)
- [ETL Pipeline](../../docs/features/etl_pipeline.md) 