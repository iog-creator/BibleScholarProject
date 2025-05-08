---
title: Tagged Bibles
description: Tagged Bible files from STEP Bible Project in the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../../docs/features/bible_translations.md
  - ../../docs/features/etl_pipeline.md
---
# Tagged Bibles

This directory contains tagged Bible files from the STEP Bible Project used in the BibleScholarProject.

## Directory Structure

- `Arabic Bibles/` - Arabic Bible translations with morphological tagging
  - `Translation Tags Individual Books/` - Individual book files with translation tags
- `English Bibles/` - English Bible translations with morphological tagging
- `Greek Bibles/` - Greek Bible text with morphological tagging
- `Hebrew Bibles/` - Hebrew Bible text with morphological tagging

## Tagging Format

The Bible texts are tagged with various linguistic annotations:

1. Strong's numbers for word definitions
2. Morphological tags for grammatical information
3. Translation tags for word alignment across languages
4. Semantic tags for theological concepts

## Using Tagged Bibles

Tagged Bible files are processed by ETL scripts to:

1. Extract linguistic information
2. Build concordances and lexicons
3. Create parallel corpora for translation analysis
4. Generate training data for models

## Data Source

These files are sourced from the STEP Bible Project:
https://github.com/STEPBible/STEPBible-Data

Please refer to their licensing terms for usage restrictions.

## Cross-References
- [Data Directory](../README.md)
- [Bible Translations](../../docs/features/bible_translations.md)
- [ETL Pipeline](../../docs/features/etl_pipeline.md)

See the [Data Directory](../README.md) and the [Documentation Index](../../docs/README.md) for more information. 