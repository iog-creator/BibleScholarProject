---
title: Names ETL Modules
description: Modules for processing biblical names in the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../../../docs/features/etl_pipeline.md
  - ../morphology/README.md
---
# Names ETL Modules

This directory contains modules for processing biblical names in the BibleScholarProject.

## Module Structure

- `hebrew_names.py` - Processing Hebrew proper names
- `greek_names.py` - Processing Greek proper names
- `name_variants.py` - Processing name variants across languages
- `name_validators.py` - Validation utilities for names data

## Names Processing

Names processing includes:

1. Extracting proper names from biblical texts
2. Mapping names across different languages
3. Identifying name variants and transliterations
4. Creating name dictionaries and concordances
5. Loading processed names into the database

## Name Types

The project processes various types of names:

- Personal names (people)
- Place names (locations)
- Deity names
- Cultural/ethnic group names
- Other proper nouns

## Usage

Names modules are used in the ETL pipeline to process biblical names and create searchable name databases for cross-linguistic studies.

## Cross-References
- [ETL Modules](../README.md)
- [ETL Pipeline](../../../docs/features/etl_pipeline.md)
- [Morphology ETL Modules](../morphology/README.md) 