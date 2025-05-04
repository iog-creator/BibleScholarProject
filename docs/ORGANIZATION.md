# Bible Scholar Project - Organization Guide

This document provides a detailed overview of the Bible Scholar Project (STEPBible Explorer) organization, including its structure, components, and how they interact.

## System Architecture

The Bible Scholar Project follows a layered architecture:

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
│   ├── api/                # API documentation
│   ├── database/           # Database schema documentation
│   └── etl/                # ETL process documentation
├── logs/                   # Log files
│   ├── api/                # API logs
│   ├── etl/                # ETL process logs
│   ├── tests/              # Test logs
│   └── web/                # Web application logs
├── sql/                    # SQL scripts and schema definitions
│   ├── create_tables.sql       # Database schema creation
│   ├── create_indexes.sql      # Index creation
│   └── populate_books.sql      # Reference data
├── src/                    # Source code
│   ├── api/                # API endpoints and controllers
│   ├── database/           # Database connection and operations
│   └── etl/                # ETL scripts for data processing
│       ├── morphology/     # Morphology code processing
│       └── names/          # Proper names processing
├── templates/              # HTML templates for the web interface
└── tests/                  # Test files
    ├── data/               # Test data files
    ├── integration/        # Integration tests
    └── unit/               # Unit tests
```

## Database Schema

The database schema is defined in `sql/create_tables.sql` and includes the following key tables:

### Lexicon Tables
- **hebrew_entries**: Hebrew lexicon entries from TBESH
  - Fields: id, strongs_id, word, pronunciation, definition, usage, etc.
- **greek_entries**: Greek lexicon entries from TBESG
  - Fields: id, strongs_id, word, pronunciation, definition, usage, etc.
- **word_relationships**: Relationships between words
  - Fields: id, source_id, target_id, relationship_type, etc.

### Tagged Text Tables
- **verses**: Bible verses with metadata
  - Fields: id, book_name, chapter_num, verse_num, text, translation_source, etc.
- **greek_nt_words**: Individual Greek words from the NT
  - Fields: id, verse_id, word, strongs_id, grammar_code, position, etc.
- **hebrew_ot_words**: Individual Hebrew words from the OT
  - Fields: id, verse_id, word, strongs_id, grammar_code, position, etc.

### Morphology Tables
- **hebrew_morphology_codes**: Hebrew morphology code explanations
  - Fields: id, code, description, function, example, etc.
- **greek_morphology_codes**: Greek morphology code explanations
  - Fields: id, code, description, function, example, etc.

### Proper Names Tables
- **proper_names**: Biblical proper names
  - Fields: id, name, type, gender, description, etc.
- **proper_name_forms**: Forms of proper names in original languages
  - Fields: id, name_id, language, form, transliteration, etc.
- **proper_name_references**: Biblical references for proper names
  - Fields: id, name_id, book_name, chapter_num, verse_num, etc.

### Arabic Bible Tables
- **arabic_verses**: Arabic Bible verses
  - Fields: id, book_name, chapter_num, verse_num, text, etc.
- **arabic_words**: Individual Arabic words with tagging
  - Fields: id, verse_id, word, strongs_id, transliteration, position, etc.

### Versification Tables
- **versification_mappings**: Maps between different versification traditions
  - Fields: id, source_tradition, source_book, source_chapter, source_verse, standard_book, standard_chapter, standard_verse, action, etc.

## ETL Process

The ETL (Extract, Transform, Load) process is handled by scripts in the `src/etl/` directory:

### Key ETL Scripts

1. **etl_lexicons.py**: Processes Hebrew and Greek lexicons
   - Input: TBESH and TBESG files
   - Output: `hebrew_entries` and `greek_entries` tables

2. **etl_greek_nt.py**: Processes Greek New Testament
   - Input: TAGNT files (Gospels, Acts-Revelation)
   - Output: `verses` and `greek_nt_words` tables

3. **etl_hebrew_ot.py**: Processes Hebrew Old Testament
   - Input: TAHOT files (Torah, Historical, Wisdom, Prophets)
   - Output: `verses` and `hebrew_ot_words` tables

4. **etl_morphology/**: Processes morphology codes
   - **etl_hebrew_morphology.py**: Processes Hebrew morphology (TEHMC)
   - **etl_greek_morphology.py**: Processes Greek morphology (TEGMC)
   - Output: `hebrew_morphology_codes` and `greek_morphology_codes` tables

5. **etl_names/etl_proper_names.py**: Processes proper names
   - Input: TIPNR file
   - Output: `proper_names`, `proper_name_forms`, and `proper_name_references` tables

6. **etl_arabic_bible.py**: Processes Arabic Bible
   - Input: TTAraSVD files
   - Output: `arabic_verses` and `arabic_words` tables

7. **tvtms/process_tvtms.py**: Processes versification mappings
   - Input: TVTMS file
   - Output: `versification_mappings` table

8. **fix_hebrew_strongs_ids.py**: Fixes Hebrew Strong's IDs
   - Extracts IDs from `grammar_code` field to `strongs_id` field
   - Updates `hebrew_ot_words` table

9. **fix_extended_hebrew_strongs.py**: Handles extended Hebrew Strong's IDs
   - Maps basic IDs to extended versions (e.g., H1234 → H1234a)
   - Updates `hebrew_ot_words` table

### ETL Process Flow

1. Load lexicons (Hebrew, Greek)
2. Load morphology codes (Hebrew, Greek)
3. Load Bible texts (Greek NT, Hebrew OT)
4. Load proper names
5. Load Arabic Bible
6. Load versification mappings
7. Fix Hebrew Strong's IDs
8. Optimize database (create indexes)

## API Endpoints

The API endpoints are defined in the `src/api/` directory:

### Lexicon API (`lexicon_api.py`)
- `/api/lexicon/stats`: Statistics about lexicon entries
- `/api/lexicon/hebrew/{strongs_id}`: Get Hebrew lexicon entry
- `/api/lexicon/greek/{strongs_id}`: Get Greek lexicon entry
- `/api/lexicon/search`: Search lexicon entries by keyword

### Tagged Text API (`tagged_text_api.py`)
- `/api/tagged/verse`: Get a verse with tagged words
- `/api/tagged/search`: Search for occurrences of words by Strong's ID

### Morphology API (`morphology_api.py`)
- `/api/morphology/hebrew`: Get Hebrew morphology codes
- `/api/morphology/hebrew/{code}`: Get specific Hebrew morphology code
- `/api/morphology/greek`: Get Greek morphology codes
- `/api/morphology/greek/{code}`: Get specific Greek morphology code

### Proper Names API
- `/api/names`: Get proper names with optional filtering
- `/api/names/{name_id}`: Get specific proper name details
- `/api/names/search`: Search proper names by criteria
- `/api/verse/names`: Get names mentioned in a specific verse

### External Resources API
- `/api/resources/commentaries`: Access commentary resources
- `/api/resources/archaeology`: Access archaeological data
- `/api/resources/manuscripts`: Access manuscript information
- `/api/resources/translations`: Compare multiple translations

## Web Interface

The web interface is implemented in `src/web_app.py` and uses templates in the `templates/` directory:

### Key Pages
- **Home page**: Search interface and overview
- **Lexicon entry**: Details of a lexicon entry
- **Verse detail**: Verse with tagged words and analysis
- **Morphology detail**: Explanation of morphology codes
- **Proper name detail**: Details of a proper name with references
- **Verse with resources**: Verse with external resources and commentary

### Templates
- `base.html`: Main layout template
- `search.html`: Search interface for lexicons, verses, and names
- `lexicon_entry.html`: Detailed view of lexicon entries
- `verse_detail.html`: Verse display with word analysis
- `morphology_detail.html`: Explanation of morphology codes
- `verse_with_resources.html`: Verse with external resources

## Testing Framework

The testing framework is organized in the `tests/` directory:

### Integration Tests
- **Database Integrity**: Verifies database structure and relationships
- **Hebrew Strong's ID Handling**: Tests proper Strong's ID extraction
- **Lexicon Data**: Validates lexicon entries and relationships
- **Verse Data**: Tests verse content and theological term integrity
- **Morphology Data**: Checks morphology code coverage and usage
- **Arabic Bible Data**: Verifies Arabic Bible integration
- **ETL Integrity**: Validates ETL process execution and results

### Theological Term Testing
- Tests key theological terms in Hebrew and Greek
- Verifies proper Strong's ID mapping for theological terms
- Checks for key theological passages

### Test Runner
- `tests/run_verification_tests.py`: Main test runner
- `--theological` flag for focused theological term testing

## Special Handling

### Hebrew Strong's ID Handling
Hebrew Strong's IDs are embedded in the `grammar_code` field in different formats:
- Standard format: `{H1234}`
- Extended format: `{H1234a}`
- Prefix format: `H9001/{H1234}`
- Alternate format: `{H1234}\H1234`

The `fix_hebrew_strongs_ids.py` script extracts these IDs and standardizes them in the `strongs_id` field.

### Multi-line Morphology Code Processing
Morphology code files (TEHMC, TEGMC) contain multi-line records delimited by '$'. The ETL scripts use a state machine approach to parse these records properly.

### Versification Mapping
The TVTMS file contains mappings between different versification traditions. Special handling is implemented for:
- Psalm titles (verse=0)
- Letter chapters (e.g., Est.A:1)
- Subverses (.1, .2, .a, .b)
- Absent references
- Verse ranges

## Data Files

The system processes the following data files from STEPBible:

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

3. **Morphology Code Files**:
   - TEHMC (Hebrew): `STEPBible-Data/TEHMC - Translators Expansion of Hebrew Morphology Codes - STEPBible.org CC BY.txt`
   - TEGMC (Greek): `STEPBible-Data/TEGMC - Translators Expansion of Greek Morphhology Codes - STEPBible.org CC BY.txt`

4. **Proper Names File**:
   - TIPNR: `STEPBible-Data/TIPNR - Translators Individualised Proper Names with all References - STEPBible.org CC BY.txt`

5. **Versification Mapping File**:
   - TVTMS: `STEPBible-Data/TVTMS - Translators Versification Traditions with Methodology for Standardisation for Eng+Heb+Lat+Grk+Others - STEPBible.org CC BY.txt`

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

## Batch Processing and Performance

The system implements batch processing for large datasets:

- Configurable batch sizes in ETL scripts (default: 1000 records)
- Incremental commits to prevent long-running transactions
- Database indexes for frequently queried fields
- Query optimization for complex operations

## External Resources Integration

The system includes integration with external biblical resources:

- Modular API connection framework
- Multi-level caching system (in-memory, filesystem, database)
- Secure authentication and API key management
- Resource display alongside Bible text

## Recent Enhancements

### Integration Test Framework Enhancement (2025-06-03)
- Added comprehensive theological term integrity testing
- Enhanced test reporting with categorized sections
- Added color-coded status indicators

### Hebrew Strong's ID Enhancement (2025-06-02)
- Improved Hebrew Strong's ID extraction and handling
- Increased coverage to 99.99% of Hebrew words
- Properly handled extended IDs with letter suffixes

### Arabic Bible Integration (2025-05-30)
- Enhanced Arabic Bible processing with improved parsing
- Verified full coverage of all 66 books with 31,091 verses
- Confirmed 100% Strong's number mapping for loaded words 