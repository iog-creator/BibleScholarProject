---
title: Morphology ETL Modules
description: Modules for processing morphological data in the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../../../docs/features/etl_pipeline.md
  - ../names/README.md
---
# Morphology ETL Modules

This directory contains modules for processing morphological data in the BibleScholarProject.

## Module Structure

- `hebrew_morphology.py` - Processing Hebrew morphology codes and tags
- `greek_morphology.py` - Processing Greek morphology codes and tags
- `morphology_validators.py` - Validation utilities for morphology data
- `morphology_transformers.py` - Transformation utilities for morphology data

## Morphology Processing

Morphology processing includes:

1. Parsing morphology codes from source files
2. Validating code formats and relationships
3. Normalizing codes across different tagging systems
4. Mapping codes to their linguistic meanings
5. Loading processed codes into the database

## Morphology Code Systems

The project supports multiple morphology code systems:

- OSHB (Open Scriptures Hebrew Bible)
- Westminster Hebrew Morphology
- Robinson's Morphological Analysis Codes (Greek)
- STEP Bible Tags

## Usage

Morphology modules are used in the ETL pipeline to process tagged Bible texts and create searchable morphological databases.

## Cross-References
- [ETL Modules](../README.md)
- [ETL Pipeline](../../../docs/features/etl_pipeline.md)
- [Names ETL Modules](../names/README.md) 