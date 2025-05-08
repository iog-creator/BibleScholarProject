---
title: Scripts Directory
description: Utility scripts for data processing, training, and system management
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../docs/guides/system_build_guide.md
  - ../docs/features/etl_pipeline.md
  - ./cursor_rules/README.md
---
# Scripts Directory

This directory contains utility scripts for data processing, training, and system management in the BibleScholarProject.

## Script Categories

### Data Processing
- `process_bible_data.py` - Process raw Bible data into structured formats
- `generate_verse_embeddings.py` - Generate verse embeddings for semantic search
- `verify_data_processing.py` - Verify the integrity of processed data

### Training and Optimization
- `train_dspy_bible_qa.py` - Train DSPy Bible QA models
- `train_semantic_search_models.py` - Train semantic search models
- `run_optimization.py` - Run optimization for DSPy models

### System Management
- `setup_db_security.py` - Set up database security
- `fix_mdc_files.py` - Fix MDC files for cursor rules
- `validate_documentation.py` - Validate documentation files

### Batch Files
- Various `.bat` files for Windows execution of Python scripts

## Subdirectories
- [`cursor_rules/`](cursor_rules/) - Cursor rules management scripts
- [`data/`](data/) - Data processing scripts
- [`logs/`](logs/) - Log files directory
- [`__pycache__/`](__pycache__/) - Python bytecode cache

## Usage
Most scripts can be run directly with Python or via their corresponding batch file. For usage information, run a script with the `-h` flag.

## Cross-References
- [Main Project Documentation](../README.md)
- [System Build Guide](../docs/guides/system_build_guide.md)
- [ETL Pipeline](../docs/features/etl_pipeline.md)
- [Cursor Rules Scripts](./cursor_rules/README.md) 