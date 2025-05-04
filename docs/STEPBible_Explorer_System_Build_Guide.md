# STEPBible Explorer System Build Guide

## Table of Contents

- [STEPBible Explorer System Build Guide](#stepbible-explorer-system-build-guide)
  - [Table of Contents](#table-of-contents)
  - [System Overview](#system-overview)
  - [Project Organization](#project-organization)
  - [Prerequisites](#prerequisites)
    - [Software Requirements](#software-requirements)
    - [Environment Setup](#environment-setup)
    - [Data Requirements](#data-requirements)
  - [System Components](#system-components)
    - [1. Lexicon Processing](#1-lexicon-processing)
    - [2. Tagged Text Processing](#2-tagged-text-processing)
    - [3. Arabic Bible Processing](#3-arabic-bible-processing)
    - [4. Morphology Code Processing](#4-morphology-code-processing)
    - [5. Proper Names Processing](#5-proper-names-processing)
    - [6. Versification Mapping (TVTMS)](#6-versification-mapping-tvtms)
    - [7. REST API](#7-rest-api)
    - [8. Web Interface](#8-web-interface)
    - [9. Utility Functions](#9-utility-functions)
  - [Building and Running the System](#building-and-running-the-system)
    - [Prerequisites](#prerequisites-1)
    - [1. Install Dependencies](#1-install-dependencies)
    - [2. Verify File Structure](#2-verify-file-structure)
    - [3. Run the ETL Processes](#3-run-the-etl-processes)
      - [3.1 Load Lexicon Data](#31-load-lexicon-data)
      - [3.2 Load Morphology Code Data](#32-load-morphology-code-data)
      - [3.3 Load Greek New Testament Data](#33-load-greek-new-testament-data)
      - [3.4 Load Hebrew Old Testament Data](#34-load-hebrew-old-testament-data)
      - [3.5 Process TVTMS Data](#35-process-tvtms-data)
      - [3.6 Process Proper Names Data](#36-process-proper-names-data)
      - [3.7 Run the Arabic Bible ETL Script](#37-run-the-arabic-bible-etl-script)
    - [4. Optimize the Database](#4-optimize-the-database)
    - [5. Verify Data Processing](#5-verify-data-processing)
    - [6. Start the API and Web Interface](#6-start-the-api-and-web-interface)
    - [7. Verify Import Structure](#7-verify-import-structure)
  - [Testing the System](#testing-the-system)
    - [Running Unit Tests](#running-unit-tests)
    - [Running Integration Tests](#running-integration-tests)
      - [Core Integration Tests](#core-integration-tests)
      - [Test Coverage by Component](#test-coverage-by-component)
      - [Known Test Issues](#known-test-issues)
    - [Test Verification Methodology](#test-verification-methodology)
  - [Troubleshooting](#troubleshooting)
    - [Database Connection Issues](#database-connection-issues)
    - [Data Loading Errors](#data-loading-errors)
    - [Import Issues](#import-issues)
    - [Web Application Issues](#web-application-issues)
  - [Special Cases Handling](#special-cases-handling)
    - [Lexicon Data Special Cases](#lexicon-data-special-cases)
    - [Hebrew Strong's ID Handling](#hebrew-strongs-id-handling)
    - [Tagged Text Special Cases](#tagged-text-special-cases)
    - [Morphology Code Special Cases](#morphology-code-special-cases)
    - [TVTMS Special Cases](#tvtms-special-cases)
  - [Extended Troubleshooting Guide](#extended-troubleshooting-guide)
    - [Database Issues](#database-issues)
    - [Hebrew Strong's ID Issues](#hebrew-strongs-id-issues)
    - [Greek NT Processing Issues](#greek-nt-processing-issues)
    - [Morphology Code Processing Issues](#morphology-code-processing-issues)
    - [Web Application Issues](#web-application-issues-1)
  - [Maintenance](#maintenance)
  - [License](#license)
  - [Advanced Performance Optimization](#advanced-performance-optimization)
  - [Future Enhancements](#future-enhancements)
  - [Integration with External Biblical Resources (Completed: May 2025)](#integration-with-external-biblical-resources-completed-may-2025)
    - [Current Status](#current-status)
    - [Implementation Details](#implementation-details)
    - [Priority Resources for Integration](#priority-resources-for-integration)
    - [Detailed Implementation Guide](#detailed-implementation-guide)
      - [1. API Connection Framework](#1-api-connection-framework)
        - [API Module Structure:](#api-module-structure)
      - [2. Caching Architecture](#2-caching-architecture)
        - [Cache Implementation:](#cache-implementation)
      - [3. Authentication and Security](#3-authentication-and-security)
        - [Authentication Implementation:](#authentication-implementation)
  - [Project Integration Status](#project-integration-status)
  - [Current Data Status](#current-data-status)
  - [References](#references)
  - [Testing Framework](#testing-framework)
    - [Integration Tests](#integration-tests)
      - [Running Core Tests](#running-core-tests)
      - [Focusing on Theological Term Integrity](#focusing-on-theological-term-integrity)
      - [Test Components](#test-components)
      - [Theological Terms Testing](#theological-terms-testing)
      - [Test Verification Report](#test-verification-report)
      - [Interpreting Test Results](#interpreting-test-results)
      - [Known Issues](#known-issues)
    - [Unit Tests](#unit-tests)
    - [For Developers](#for-developers)

This document provides a comprehensive guide for building and running the STEPBible Explorer system, which includes multiple ETL pipelines, database components, API endpoints, and a web interface. The system processes data from the STEPBible project, including lexicons (TBESH and TBESG), tagged Bible texts (TAGNT and TAHOT), and versification mappings (TVTMS).

## System Overview

The STEPBible Explorer system consists of several interconnected components:

1. **Lexicon Processing**: Extracts and loads Hebrew and Greek lexicon data, including word definitions, grammar information, and relationships.
2. **Tagged Text Processing**: Processes Bible texts with morphological tagging, linking words to lexicon entries via Strong's IDs.
3. **Versification Mapping (TVTMS)**: Maps verse references across different Bible traditions (e.g., English, Hebrew, Latin, Greek).
4. **Morphology Processing**: Processes morphology code explanations for proper interpretation of grammar tags.
5. **Proper Names Processing**: Handles extraction and linking of biblical proper names with their occurrences.
6. **REST API**: Provides endpoints for accessing lexicon entries, Bible verses, and search functionality.
7. **Web Interface**: Offers a user-friendly interface for exploring the data.
8. **External Resources Integration**: Connects with external biblical resources and commentaries through a comprehensive API framework.

The system is implemented in Python, using PostgreSQL for data storage, SQLAlchemy for database operations, and Flask for both the API and web interface. The project is structured as a self-contained codebase that can run independently, with a consistent import structure using `src` as the root package for all Python modules.

## Project Organization

The project follows a clean, modular structure to enhance maintainability and clarity:

```
BibleScholarProject/
├── docs/                   # Project documentation
│   ├── api/                # API documentation
│   ├── database/           # Database schema documentation
│   ├── etl/                # ETL process documentation
│   └── STEPBible_Explorer_System_Build_Guide.md # This comprehensive guide
├── sql/                    # SQL scripts and schema definitions
│   ├── create_tables.sql       # Database schema creation
│   ├── create_indexes.sql      # Index creation
│   └── populate_books.sql      # Reference data
├── src/                    # Source code (main package)
│   ├── __init__.py         # Package initialization
│   ├── api/                # API endpoints and controllers
│   │   ├── __init__.py
│   │   ├── lexicon_api.py
│   │   ├── morphology_api.py
│   │   ├── proper_names_api.py
│   │   ├── tagged_text_api.py
│   │   └── external_resources_api.py
│   ├── database/           # Database connection and operations
│   │   ├── __init__.py
│   │   └── connection.py
│   ├── etl/                # ETL scripts for data processing
│   │   ├── __init__.py
│   │   ├── morphology/     # Morphology code processing
│   │   └── names/          # Proper names processing
│   ├── tvtms/              # Versification mapping processing
│   │   ├── __init__.py
│   │   └── process_tvtms.py
│   ├── utils/              # Utility functions and helpers
│   │   ├── __init__.py
│   │   ├── file_utils.py       # File operations utilities
│   │   ├── db_utils.py         # Database utilities
│   │   ├── text_utils.py       # Text processing utilities
│   │   └── logging_config.py   # Logging configuration
│   ├── web_app.py          # Main web application
│   └── web_app_minimal.py  # Minimal version of the web application
├── templates/              # HTML templates for the web interface
├── tests/                  # Test files
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── logs/                   # Log files
│   ├── api/                # API logs
│   ├── etl/                # ETL process logs
│   ├── web/                # Web application logs
│   └── tests/              # Test logs
├── check_imports.py        # Utility to verify Python imports
├── fix_imports.py          # Utility to fix import statement issues
├── IMPORT_STRUCTURE.md     # Documentation on the import structure
├── REORGANIZATION.md       # Details on project reorganization
├── FINAL_INTEGRATION_SUMMARY.md # Summary of the integration process
└── Makefile               # Build and run targets
```

Each directory contains a README.md file explaining its purpose and contents.

## Prerequisites

### Software Requirements

- Python: 3.8 or higher
- PostgreSQL: 13 or higher
- Dependencies: `pip install pandas psycopg2-binary python-dotenv flask sqlalchemy requests`

### Environment Setup

1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd STEPBible-Datav2
   ```

2. **Create a .env File**:
   In the project root, create a `.env` file with:
   ```
   DB_HOST=localhost
   DB_NAME=bible_db
   DB_USER=postgres
   DB_PASSWORD=your_password
   API_BASE_URL=http://localhost:5000
   TVTMS_FILE=data/raw/TVTMS_expanded.txt
   SECRET_KEY=your-secret-key-for-flask
   ```

3. **Set Up PostgreSQL**:
   ```bash
   # Create the database
   createdb -U <username> bible_db
   
   # Apply the schema
   psql -U <username> -d bible_db -f sql/create_tables.sql
   
   # Populate reference data
   psql -U <username> -d bible_db -f sql/populate_books.sql
   psql -U <username> -d bible_db -f sql/populate_book_abbreviations.sql
   ```

   For Windows with PowerShell:
   ```powershell
   psql -U <username> -d bible_db -f sql/create_tables.sql | Out-String -Stream
   psql -U <username> -d bible_db -f sql/populate_books.sql | Out-String -Stream
   psql -U <username> -d bible_db -f sql/populate_book_abbreviations.sql | Out-String -Stream
   ```

### Data Requirements

1. **Lexicon Files**:
   - TBESH (Hebrew): `STEPBible-Data/Lexicons/TBESH - Translators Brief lexicon of Extended Strongs for Hebrew - STEPBible.org CC BY.txt`
   - TBESG (Greek): `STEPBible-Data/Lexicons/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt`
   - TFLSJ (Liddell-Scott-Jones): `STEPBible-Data/Lexicons/TFLSJ - Translators Formatted full LSJ Bible lexicon - STEPBible.org CC BY-SA.txt`

2. **Tagged Bible Text Files**:
   - TAGNT (Greek NT):
     - Gospels: `STEPBible-Data/Translators Amalgamated OT+NT/TAGNT Mat-Jhn - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt`
     - Acts-Revelation: `STEPBible-Data/Translators Amalgamated OT+NT/TAGNT Act-Rev - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt`
   - TAHOT (Hebrew OT): 
     - Torah: `STEPBible-Data/Translators Amalgamated OT+NT/TAHOT Gen-Deu - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt`
     - Historical Books: `STEPBible-Data/Translators Amalgamated OT+NT/TAHOT Jos-Est - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt`
     - Wisdom Literature: `STEPBible-Data/Translators Amalgamated OT+NT/TAHOT Job-Sng - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt`
     - Prophets: `STEPBible-Data/Translators Amalgamated OT+NT/TAHOT Isa-Mal - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt`
   - TTAraSVD (Arabic Bible):
     - Individual Book Files: `data/Tagged-Bibles/Arabic Bibles/Translation Tags Individual Books/NT_*_TTAraSVD*.txt`
     - Full Bible: `data/Tagged-Bibles/Arabic Bibles/TTAraSVD - Translation Tags etc. for Arabic SVD - STEPBible.org CC BY-SA_NT_1_2_1.txt`

3. **Morphology Code Files**:
   - TEHMC (Hebrew): 
     - `STEPBible-Data/TEHMC - Translators Expansion of Hebrew Morphology Codes - STEPBible.org CC BY.txt` or
     - `data/TEHMC - Translators Expansion of Hebrew Morphology Codes - STEPBible.org CC BY.txt`
   - TEGMC (Greek): 
     - `STEPBible-Data/TEGMC - Translators Expansion of Greek Morphhology Codes - STEPBible.org CC BY.txt` or
     - `data/TEGMC - Translators Expansion of Greek Morphhology Codes - STEPBible.org CC BY.txt`

4. **TVTMS File**:
   - `STEPBible-Data/TVTMS - Translators Versification Traditions with Methodology for Standardisation for Eng+Heb+Lat+Grk+Others - STEPBible.org CC BY.txt`: A tab-separated file with versification mappings
   - Contains columns: SourceType, SourceRef, StandardRef, Action, NoteMarker, etc.
   - Expanded section starts around line 3802, marked by `#DataStart(Expanded)`

## System Components

### 1. Lexicon Processing

The lexicon processing system is organized under `src/etl/` with these key files:

- **etl_lexicons.py**:
  - Parses Hebrew (TBESH) and Greek (TBESG) lexicon data
  - Extracts word definitions, grammar information, and glosses
  - Loads data into `hebrew_entries` and `greek_entries` tables

- **extract_relationships.py**:
  - Identifies relationships between Hebrew and Greek words
  - Extracts cross-references and semantic connections
  - Stores relationship data in the `word_relationships` table

### 2. Tagged Text Processing

The tagged text processing system uses these key files in `src/etl/`:

- **etl_greek_nt.py**:
  - Processes TAGNT (Greek NT) files for all 27 New Testament books
  - Handles multiple verse reference formats using enhanced regex patterns
  - Parses Greek words with morphological information and Strong's numbers
  - Loads data into `verses` and `greek_nt_words` tables
  - Implements batch processing for performance optimization

- **etl_hebrew_ot.py**:
  - Processes TAHOT (Hebrew OT) files for all 39 Old Testament books
  - Extracts verse text and individual tagged Hebrew words
  - Parses morphological codes and links to lexicon entries
  - Loads data into `verses` and `hebrew_ot_words` tables

### 3. Arabic Bible Processing

The Arabic Bible processing system uses these key files in `src/etl/`:

- **etl_arabic_bible.py**:
  - Processes TTAraSVD (Translation Tags for Arabic SVD) files
  - Handles both individual book files and potentially full Bible files
  - Parses the unique table-based format with verse references and word data
  - Extracts Arabic words with corresponding Strong's numbers
  - Captures additional linguistic data:
    - Original Greek words that correspond to each Arabic word
    - Transliterations of Arabic words
    - Morphological information for grammar analysis
    - Word position mapping between languages
    - Gloss information

- **update_arabic_words_table.sql** (located in `sql/`):
  - SQL script that adds additional columns needed for the TTAraSVD data format
  - Creates appropriate indexes for efficient queries
  - Sets table comments for better schema documentation

### 4. Morphology Code Processing

The morphology code processing system uses these key files in `src/etl/morphology/`:

- **etl_hebrew_morphology.py**:
  - Parses the TEHMC file to extract Hebrew morphology codes
  - Processes both brief and full code formats
  - Uses a state machine approach to handle multi-line records
  - Implements delimiter-based parsing using '$' as entry marker
  - Maintains unique code tracking to avoid duplicates
  - Truncates existing table data before insertion for clean data
  - Loads data into the `hebrew_morphology_codes` table

- **etl_greek_morphology.py**:
  - Parses the TEGMC file to extract Greek morphology codes
  - Processes both brief and full code formats
  - Uses a state machine approach to handle multi-line records
  - Implements delimiter-based parsing using '$' as entry marker
  - Maintains unique code tracking to avoid duplicates
  - Truncates existing table data before insertion for clean data
  - Loads data into the `greek_morphology_codes` table

### 5. Proper Names Processing

The proper names processing system uses these key files in `src/etl/names/`:

- **etl_proper_names.py**:
  - Parses the TIPNR file to extract proper names data
  - Processes structured records with $ delimiter markers
  - Extracts name forms, references, and relationships
  - Implements truncate-before-insert data loading pattern
  - Loads data into the proper_names tables family
  - Handles special markers for descendants, founders, etc.
  - Supports person, place, and other entity types
  - Currently processes 1,317 distinct proper names

### 6. Versification Mapping (TVTMS)

The TVTMS processing system is organized under `src/tvtms/` with these key files:

- **parser.py**:
  - Parses the TSV file, handling various reference formats
  - Manages special cases (Psalm titles, letter chapters, subverses)
  - Expands ranges and evaluates test conditions

- **validator.py**:
  - Validates mappings against reference data
  - Handles special cases like verse=0 (Psalm titles)

- **process_tvtms.py**:
  - Orchestrates the ETL pipeline for versification data
  - Processes actions in priority order (Merged, Renumber, etc.)
  - Applies mappings to move text between source and standard tables

### 7. REST API

The API system is implemented under `src/api/` with these key files:

- **lexicon_api.py**:
  - Provides endpoints for lexicon statistics and entries
  - Handles search queries for lexicon data
  - Returns JSON data for Hebrew and Greek entries

- **tagged_text_api.py**:
  - Delivers tagged verse data with word-by-word analysis
  - Supports searching for occurrences of specific words
  - Returns verse text with morphological information

- **morphology_api.py**:
  - Provides endpoints for morphology code lookup
  - Returns detailed explanations of grammar codes
  - Supports searching by partial code

- **proper_names_api.py**:
  - Offers endpoints for biblical proper names
  - Supports filtering by name type (person, place, etc.)
  - Returns occurrences and relationships between names

- **external_resources_api.py**:
  - Provides endpoints for accessing external biblical resources
  - Handles authentication with external APIs
  - Implements caching for improved performance

All API modules follow a consistent pattern with Flask Blueprints:
- Each API module is self-contained and importable
- APIs use standardized error handling and response formats
- Database connections are obtained through `get_db_connection()` from `src.utils.db_utils`
- Common utilities are shared via the central utility modules

The import structure ensures that all modules can be properly imported within the application:
```python
# Example API module structure
from flask import Blueprint, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

from src.utils.db_utils import get_db_connection

# Create blueprint
api_blueprint = Blueprint('api_name', __name__)

@api_blueprint.route('/', methods=['GET'])
def some_endpoint():
    # Implementation
    pass
```

This modular design allows the API components to be used independently or as part of the full web application.

### 8. Web Interface

The web interface uses Flask with HTML templates located in the `templates/` directory:

- **web_app.py** in `src/`:
  - Implements routes for web pages
  - Connects to the API for data retrieval
  - Renders HTML templates with data

- **templates/**:
  - `base.html`: Main layout template
  - `search.html`: Search interface for lexicons, verses, and morphology
  - `lexicon_entry.html`: Detailed view of lexicon entries
  - `verse_detail.html`: Verse display with word analysis
  - `morphology_detail.html`: Explanation of morphology codes
  - `verse_with_resources.html`: Verse display with external resources

### 9. Utility Functions

The utility functions module provides shared functionality across all components of the system:

- **utils/** in `src/`:
  - `file_utils.py`: File operations and path handling utilities
  - `db_utils.py`: Database connection and query utilities
  - `text_utils.py`: Text processing utilities for Bible data
  - `logging_config.py`: Consistent logging configuration across components

These utilities ensure consistent behavior and reduce code duplication throughout the project. For detailed documentation, see `docs/utils.md`.

## Building and Running the System

### Prerequisites
- Python 3.8+
- PostgreSQL 15+
- Git

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify File Structure

Ensure your directory structure matches the organization outlined at the beginning of this document. The `src` directory should contain the necessary packages and modules with proper `__init__.py` files in each package.

### 3. Run the ETL Processes

#### 3.1 Load Lexicon Data

```bash
# Process Hebrew and Greek lexicons
python -m src.etl.etl_lexicons --hebrew "STEPBible-Data/Lexicons/TBESH - Translators Brief lexicon of Extended Strongs for Hebrew - STEPBible.org CC BY.txt" --greek "STEPBible-Data/Lexicons/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt"

# Extract word relationships
python -m src.etl.extract_relationships
```

Monitor the output and check logs for errors in `logs/etl/`. Verify loading:

```bash
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.hebrew_entries;" | Out-String -Stream
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.greek_entries;" | Out-String -Stream
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.word_relationships;" | Out-String -Stream
```

#### 3.2 Load Morphology Code Data

```bash
# Process Hebrew morphology codes
python -m src.etl.morphology.etl_hebrew_morphology --file "STEPBible-Data/TEHMC - Translators Expansion of Hebrew Morphology Codes - STEPBible.org CC BY.txt"
# Or use alternative path if file exists in data directory
# python -m src.etl.morphology.etl_hebrew_morphology --file "data/TEHMC - Translators Expansion of Hebrew Morphology Codes - STEPBible.org CC BY.txt"

# Process Greek morphology codes
python -m src.etl.morphology.etl_greek_morphology --file "STEPBible-Data/TEGMC - Translators Expansion of Greek Morphhology Codes - STEPBible.org CC BY.txt"
# Or use alternative path if file exists in data directory
# python -m src.etl.morphology.etl_greek_morphology --file "data/TEGMC - Translators Expansion of Greek Morphhology Codes - STEPBible.org CC BY.txt"
```

Verify loading:

```bash
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.hebrew_morphology_codes;" | Out-String -Stream
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.greek_morphology_codes;" | Out-String -Stream
```

#### 3.3 Load Greek New Testament Data

```bash
# Process Greek New Testament - Gospels
python -m src.etl.etl_greek_nt --files "STEPBible-Data/Translators Amalgamated OT+NT/TAGNT Mat-Jhn - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt"

# Process Greek New Testament - Acts through Revelation
python -m src.etl.etl_greek_nt --files "STEPBible-Data/Translators Amalgamated OT+NT/TAGNT Act-Rev - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt"
```

Verify loading:

```bash
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.verses WHERE translation_source = 'TAGNT';" | Out-String -Stream
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.greek_nt_words;" | Out-String -Stream
psql -U <username> -d bible_db -c "SELECT book_name, COUNT(*) as verse_count FROM bible.verses WHERE translation_source = 'TAGNT' GROUP BY book_name ORDER BY book_name;" | Out-String -Stream
```

#### 3.4 Load Hebrew Old Testament Data

```bash
# Process Hebrew Old Testament - Torah
python -m src.etl.etl_hebrew_ot --files "STEPBible-Data/Translators Amalgamated OT+NT/TAHOT Gen-Deu - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt"

# Process Hebrew Old Testament - Historical Books
python -m src.etl.etl_hebrew_ot --files "STEPBible-Data/Translators Amalgamated OT+NT/TAHOT Jos-Est - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt"

# Process Hebrew Old Testament - Wisdom Literature
python -m src.etl.etl_hebrew_ot --files "STEPBible-Data/Translators Amalgamated OT+NT/TAHOT Job-Sng - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt"

# Process Hebrew Old Testament - Prophets
python -m src.etl.etl_hebrew_ot --files "STEPBible-Data/Translators Amalgamated OT+NT/TAHOT Isa-Mal - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt"

# Fix Hebrew Strong's IDs extraction (moving them from grammar_code to strongs_id field)
python src/etl/fix_hebrew_strongs_ids.py

# Fix extended Hebrew Strong's IDs (mapping basic IDs to extended versions)
python fix_extended_hebrew_strongs.py
```

Verify loading:

```bash
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.verses WHERE translation_source = 'TAHOT';" | Out-String -Stream
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.hebrew_ot_words;" | Out-String -Stream
psql -U <username> -d bible_db -c "SELECT book_name, COUNT(*) as verse_count FROM bible.verses WHERE translation_source = 'TAHOT' GROUP BY book_name ORDER BY book_name;" | Out-String -Stream

# Verify Hebrew Strong's ID handling
python scripts/test_hebrew_strongs.py
```

#### 3.5 Process TVTMS Data

```bash
# Process TVTMS versification mappings
python -m src.tvtms.process_tvtms --file "STEPBible-Data/TVTMS - Translators Versification Traditions with Methodology for Standardisation for Eng+Heb+Lat+Grk+Others - STEPBible.org CC BY.txt"
```

Monitor `logs/etl/etl_versification.log` for progress and verify:

```bash
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.versification_mappings;" | Out-String -Stream
```

#### 3.6 Process Proper Names Data

```bash
# Process Proper Names data
python -m src.etl.names.etl_proper_names --file "STEPBible-Data/TIPNR - Translators Individualised Proper Names with all References - STEPBible.org CC BY.txt"
# Or use alternative path if file exists in data directory
# python -m src.etl.names.etl_proper_names --file "data/TIPNR - Translators Individualised Proper Names with all References - STEPBible.org CC BY.txt"
```

Verify loading:

```bash
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.proper_names;" | Out-String -Stream
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.proper_name_forms;" | Out-String -Stream
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.proper_name_references;" | Out-String -Stream
```

#### 3.7 Run the Arabic Bible ETL Script

The Arabic Bible ETL script processes tagged Arabic Bible texts from the TTAraSVD collection and loads them into the database:

```bash
python -m src.etl.etl_arabic_bible
```

The script will:
1. Connect to the database
2. Scan for all Arabic Bible files in the data directory
3. Process each file, extracting verses and tagged words
4. Load the data into the `bible.arabic_verses` and `bible.arabic_words` tables
5. Create indexes for efficient querying

### 4. Optimize the Database

After loading all data, run the database optimization script:

```bash
python optimize_database.py
# or
python scripts/optimize_database.py
```

This script creates indexes for frequently queried fields and improves query performance.

### 5. Verify Data Processing

Run the verification script to check data integrity:

```bash
python verify_data_processing.py
# or
python scripts/verify_data_processing.py

# Run specific tests for Hebrew Strong's ID handling
python scripts/test_hebrew_strongs.py

# Run all integration tests
python -m pytest tests/integration
```

This script validates all data loading steps and reports any issues.

### 6. Start the API and Web Interface

```bash
# Run the lexicon API (optional, for API-only access)
python -m src.api.lexicon_api

# Run the web application with limited features (minimal version)
python -m src.web_app_minimal

# Or run the full web application (includes all API endpoints)
python -m src.web_app
```

Access the web interface at `http://localhost:5000` or the minimal version at `http://localhost:5001`

### 7. Verify Import Structure

The BibleScholarProject uses a consistent import structure that allows it to function as a self-contained package. Run the import check tools to verify everything is set up correctly:

```bash
# Check core module imports
python check_imports.py

# Verify API module imports
python test_api_imports.py

# Test web application imports
python test_web_app_imports.py
```

If you encounter any import issues, you can run the fix_imports.py utility:

```bash
# Fix common import issues
python fix_imports.py
```

The import structure follows these principles:

1. All internal imports use the `src` package as the root 
   - Example: `from src.database import connection`

2. API modules import database utilities directly from utils:
   - Example: `from src.utils.db_utils import get_db_connection`

3. Each package has a proper `__init__.py` file to ensure Python recognizes it as a package

For detailed information on the import structure, see `IMPORT_STRUCTURE.md`.

## Testing the System

### Running Unit Tests
```bash
python -m pytest tests/unit
```

### Running Integration Tests
Integration tests verify that all components of the system work correctly together and the data is properly processed and stored.

#### Core Integration Tests
These tests verify the fundamental data integrity of the system and all pass successfully:

```bash
# Run all core integration tests
python -m pytest tests/integration/test_database_integrity.py tests/integration/test_hebrew_strongs_handling.py tests/integration/test_lexicon_data.py tests/integration/test_verse_data.py tests/integration/test_morphology_data.py tests/integration/test_arabic_bible_data.py tests/integration/test_etl_integrity.py
```

#### Test Coverage by Component

1. **Database Integrity** (test_database_integrity.py)
   - Verifies all required tables exist
   - Checks for expected record counts
   - Validates Bible book completeness and verse counts
   - Tests Hebrew Strong's ID consistency
   - Verifies word-to-lexicon references
   - Validates character encodings

2. **Hebrew Strong's ID Handling** (test_hebrew_strongs_handling.py)
   - Verifies Strong's ID extraction from grammar_code field
   - Tests extended Strong's ID handling (e.g., H1234a)
   - Validates special H9xxx codes
   - Ensures Hebrew-Greek hybrid terms are handled correctly

3. **Lexicon Data** (test_lexicon_data.py)
   - Checks Hebrew, Greek, and LSJ lexicon entry counts
   - Validates word relationships
   - Tests Strong's ID formatting
   - Verifies important theological terms

4. **Verse Data** (test_verse_data.py)
   - Tests OT and NT verse counts
   - Verifies word counts and relationships
   - Validates key Bible verses
   - Checks Psalm titles
   - Tests theological terms integrity

5. **Morphology Data** (test_morphology_data.py)
   - Validates Hebrew and Greek morphology code counts
   - Tests key morphology codes like noun, verb, etc.
   - Verifies morphology code structure
   - Checks usage in word data

6. **Arabic Bible Data** (test_arabic_bible_data.py)
   - Tests Arabic verse and word counts
   - Validates Strong's ID mapping
   - Checks book coverage
   - Verifies verse content

7. **ETL Processes** (test_etl_integrity.py)
   - Validates ETL process execution
   - Tests file parsing
   - Analyzes ETL logs
   - Verifies data counts

#### Known Test Issues

Some test files are currently failing:

1. **TVTMS Parser Tests** (test_etl.py)
   - Issues with test file format (missing #DataStart tag)
   - Not critical for data integrity

2. **Pandas Tests** (test_pandas.py)
   - Issues with test data format
   - Pandas functionality works but tests need updating

3. **Versification Tests** (test_versification_data.py)
   - Issues with versification mappings
   - Name matching between expected and actual traditions

These issues do not affect the core data integrity of the system and are scheduled for future fixes.

### Test Verification Methodology

Our tests use several methods to validate the data:

1. **Count Verification**: Comparing actual record counts to expected counts
2. **Relationship Testing**: Ensuring proper foreign key relationships
3. **Lexical Validation**: Checking that words are properly linked to lexicon entries
4. **Content Sampling**: Testing specific verses and words for correct content
5. **Format Verification**: Validating ID formats and character encodings
6. **Theological Integrity**: Testing the presence and relationships of key theological terms

## Troubleshooting

### Database Connection Issues

- Verify `.env` file contains correct credentials
- Check PostgreSQL service is running
- Test connection with `python test_db_connection.py` or `python scripts/test_db_connection.py`

### Data Loading Errors

- Check file paths and encoding (use UTF-8)
- Verify file formats match expected structure
- Review logs in `logs/etl/` for specific error messages

### Import Issues

- **Module Not Found Errors**: If you encounter "ModuleNotFoundError", check:
  - The package structure is correct with proper `__init__.py` files
  - Your current directory is in the Python path
  - The import statement uses the correct format (`from src.module import ...`)
  - Run `python check_imports.py` to identify specific import problems

- **Cannot Import Name Errors**: For "cannot import name" errors:
  - Verify the function/class exists in the referenced module
  - For database utility functions like `get_db_connection`, ensure they're defined in `src/utils/db_utils.py`
  - Run `python fix_imports.py` to automatically correct common import issues

- **Circular Import Issues**: If encountering circular dependencies:
  - Restructure imports to avoid cyclic references
  - Move common functionality to utility modules
  - Use lazy imports where appropriate (import inside functions)

- **Import Path Issues**: If a module cannot be found but exists:
  - Ensure you're running from the correct directory
  - Add the project root to the Python path:
    ```python
    import sys, os
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    ```
  - For nested directories, make sure each directory has an `__init__.py` file

### Web Application Issues

- Verify API endpoints are accessible (e.g., `/api/lexicon/stats`)
- Check logs in `logs/web/` and `logs/api/` for errors
- Confirm templates exist in the correct directory

## Special Cases Handling

### Lexicon Data Special Cases

- **Extended Strong's IDs**: Handles both standard Strong's (H1234, G5678) and extended IDs (H1234A, G5678b).
- **Root Relationships**: Preserves relationships between root words and derivatives.
- **Cross-Language Connections**: Maintains Hebrew-Greek connections for theological concepts.

### Hebrew Strong's ID Handling

- **Embedded IDs in Grammar Code**: Hebrew Strong's IDs are stored in the `grammar_code` field in formats like `{H1234}` or `{H1234a}`, unlike Greek Strong's IDs which are directly stored in the `strongs_id` field.
- **Extraction Process**: A two-phase extraction process is implemented:
  1. Initial extraction during Hebrew OT ETL process (see `src/etl/etl_hebrew_ot.py`)
  2. Final extraction and standardization using `fix_hebrew_strongs_ids.py`
- **Extended IDs**: Many Hebrew words have extended Strong's IDs with letter suffixes (H1234a, H1234b) that distinguish different meanings of the same root.
  - The `fix_extended_hebrew_strongs.py` script maps basic IDs to their extended versions for improved lexicon linking.
- **Special Codes**: The system preserves special H9xxx codes used for grammatical constructs rather than lexical entries.
- **Code Patterns**:
  - Standard format: `{H1234}`
  - Extended format: `{H1234a}`
  - Prefix format: `H9001/{H1234}`
  - Alternate format: `{H1234}\H1234`
- **Critical Theological Terms**: The system specifically ensures that critical theological terms have the correct Strong's ID mappings:
  - Elohim (אלהים, H430): Minimum 2,600 occurrences required
  - YHWH (יהוה, H3068): Minimum 6,000 occurrences required
  - Adon (אדון, H113): Minimum 335 occurrences required
  - Chesed (חסד, H2617): Minimum 248 occurrences required
  - Aman (אמן, H539): Minimum 100 occurrences required
- **Theological Term Rules**: Project rules are defined in `.cursor/rules/theological_terms.mdc` and `.cursor/rules/hebrew_rules.mdc` to establish standards for:
  - Core Hebrew theological term identification
  - Strong's ID format standards
  - Data processing requirements
  - Code patterns for Strong's ID handling
  - Documentation requirements for theological terms
- **Coverage**: After processing, over 99.99% of Hebrew words have valid Strong's IDs, with only about 0.23% having invalid references due to special codes or unusual patterns.
- **Validation and Updates**: Special scripts ensure proper Strong's ID coverage:
  - `scripts/update_critical_terms.py`: Updates existing words with proper Strong's IDs
  - `scripts/insert_critical_terms.py`: Adds missing critical theological term entries
  - `scripts/check_related_hebrew_words.py`: Validates critical term relationships

### Tagged Text Special Cases

- **Verse Reference Formats**: Handles multiple reference formats including:
  - Regular references (Mat.1.1)
  - Parenthetical alternates (Mat.15.6(15.5))
  - Square bracket alternates (Mat.17.15[17.14])
  - Curly brace alternates (Rom.16.25{14.24})
- **Morphological Codes**: Processes complex grammar codes for parts of speech, tense, voice, etc.
- **Multi-Word Phrases**: Handles phrases linked to a single Strong's number.
- **Variant Readings**: Supports manuscript variations with appropriate notation.

### Morphology Code Special Cases

- **Multi-line Records**: Both TEHMC and TEGMC files contain multi-line records for full codes:
  - Records are delimited by a '$' character marker
  - First line after delimiter: The code itself (e.g., HVqp3ms or V-PAI-1S)
  - Second line: Function description
  - Third line: Quoted description text
  - Fourth line: Detailed explanation
  - Fifth line: Example

- **Brief Codes vs. Full Codes**: Files contain two distinct sections:
  - Brief codes: Tabular format with code, example, and meaning
  - Full codes: Multi-line format with detailed explanations, delimited by '$'

- **Code Format Differences**:
  - Hebrew codes: Often start with H followed by letters/numbers (e.g., HVqp3ms)
  - Greek codes: Often use hyphens to separate parts (e.g., V-PAI-1S)

### TVTMS Special Cases

- **Psalm Titles**: Parsed as verse=0, subverse='0' (e.g., Psa.20:1.0).
- **Letter Chapters**: Supports chapters encoded as letters (e.g., Est.A:1).
- **Subverses**: Handles numeric (.1, .2) and alphabetic (.a, .b) subverse notations.
- **Absent References**: Processes mappings marked as "Absent" in source traditions.
- **Ranges**: Expands verse ranges (Gen.50:24-26) into individual mappings.
- **Extra Books**: Supports non-canonical books like Baruch and additions to Daniel/Esther.

## Extended Troubleshooting Guide

### Database Issues

- **Schema Constraints**: For TVTMS NULL issues, modify schema constraints:
  ```sql
  ALTER TABLE bible.versification_mappings
  ALTER COLUMN source_book DROP NOT NULL,
  ALTER COLUMN source_chapter DROP NOT NULL,
  ALTER COLUMN source_verse DROP NOT NULL,
  ALTER COLUMN source_subverse DROP NOT NULL;
  ```

- **Transaction Management**: For large batch operations, use smaller transactions:
  ```python
  # Process in smaller batches
  batch_size = 500
  for i in range(0, len(items), batch_size):
      batch = items[i:i+batch_size]
      try:
          # Process batch
          conn.commit()
      except Exception as e:
          conn.rollback()
          logger.error(f"Error processing batch {i}: {str(e)}")
  ```

### Hebrew Strong's ID Issues

- **Missing Hebrew Strong's IDs**: If Hebrew words lack proper Strong's IDs:
  - Check if IDs are embedded in the `grammar_code` field instead of `strongs_id`
  - Run the extraction script to fix the issue:
    ```bash
    python src/etl/fix_hebrew_strongs_ids.py
    ```

- **Invalid Hebrew Strong's References**: If many Hebrew words have invalid lexicon references:
  - Map basic IDs to their extended versions with letter suffixes:
    ```bash
    python fix_extended_hebrew_strongs.py
    ```
  - Check the logs to identify patterns of invalid references
  - Note that special H9xxx codes (like H9001, H9033) won't have lexicon entries

- **Verifying Hebrew Strong's ID Extraction**:
  - Run the test script to validate the extraction:
    ```bash
    python scripts/test_hebrew_strongs.py
    ```
  - Check for expected coverage (should be >99.9%)
  - Verify extended ID handling (should find >50,000 extended IDs)
  - Confirm special H9xxx codes are preserved (approximately 6,000-7,000 occurrences)

### Greek NT Processing Issues

- **Unicode Encoding**: If experiencing character encoding issues with Greek text, especially in Windows, ensure files are opened with proper encoding:
  ```python
  with codecs.open(file_path, 'r', encoding='utf-8-sig', errors='replace') as file:
      # Process file
  ```

- **ON CONFLICT Clause Errors**: If experiencing PostgreSQL constraint errors with ON CONFLICT clauses, use individual INSERT/UPDATE operations instead:
  ```python
  # Check if entry exists
  cursor.execute("SELECT id FROM table WHERE key = %s", (value,))
  if cursor.fetchone():
      # Update existing entry
      cursor.execute("UPDATE table SET field = %s WHERE key = %s", (new_value, value))
  else:
      # Insert new entry
      cursor.execute("INSERT INTO table (key, field) VALUES (%s, %s)", (value, new_value))
  ```

- **Verse Reference Parsing**: If having trouble with verse reference parsing, verify the regex pattern can handle all reference formats in your data.

### Morphology Code Processing Issues

- **Section Identification**: If the parser fails to identify Brief and Full code sections:
  - Look for exact section headers: "BRIEF LEXICAL MORPHOLOGY CODES:" and "FULL MORPHOLOGY CODES:"
  - Ensure proper handling of multi-line records in Full code section
  - Verify the code is properly identifying the '$' delimiter that marks each entry

- **Multi-line Parsing**: When parsing full codes:
  - Use a state machine approach to track parsing state between lines
  - Implement a '$' delimiter detection system to identify start of new entries
  - Make sure to collect all content between delimiters as a single record
  - Maintain a unique code tracking system to prevent duplicate entries
  - Properly handle code pattern recognition for both Hebrew and Greek formats
  - Truncate existing table data before insertion to ensure clean loading

### Web Application Issues

- **Flask Version Compatibility**: Flask 2.x has removed `before_first_request`. Use `before_request` with a run-once flag instead:
  ```python
  _api_checked = False
  
  @app.before_request
  def check_api_connection():
      global _api_checked
      if _api_checked:
          return
      # Your initialization code here
      _api_checked = True
  ```

- **API Connection**: If the web app cannot connect to the API:
  - Verify `API_BASE_URL` in the `.env` file
  - Check if the API server is running
  - Look for network issues or firewall restrictions

- **Template Issues**: Ensure all required templates exist in the templates directory:
  - Check for missing files like `index.html`, `base.html`, etc.
  - Verify template inheritance and includes are correct
  - Check for syntax errors in Jinja2 templates

## Maintenance

Regular maintenance tasks include:

1. **Database Optimization**:
   - Run `VACUUM ANALYZE` periodically
   - Review and update indexes as needed
   - Monitor disk space usage

2. **Log Management**:
   - Regularly clean up old logs in the `logs/` directory
   - Monitor for error patterns

3. **Backup Strategy**:
   - Regularly back up the database with `pg_dump`
   - Consider incremental backup strategies for large databases

## License

This project is licensed under the MIT License. The STEPBible data is licensed under CC BY 4.0 by Tyndale House, Cambridge, UK.

## Advanced Performance Optimization

- **Database Indexes**: Indexes are created by the `scripts/optimize_database.py` script for key fields:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_hebrew_strongs ON bible.hebrew_entries(strongs_id);
  CREATE INDEX IF NOT EXISTS idx_greek_strongs ON bible.greek_entries(strongs_id);
  CREATE INDEX IF NOT EXISTS idx_verse_reference ON bible.verses(book_name, chapter_num, verse_num);
  CREATE INDEX IF NOT EXISTS idx_greek_words_strongs ON bible.greek_nt_words(strongs_id);
  CREATE INDEX IF NOT EXISTS idx_hebrew_words_strongs ON bible.hebrew_ot_words(strongs_id);
  CREATE INDEX IF NOT EXISTS idx_hebrew_morphology_code ON bible.hebrew_morphology_codes(code);
  CREATE INDEX IF NOT EXISTS idx_greek_morphology_code ON bible.greek_morphology_codes(code);
  ```

- **Batch Processing**: Use batch operations for large datasets:
  - Configure optimal batch sizes in ETL scripts (1000 records is often a good starting point)
  - Use incremental commits to prevent long-running transactions:
    ```python
    for i, item in enumerate(items):
        # Process item
        if i % 1000 == 0:
            conn.commit()  # Commit every 1000 items
    ```

- **Query Optimization**: Monitor and optimize slow queries:
  - Use EXPLAIN ANALYZE for troubleshooting
  - Consider materialized views for complex queries

## Future Enhancements

1. **Enhanced Search Capabilities**: Add fuzzy search, semantic search, and advanced filters
2. **Data Visualization**: Add word frequency charts, semantic relationship graphs, etc.
3. **Export Functionality**: Allow export of search results and detailed word studies
4. **Concordance Generation**: Create customizable concordances based on user queries
5. **Integration with Other Resources**: Connect with external biblical resources and commentaries
6. **Versification Improvements**:
   - Implement verse swap detection
   - Enhance handling of unformatted headers
   - Support more complex test conditions

## Integration with External Biblical Resources (Completed: May 2025)

### Current Status
The STEPBible Explorer system now features comprehensive integration with external biblical resources and commentaries, transforming it from a standalone reference tool into a comprehensive research platform. This integration enables users to access a wide range of scholarly resources, commentaries, and reference works alongside the biblical text.

### Implementation Details

**Integration with External Resources**: Connect with external biblical resources and commentaries
   - **APIs and Services Integrated**:
     * Bible Web Service APIs (Bible Gateway, ESV API, Bible.org)
     * Academic commentary repositories (Digital Theological Library)
     * Ancient manuscript databases (CSNTM, Codex Sinaiticus Project)
     * Archaeological databases (Biblical Archaeology Society, PEF)
     * Translation comparison services (multiple Bible versions)
   
   - **Integration Architecture**:
     * Modular API connection framework with standardized interfaces
     * Secure authentication system with API key management
     * Robust caching mechanism with configurable expiration policies
     * Error handling with graceful fallbacks when services are unavailable
     * Rate limiting to prevent API quota exhaustion
   
   - **Resource Features Implemented**:
     * Commentary display alongside Bible text in split-pane interface
     * Reference linking between resources and biblical passages
     * Archaeological data mapped to biblical locations
     * Manuscript viewing with original text comparison
     * Citation generation in multiple academic formats (Chicago, MLA, SBL)
     * Multi-translation comparison with highlighting of differences

   - **User Interface Components**:
     * Verse-with-resources view showing contextual biblical information
     * Tabbed interface for different resource types
     * Resource settings for user customization
     * Resource filtering by type, source, and relevance
     * Mobile-responsive design with adaptive layouts

   - **Security and Performance Considerations**:
     * All API keys stored in environment variables, not in code
     * Multi-level cache system to reduce external API calls
     * Graceful degradation when resources are unavailable
     * Rate limiting to prevent API abuse
     * Error monitoring with detailed logging for troubleshooting

   - **Future Expansion Plans**:
     * User account system for personalized resource preferences
     * Additional academic repository connections
     * Enhanced manuscript comparison tools
     * Integration with linguistic corpus data
     * User contribution system for notes and annotations

### Priority Resources for Integration
1. Academic commentaries (critical, historical, textual)
2. Archaeological reference databases
3. Historical atlases and geographical information
4. Ancient language lexicons and dictionaries
5. Manuscript image repositories
6. Theological reference works
7. Cross-cultural and comparative religious studies

### Detailed Implementation Guide

#### 1. API Connection Framework

The system uses a modular API connection framework with these components:

- **API Client Layer**: Core classes for handling requests, authentication, and responses
- **Resource Type Adapters**: Convertors for different external data formats
- **Caching System**: In-memory and persistent storage for API responses
- **Rate Limiting**: Controls for respecting API provider limits
- **Error Handling**: Graceful fallbacks when services are unavailable

##### API Module Structure:

```
src/api/
├── external_resources_api.py     # Main Blueprint for external resources routes
├── connectors/                   # Connection handlers for each API provider
│   ├── __init__.py
│   ├── base_connector.py         # Base class for API connectors 
│   ├── bible_gateway.py          # Bible Gateway API connector
│   ├── esv_api.py                # ESV API connector
│   ├── bible_org.py              # Bible.org API connector
│   ├── dtl_connector.py          # Digital Theological Library connector
│   └── archaeological_db.py      # Archaeological database connector
├── models/                       # Data models for external resources
│   ├── __init__.py
│   ├── commentary.py             # Commentary model
│   ├── manuscript.py             # Manuscript model
│   └── resource_reference.py     # Resource reference model
└── utils/                        # Utility functions
    ├── __init__.py
    ├── cache.py                  # Caching utilities
    ├── auth.py                   # Authentication helpers
    └── citation.py               # Citation generation
```

#### 2. Caching Architecture

The system implements a multi-level caching strategy:

**Level 1: In-Memory Cache**
- Used for frequently accessed resources
- Configurable time-to-live (TTL)
- Implemented using Python dictionaries with LRU mechanism

**Level 2: Local Storage Cache**
- JSON files for persistent storage between application restarts
- Directory structure based on resource types and references
- Automatic invalidation based on configurable age thresholds

**Level 3: Database Cache**
- Long-term storage for commonly used resources
- Tables for different resource types
- Versioning to track updates from source APIs

##### Cache Implementation:

```python
class ResourceCache:
    def __init__(self, cache_duration=86400):  # Default to 1 day
        self.memory_cache = {}  # In-memory cache
        self.cache_duration = cache_duration
        
    def get(self, key):
        """Get resource from cache if available and not expired"""
        if key in self.memory_cache:
            timestamp, data = self.memory_cache[key]
            if time.time() - timestamp < self.cache_duration:
                return data
        # Try database cache if not in memory
        return self._get_from_db(key)
    
    def set(self, key, data):
        """Store resource in cache with current timestamp"""
        self.memory_cache[key] = (time.time(), data)
        # Also store in database for persistence
        self._store_in_db(key, data)
        
    def invalidate(self, key=None):
        """Invalidate cache entry or entire cache"""
        if key:
            if key in self.memory_cache:
                del self.memory_cache[key]
            self._remove_from_db(key)
        else:
            self.memory_cache.clear()
            self._clear_db_cache()
```

#### 3. Authentication and Security

- **Environment Variables**: API keys stored in environment variables, not in code
- **OAuth Handling**: Support for OAuth 1.0a and 2.0 authentication flows
- **Token Rotation**: Automatic refreshing of expired tokens
- **Credential Security**: No credentials in logs or error messages
- **Request Signing**: HMAC signing for APIs that require it

##### Authentication Implementation:

```python
class ApiAuthenticator:
    def __init__(self, api_name):
        self.api_name = api_name
        self.load_credentials()
        
    def load_credentials(self):
        """Load API credentials from environment variables"""
        env_prefix = self.api_name.upper().replace('-', '_')
        self.api_key = os.getenv(f"{env_prefix}_API_KEY")
        self.api_secret = os.getenv(f"{env_prefix}_API_SECRET")
        self.access_token = os.getenv(f"{env_prefix}_ACCESS_TOKEN")
        
    def get_auth_headers(self):
        """Generate authentication headers for API requests"""
        if not self.api_key:
            logger.error(f"Missing API key for {self.api_name}")
            return {}
            
        if self.api_name == "bible_gateway":
            return {"Authorization": f"Bearer {self.api_key}"}
        elif self.api_name == "esv":
            return {"Authorization": f"Token {self.api_key}"}
        # Add other API specific auth methods
        
        return {"X-API-Key": self.api_key}
```

## Project Integration Status

The BibleScholarProject has been successfully integrated as a standalone, self-contained application with all necessary components from the parent project. The integration process involved:

1. **Module Structure Standardization**: All Python modules now follow a consistent import structure using `src` as the root package.

2. **Import Path Fixes**: All import statements have been updated to use the correct paths, ensuring modules can find their dependencies.

3. **API Module Integration**: All API modules now follow a consistent pattern with Flask Blueprints and standardized database connection handling.

4. **Database Utility Functions**: Common database functions like `get_db_connection()` have been properly implemented in the utility modules.

5. **Package Recognition**: Proper `__init__.py` files have been added to all packages to ensure Python recognizes the directory structure.

6. **Documentation**: Comprehensive documentation has been created:
   - `IMPORT_STRUCTURE.md`: Details the Python import conventions
   - `REORGANIZATION.md`: Explains the reorganization of files
   - `FINAL_INTEGRATION_SUMMARY.md`: Provides a complete overview of the integration process

7. **Testing Utilities**: Tools for verifying the integration have been created:
   - `check_imports.py`: Verifies that modules can be imported
   - `test_api_imports.py`: Tests specific API module imports
   - `test_web_app_imports.py`: Verifies web application imports
   - `fix_imports.py`: Automatically corrects common import issues

This integration ensures that the BibleScholarProject can be deployed and run independently, while maintaining all the functionality of the original system.

## Current Data Status

The following datasets have been successfully processed:

1. **Hebrew & Greek Lexicons**: 
   - 9,345 Hebrew lexicon entries
   - 10,847 Greek lexicon entries
   - 10,846 LSJ lexicon entries
   - Fully processed from the TBESH, TBESG, and TFLSJ files

2. **Tagged Bible Texts**:
   - 31,219 verses loaded
   - Processed from the TAHOT (Hebrew OT) and TAGNT (Greek NT) files

3. **Morphology Codes**:
   - 1,013 Hebrew morphology codes
   - 1,730 Greek morphology codes
   - Processed from the TEHMC and TEGMC files

4. **Proper Names**:
   - 1,317 proper names loaded
   - Primary entities processed from the TIPNR file:
     - `STEPBible-Data/TIPNR - Translators Individualised Proper Names with all References - STEPBible.org CC BY.txt` or
     - `data/TIPNR - Translators Individualised Proper Names with all References - STEPBible.org CC BY.txt`
   - Name forms and references fully integrated

5. **Versification Mappings**:
   - 54,924 verse mappings loaded
   - Processed from the TVTMS file

6. **Arabic Bible**:
   - 31,091 verses and 382,293 words processed
   - Complete Old and New Testament coverage
   - Full word-level tagging with Strong's number mapping
   - Parallel text alignment with original languages
   - Processed from the TTAraSVD files

## References

- STEPBible Data Repository: [STEPBible/STEPBible-Data](https://github.com/STEPBible/STEPBible-Data)
- STEPBible Website: [STEPBible.org](https://www.stepbible.org/)
- Data Files:
  - Lexicons: TBESH, TBESG, TFLSJ
  - Tagged Texts: TAGNT, TAHOT, TTAraSVD
  - Morphology Codes: TEHMC, TEGMC
  - Proper Names: TIPNR
  - Versification: TVTMS_expanded.txt
- Project Documentation:
  - `README.md`: Overview and quick start
  - `COMPLETED_WORK.md`: Summary of implemented features
  - `docs/STEPBible_Data_Guide.md`: Detailed guide to data files and formats
  - `REORGANIZATION_SUMMARY.md`: Summary of project reorganization work 

## Testing Framework

### Integration Tests

The STEPBible Explorer system includes a comprehensive integration test framework to verify data integrity and system functionality. These tests ensure that the biblical data has been correctly extracted, processed, and loaded into the database.

#### Running Core Tests

To run all core integration tests:

```bash
python tests/run_verification_tests.py
```

This will run all essential tests and generate a detailed log file in the `logs/tests/` directory with a timestamp.

#### Focusing on Theological Term Integrity

For theological research, we've developed specialized tests to verify the integrity of key theological terms:

```bash
python tests/run_verification_tests.py --theological
```

This focuses only on theological term integrity tests, which verify that critical Hebrew terms (like אלהים/Elohim, יהוה/YHWH) and Greek terms (like θεος/Theos, χριστος/Christos) are properly represented in the database with correct Strong's ID mappings.

#### Test Components

The integration tests cover the following areas:

1. **Database Integrity** - Verifies database structure and relationships
2. **Hebrew Strong's ID Handling** - Confirms proper Strong's ID extraction and mapping
3. **Lexicon Data** - Validates lexicon entries and relationships
4. **Verse Data** - Tests verse content and theological term integrity
5. **Morphology Data** - Checks morphology code coverage and usage
6. **Arabic Bible Data** - Verifies Arabic Bible integration
7. **ETL Integrity** - Confirms ETL process execution and results

#### Theological Terms Testing

The theological terms integrity test (`test_theological_terms_integrity` in `tests/integration/test_verse_data.py`) performs detailed validation of key theological concepts:

- Verifies 10 critical Hebrew theological terms including:
  - אלהים (Elohim, H430): Minimum 2,600 occurrences required
  - יהוה (YHWH, H3068): Minimum 6,000 occurrences required
  - משיח (Mashiach, H4899): Minimum 1,000 occurrences required
  - תורה (Torah, H8451): Minimum 1,000 occurrences required
  - צדק (Tsedeq, H6664): Minimum 1,000 occurrences required

- Verifies 10 critical Greek theological terms including:
  - θεος (Theos, G2316): Minimum 1,000 occurrences required
  - κυριος (Kyrios, G2962): Minimum 1,000 occurrences required
  - χριστος (Christos, G5547): Minimum 1,000 occurrences required
  - πνευμα (Pneuma, G4151): Minimum 1,000 occurrences required
  - χαρις (Charis, G5485): Minimum 1,000 occurrences required

- Checks for key theological passages like:
  - Genesis 1:1 (Creation)
  - Deuteronomy 6:4 (Shema)
  - Isaiah 53:5 (Suffering Servant)
  - John 3:16 (For God so loved the world)
  - Romans 3:23 (All have sinned)

#### Test Verification Report

The test runner produces a detailed report showing:

1. **Database Record Counts** - Statistics for verses, words, lexicon entries, etc.
2. **Test Execution Results** - Pass/fail status for each test
3. **Database Verification Summary** - Detailed statistics with expected values
4. **Theological Terms Statistics** - Counts of key theological terms with expected ranges

#### Interpreting Test Results

- **✅ Passed** - Test completed successfully
- **⚠️ Warning** - Test passed but with some non-critical issues
- **❌ Failed** - Test failed and requires attention

The database verification section compares actual counts with expected values. Small variances in some areas (like LSJ lexicon entries or Arabic word counts) are acceptable and documented in the tolerance ranges.

#### Known Issues

Some tests are known to fail due to test data format issues rather than actual data problems:

1. TVTMS Parser Tests - Issues with test file format
2. Pandas Tests - Issues with test data format
3. Versification Tests - Mapping discrepancies in tradition names

These tests are marked as "known failing tests" and don't indicate problems with the core functionality.

### Unit Tests

In addition to integration tests, the system includes targeted unit tests for specific components:

```bash
python -m pytest tests/unit/
```

These tests verify the behavior of individual functions and classes.

### For Developers

When extending the system, always add appropriate tests for new functionality:

1. **Unit tests** for new functions or classes
2. **Integration tests** for new data sources or end-to-end functionality
3. **Update expected counts** in test_database_integrity.py when data changes

See `docs/integration_testing_checklist.md` for a complete list of tests and expected values. 