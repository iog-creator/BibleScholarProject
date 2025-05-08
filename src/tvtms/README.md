---
title: TVTMS Modules
description: Tagged Verse Translation Mapping System modules for the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../../README.md
  - ../../docs/features/bible_translations.md
  - ../etl/README.md
  - ../database/README.md
---
# TVTMS Modules

This directory contains Tagged Verse Translation Mapping System (TVTMS) modules for the BibleScholarProject.

## Overview

The TVTMS is a system for mapping between different Bible translations at the word and verse level, preserving morphological tagging information.

## Module Structure

- `tvtms_parser.py` - Parser for TVTMS mapping files
- `tvtms_validator.py` - Validation utilities for TVTMS mappings
- `tvtms_loader.py` - Database loader for TVTMS mappings
- `tvtms_query.py` - Query utilities for TVTMS mappings

## TVTMS Format

The TVTMS format is a standardized format for mapping between Bible translations, including:

1. Verse-to-verse mappings
2. Word-to-word alignments
3. Morphological tag preservation
4. Strong's number mappings
5. Translation notes and variants

## Usage

TVTMS modules are used to:

1. Parse TVTMS mapping files
2. Validate mapping integrity
3. Load mappings into the database
4. Query mappings for cross-translation search

## Cross-References
- [Main Project Documentation](../../README.md)
- [Bible Translations](../../docs/features/bible_translations.md)
- [ETL Modules](../etl/README.md)
- [Database Modules](../database/README.md) 