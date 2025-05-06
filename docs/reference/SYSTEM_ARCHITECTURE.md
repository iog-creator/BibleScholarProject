# System Architecture Reference

This document provides a comprehensive reference of the BibleScholarProject's system architecture, components, and organization.

## Overview

The BibleScholarProject follows a layered architecture:

1. **Data Layer**: PostgreSQL database containing lexicons, Bible texts, and relationships
2. **ETL Layer**: Python scripts for extracting, transforming, and loading STEPBible data
3. **API Layer**: REST endpoints for accessing the data
4. **Presentation Layer**: Web interface for exploring the data

## Directory Structure

The project is organized into the following directories:

```
BibleScholarProject/
├── config/                 # Configuration files
├── data/                   # Data files
│   ├── processed/          # Processed data
│   └── raw/                # Original data from STEPBible
├── docs/                   # Project documentation
│   ├── features/           # Feature documentation
│   ├── guides/             # How-to guides and tutorials
│   └── reference/          # Reference documentation
├── logs/                   # Log files
├── src/                    # Source code
│   ├── api/                # API endpoints and controllers
│   ├── database/           # Database connection and operations
│   ├── etl/                # ETL scripts for data processing
│   │   ├── morphology/     # Morphology code processing
│   │   └── names/          # Proper names processing
│   ├── tvtms/              # Versification mapping code
│   └── utils/              # Utility functions and helpers
├── templates/              # HTML templates for the web interface
└── tests/                  # Test files
    ├── data/               # Test data files
    ├── integration/        # Integration tests
    └── unit/               # Unit tests
```

## Database Schema

The database schema includes the following key tables:

### Lexicon Tables
- **hebrew_entries**: Hebrew lexicon entries from TBESH
- **greek_entries**: Greek lexicon entries from TBESG
- **word_relationships**: Relationships between words

### Tagged Text Tables
- **verses**: Bible verses with metadata
- **greek_nt_words**: Individual Greek words from the NT
- **hebrew_ot_words**: Individual Hebrew words from the OT

### Morphology Tables
- **hebrew_morphology_codes**: Hebrew morphology code explanations
- **greek_morphology_codes**: Greek morphology code explanations

### Proper Names Tables
- **proper_names**: Biblical proper names
- **proper_name_forms**: Forms of proper names in original languages
- **proper_name_references**: Biblical references for proper names

### Arabic Bible Tables
- **arabic_verses**: Arabic Bible verses
- **arabic_words**: Individual Arabic words with tagging

### Versification Tables
- **versification_mappings**: Maps between different versification traditions

### Semantic Search Tables
- **verse_embeddings**: Vector embeddings for semantic search

For complete database schema details, see [Database Schema](DATABASE_SCHEMA.md).

## ETL Process

The ETL (Extract, Transform, Load) process is handled by scripts in the `src/etl/` directory:

### Key ETL Scripts

1. **etl_lexicons.py**: Processes Hebrew and Greek lexicons
2. **etl_greek_nt.py**: Processes Greek New Testament
3. **etl_hebrew_ot.py**: Processes Hebrew Old Testament
4. **etl_morphology/**: Processes morphology codes
5. **etl_names/etl_proper_names.py**: Processes proper names
6. **etl_arabic_bible.py**: Processes Arabic Bible
7. **tvtms/process_tvtms.py**: Processes versification mappings
8. **fix_hebrew_strongs_ids.py**: Fixes Hebrew Strong's IDs

For detailed ETL process documentation, see [ETL Pipeline](../features/etl_pipeline.md).

## API Endpoints

The API is organized into the following endpoint groups:

### Lexicon API
- Endpoints for accessing Hebrew and Greek lexicon entries

### Bible Text API
- Endpoints for accessing verses and tagged words

### Morphology API
- Endpoints for accessing morphology code explanations

### Proper Names API
- Endpoints for accessing biblical proper names and references

### Semantic Search API
- Endpoints for vector-based semantic search

For complete API documentation, see [API Reference](API_REFERENCE.md).

## Web Interface

The web interface includes the following key pages:

- **Home page**: Search interface and overview
- **Lexicon entry**: Details of a lexicon entry
- **Verse detail**: Verse with tagged words and analysis
- **Morphology detail**: Explanation of morphology codes
- **Proper name detail**: Details of a proper name with references
- **Semantic search**: Interface for semantic search

## Testing Framework

The testing framework includes:

- **Unit tests**: For testing individual components
- **Integration tests**: For testing component interactions
- **Theological term tests**: For validating theological term integrity

For detailed testing documentation, see [Testing Framework](../guides/testing_framework.md).

## Data Verification

The system includes comprehensive data verification:

- **Statistical verification**: Ensures expected counts match actual data
- **Theological term verification**: Tests accurate representation of key theological terms
- **Critical passage verification**: Verifies the integrity of theologically significant passages
- **Linguistic verification**: Ensures proper linguistic representation

For detailed verification documentation, see [Data Verification](../guides/data_verification.md).

## Configuration

The system uses a `.env` file for configuration:

```
DB_HOST=localhost
DB_NAME=bible_db
DB_USER=postgres
DB_PASSWORD=your_password
API_BASE_URL=http://localhost:5000
TVTMS_FILE=data/raw/TVTMS_expanded.txt
SECRET_KEY=your-secret-key-for-flask
```

## Related Documentation

- [ETL Pipeline](../features/etl_pipeline.md)
- [Semantic Search](../features/semantic_search.md)
- [Bible Translations](../features/bible_translations.md)
- [Theological Terms](../features/theological_terms.md)
- [Database Schema](DATABASE_SCHEMA.md)
- [API Reference](API_REFERENCE.md)
- [Testing Framework](../guides/testing_framework.md)
- [Data Verification](../guides/data_verification.md)

## Modification History

| Date | Author | Description |
|------|--------|-------------|
| 2025-06-10 | Documentation Team | Created system architecture reference document | 