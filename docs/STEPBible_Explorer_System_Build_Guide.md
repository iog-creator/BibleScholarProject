# STEPBible Explorer System Build Guide

## Table of Contents

- [STEPBible Explorer System Build Guide](#stepbible-explorer-system-build-guide)
  - [Table of Contents](#table-of-contents)
  - [⚠️ Important: TVTMS Data Source Authority](#️-important-tvtms-data-source-authority)
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
    - [4. English Bible Processing](#4-english-bible-processing)
    - [5. Morphology Code Processing](#5-morphology-code-processing)
    - [6. Proper Names Processing](#6-proper-names-processing)
    - [7. Versification Mapping (TVTMS)](#7-versification-mapping-tvtms)
    - [8. REST API](#8-rest-api)
    - [9. Web Interface](#9-web-interface)
    - [10. Utility Functions](#10-utility-functions)
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
      - [3.8 Run the English Bible ETL Script](#38-run-the-english-bible-etl-script)
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
  - [Theological Terms Standardization](#theological-terms-standardization)
    - [Core Hebrew Theological Terms](#core-hebrew-theological-terms)
    - [Strong's ID Format Standards](#strongs-id-format-standards)
    - [Theological Term Validation](#theological-term-validation)
    - [Code Patterns for Processing](#code-patterns-for-processing)
  - [Extended Troubleshooting Guide](#extended-troubleshooting-guide)
    - [Database Issues](#database-issues)
    - [Hebrew Strong's ID Issues](#hebrew-strongs-id-issues)
    - [Greek NT Processing Issues](#greek-nt-processing-issues)
    - [Morphology Code Processing Issues](#morphology-code-processing-issues)
    - [Web Application Issues](#web-application-issues-1)
  - [Maintenance](#maintenance)
  - [DSPy Training Data Generation and AI Assistance](#dspy-training-data-generation-and-ai-assistance)
    - [DSPy Data Generation](#dspy-data-generation)
    - [Autonomous Web Interface Interaction](#autonomous-web-interface-interaction)
  - [License](#license)

## ⚠️ Important: TVTMS Data Source Authority

> **Only `data/raw/TVTMS_expanded.txt` is the authoritative source for versification mappings in the ETL pipeline.**
> Do **not** use the `.tsv` file for ETL or integration. The `.tsv` is for reference or manual inspection only.

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
   - TTESV (English Bible):
     - `STEPBible-Data/Tagged-Bibles/TTESV - Tyndale Translation tags for ESV - TyndaleHouse.com STEPBible.org CC BY-NC.txt`

3. **Morphology Code Files**:
   - TEHMC (Hebrew): 
     - `STEPBible-Data/TEHMC - Translators Expansion of Hebrew Morphology Codes - STEPBible.org CC BY.txt` or
     - `data/TEHMC - Translators Expansion of Hebrew Morphology Codes - STEPBible.org CC BY.txt`
   - TEGMC (Greek): 
     - `STEPBible-Data/TEGMC - Translators Expansion of Greek Morphhology Codes - STEPBible.org CC BY.txt` or
     - `data/TEGMC - Translators Expansion of Greek Morphhology Codes - STEPBible.org CC BY.txt`

4. **TVTMS File**:
   - `data/raw/TVTMS_expanded.txt`: The **only** authoritative, tab-separated text file for versification mappings. Used by the ETL and parser.
   - **Do not use** the `.tsv` file for ETL. It is not supported by the parser or integration tests.
   - The expanded section starts around line 3802, marked by `#DataStart(Expanded)`

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

### 4. English Bible Processing

The English Bible processing system uses these key files in `src/etl/`:

- **etl_english_bible.py**:
  - Processes TTESV (Tyndale Translation tags for ESV) files
  - Extracts English Bible verse text with supporting data
  - Handles verse reference formats and book abbreviations
  - Implements efficient file parsing for large text files
  - Supports both insertion of new verses and updates to existing verses
  - Maintains proper database transaction handling for data integrity
  - Provides detailed logging for ETL process monitoring
  - Includes validation to ensure data completeness and integrity

The ESV processing script extracts verse text and reference information from the tagged ESV file, carefully skipping Strong's number lines and other metadata while preserving the complete verse text. The process is optimized to handle the specific format of the TTESV file, which includes verse references in the format of "BookAbbr.Chapter.Verse" followed by the verse text.

### 5. Morphology Code Processing

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

### 6. Proper Names Processing

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

### 7. Versification Mapping (TVTMS)

The TVTMS processing system is organized under `src/tvtms/` with these key files:

- **parser.py**:
  - Parses the expanded TXT file (`TVTMS_expanded.txt`), handling various reference formats
  - Manages special cases (Psalm titles, letter chapters, subverses)
  - Expands ranges and evaluates test conditions

- **validator.py**:
  - Validates mappings against reference data
  - Handles special cases like verse=0 (Psalm titles)

- **process_tvtms.py**:
  - Orchestrates the ETL pipeline for versification data
  - Processes actions in priority order (Merged, Renumber, etc.)
  - Applies mappings to move text between source and standard tables

### 8. REST API

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

### 9. Web Interface

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

### 10. Utility Functions

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

```bash
# Process Arabic Bible
python -m src.etl.etl_arabic_bible
```

Verify loading:

```bash
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.arabic_verses;" | Out-String -Stream
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.arabic_words;" | Out-String -Stream
psql -U <username> -d bible_db -c "SELECT book_name, COUNT(*) as verse_count FROM bible.arabic_verses GROUP BY book_name ORDER BY book_name;" | Out-String -Stream
```

The verse counts should match the expected counts from the original Bible text.

#### 3.8 Run the English Bible ETL Script

```bash
# Process ESV Bible text
python -m src.etl.etl_english_bible
```

Verify loading:

```bash
psql -U <username> -d bible_db -c "SELECT COUNT(*) FROM bible.verses WHERE translation_source = 'ESV';" | Out-String -Stream
psql -U <username> -d bible_db -c "SELECT book_name, COUNT(*) as verse_count FROM bible.verses WHERE translation_source = 'ESV' GROUP BY book_name ORDER BY book_name;" | Out-String -Stream
```

The ESV Bible should have approximately 31,000 verses across 66 books. Verify that key passages are properly loaded:

```bash
# Check a famous verse to confirm correct loading
psql -U <username> -d bible_db -c "SELECT verse_text FROM bible.verses WHERE translation_source = 'ESV' AND book_name = 'John' AND chapter_num = 3 AND verse_num = 16;" | Out-String -Stream
```

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

## Theological Terms Standardization

The BibleScholarProject enforces strict standardization for theological terms, especially for Hebrew terms that hold significant theological importance. These standards are documented in the `.cursor/rules/theological_terms.mdc` file and implemented throughout the ETL process.

### Core Hebrew Theological Terms

These critical Hebrew theological terms must always have the correct Strong's ID mappings:

| Term | Hebrew | Strong's ID | Minimum Required Count |
|---|-----|----|---|
| Elohim | אלהים | H430 | 2,600 |
| YHWH | יהוה | H3068 | 6,000 |
| Adon | אדון | H113 | 335 |
| Chesed | חסד | H2617 | 248 |
| Aman | אמן | H539 | 100 |

### Strong's ID Format Standards

The system enforces specific format standards for Hebrew Strong's IDs:

1. **Standard Format**: `H1234` - Basic Strong's ID with 'H' prefix and numeric identifier
2. **Extended Format**: `H1234a` - Strong's ID with letter suffix for distinguishing different words
3. **Database Storage**: Strong's IDs are stored in the dedicated `strongs_id` column, extracted from `grammar_code`
4. **Validation**: All Strong's IDs should match entries in the `hebrew_entries` lexicon table
5. **Special Codes**: Special codes (H9xxx) used for grammatical constructs are preserved

When Strong's IDs appear in grammar codes, they follow these patterns:
1. **Standard Pattern**: `{H1234}` - Enclosed in curly braces
2. **Extended Pattern**: `{H1234a}` - Extended ID enclosed in curly braces
3. **Prefix Pattern**: `H9001/{H1234}` - Special prefix code followed by ID in braces
4. **Alternate Pattern**: `{H1234}\H1234` - ID in braces followed by backslash and ID

### Theological Term Validation

After ETL processing, the system validates the presence and correct mapping of critical theological terms:

```bash
# Verify critical theological term counts
python scripts/check_critical_terms.py

# Run theological term validation tests
python -m pytest tests/integration/test_theological_terms.py
```

The validation process checks:
1. Minimum occurrence counts for each critical term
2. Proper mapping of Strong's IDs to lexicon entries
3. Contextual relationships between theological terms
4. Distribution of terms across biblical books

### Code Patterns for Processing

The ETL process uses standardized patterns for handling Strong's IDs and theological terms:

```python
# Pattern for extracting Strong's IDs from grammar_code
import re

def extract_strongs_id(grammar_code):
    """Extract Strong's ID from grammar_code field."""
    if not grammar_code:
        return None
        
    # Try standard pattern in curly braces
    match = re.search(r'\{(H[0-9]+[A-Za-z]?)\}', grammar_code)
    if match:
        return match.group(1)
        
    # Try prefix pattern
    match = re.search(r'H[0-9]+/\{(H[0-9]+)\}', grammar_code)
    if match:
        return match.group(1)
        
    # Try alternate pattern
    match = re.search(r'\{(H[0-9]+)\}\\H[0-9]+', grammar_code)
    if match:
        return match.group(1)
        
    return None
```

For validating critical theological terms:

```python
def validate_critical_terms(conn):
    """Validate minimum counts of critical theological terms."""
    critical_terms = {
        "H430": {"name": "Elohim", "min_count": 2600},
        "H3068": {"name": "YHWH", "min_count": 6000},
        "H113": {"name": "Adon", "min_count": 335},
        "H2617": {"name": "Chesed", "min_count": 248},
        "H539": {"name": "Aman", "min_count": 100}
    }
    
    cursor = conn.cursor()
    all_valid = True
    
    for strongs_id, info in critical_terms.items():
        cursor.execute(
            "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id = %s",
            (strongs_id,)
        )
        count = cursor.fetchone()[0]
        
        if count < info["min_count"]:
            print(f"Error: {info['name']} ({strongs_id}) has only {count} occurrences, expected {info['min_count']}")
            all_valid = False
        else:
            print(f"Valid: {info['name']} ({strongs_id}) has {count} occurrences")
    
    return all_valid
```

All documentation and ETL processes must maintain theological term integrity according to these standards.

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
  - Verify critical theological terms meet minimum occurrence requirements

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

## DSPy Training Data Generation and AI Assistance

The system now includes comprehensive DSPy training data generation to enable AI assistance and autonomous interaction with the web interface.

### DSPy Data Generation

1. **Generating DSPy Training Data**:
   - Run the DSPy training data generator:
     ```bash
     python scripts/generate_dspy_training_data.py
     ```
   - This creates formatted JSONL files in `data/processed/dspy_training_data/`:
     * `qa_dataset.jsonl` - Question-answering pairs for Bible verses
     * `theological_terms_dataset.jsonl` - Theological term analysis examples
     * `ner_dataset.jsonl` - Named entity recognition data
     * `web_interaction_dataset.jsonl` - Web interface interaction patterns
     * `evaluation_metrics.jsonl` - Custom theological evaluation metrics

2. **Key Features and Requirements**:
   - All data generation must include theological term integrity checks
   - Critical terms (Elohim, YHWH, Adon, Chesed, Aman) must meet minimum occurrence counts
   - Processing must be done in batches of at least 100 records at a time for efficiency
   - Web interaction training must include parameter extraction and response formatting

3. **Performance Guidelines**:
   - Run generation with `conn.autocommit = True` to prevent transaction issues
   - Use batch processing instead of one-by-one record processing
   - Use parallel processing for large datasets when possible:
     ```python
     # Example batch processing approach
     def process_in_batches(items, batch_size=100):
         results = []
         for i in range(0, len(items), batch_size):
             batch = items[i:i+batch_size]
             # Process batch
             batch_results = process_batch(batch)
             results.extend(batch_results)
         return results
     ```

### Autonomous Web Interface Interaction

1. **Enabling AI-Assisted Interface**:
   - The `web_interaction_dataset.jsonl` provides training examples for:
     * Database search tasks
     * Strong's lexicon lookups
     * Translation comparison
     * Theological analysis
   
   - Integration with the web application:
     ```python
     # Example DSPy Agent setup for web interaction
     class BibleSearchAgent(dspy.Module):
         def __init__(self):
             super().__init__()
             self.query_parser = dspy.ChainOfThought("context, query -> action, parameters")
             
         def forward(self, query):
             # Parse query and extract parameters
             parsed = self.query_parser(context="Biblical research assistant", query=query)
             
             # Execute appropriate action based on parsed intent
             if parsed.action == "search_database":
                 return search_bible_database(**parsed.parameters)
             elif parsed.action == "lookup_strongs":
                 return lookup_strongs_entry(**parsed.parameters)
             # Other actions...
     ```

2. **DSPy Optimization for Theological Accuracy**:
   - Custom theological evaluation metrics ensure accuracy in critical concepts
   - Models can be optimized using DSPy's SIMBA or other prompt optimizers:
     ```python
     from dspy.teleprompt import SIMBA
     
     # Training DSPy for theological accuracy
     optimizer = SIMBA(metric="theological_accuracy")
     optimized_model = optimizer.optimize(model, trainset=trainset)
     ```

3. **Deployment and Management**:
   - Deploy optimized models as API endpoints
   - Monitor theological accuracy metrics
   - Regularly update training data with new examples
   - Implement user feedback collection for continuous improvement

4. **Theological Accuracy Requirements**:
   - All AI responses must maintain theological term integrity
   - Critical terms like Elohim (H430) and YHWH (H3068) must be handled correctly
   - Responses must align with scholarly biblical interpretations
   - Named entity recognition must correctly identify DEITY vs PERSON entities

## License

This project is licensed under the MIT License. The STEPBible data is licensed under CC BY 4.0 by Tyndale House, Cambridge, UK. 