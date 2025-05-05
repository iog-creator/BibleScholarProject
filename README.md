# BibleScholarProject

A comprehensive system for processing, analyzing, and exploring biblical texts with lexical information, morphological analysis, and multilingual support.

## Overview

BibleScholarProject is a standalone application for accessing and analyzing biblical data from the STEPBible project. The system includes:

- **Lexicon Integration**: Hebrew and Greek lexicon data with detailed definitions and grammar information.
- **Tagged Text Analysis**: Process Bible texts with morphological tagging, linking words to lexicon entries.
- **Multilingual Support**: Including Hebrew, Greek, and Arabic texts with parallel viewing capabilities.
- **Morphology Code Expansion**: Detailed grammatical information for Hebrew and Greek words.
- **Proper Name Identification**: Biblical proper names with references and relationships.
- **Versification Mapping**: Cross-reference verses between different Bible traditions using only `TVTMS_expanded.txt` (tab-separated TXT, not TSV)
- **REST API**: Access biblical data programmatically through a comprehensive API.
- **Web Interface**: User-friendly interface for exploring the biblical data.
- **External Resources Integration**: Connect with biblical commentaries and academic resources.

## Features
- Complete Strong's ID mapping for all Hebrew words (100% coverage)
- Standardized theological term handling for critical Hebrew terms
- Validates critical Hebrew terms (e.g., Elohim/H430, YHWH/H3068, Chesed/H2617) with proper Strong's mappings
- Cross-language term mappings (e.g., YHWH-Theos-Allah) via `/cross_language`
- Advanced extraction of embedded Strong's IDs from grammar codes

## Recent Updates

### Database and TVTMS Improvements
- Enhanced TVTMS database functions to support both direct psycopg Connection and SQLAlchemy ConnectionFairy objects
- Implemented proper transaction management with explicit commits for direct database connections
- Fixed versification data integration with 1,786 sample versification mappings covering all mapping types
- Added comprehensive support for special cases (Psalm 3:0, 3John 1:15)
- Created robust integration test infrastructure for database verification

### Versification System Enhancement
- Implemented 6 different versification tradition mappings (Hebrew, Greek, Latin, English, Aramaic, Syriac)
- Added support for 7 different mapping types (Psalm title, Missing verse, Merged verse, etc.)
- Ensured >50% book coverage for both Old and New Testament

### Integration Improvements
- All components are now properly integrated with correct import paths
- The project can be run as a standalone application without dependencies
- Improved error handling throughout the application
- Enhanced logging for all modules

## Getting Started

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 13 or higher
- Required Python packages (see `requirements.txt`)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/BibleScholarProject.git
   cd BibleScholarProject
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the environment:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. Create the database:
   ```bash
   psql -U <username> -c "CREATE DATABASE bible_db;"
   psql -U <username> -d bible_db -f sql/create_tables.sql
   psql -U <username> -d bible_db -f sql/populate_books.sql
   ```

5. Install the package in development mode:
   ```bash
   pip install -e .
   ```

6. Apply the Hebrew Strong's ID fixes:
   ```bash
   # Run the main extraction script
   python -m src.etl.fix_hebrew_strongs_ids
   
   # Insert critical theological terms
   python scripts/insert_critical_terms.py
   
   # Update existing entries
   python scripts/update_critical_terms.py
   ```

7. Process the biblical data:
   ```bash
   # See detailed setup instructions in docs/STEPBible_Explorer_System_Build_Guide.md
   ```

### Running the Application

1. Start the web application:
   ```bash
   python -m src.web_app
   ```

2. Access the web interface at `http://localhost:5000`

3. For a minimal version:
   ```bash
   python -m src.web_app_minimal
   ```

## Project Structure

```
BibleScholarProject/
├── docs/                   # Documentation
│   └── STEPBible_Explorer_System_Build_Guide.md  # Comprehensive guide
├── sql/                    # SQL scripts and schemas
├── src/                    # Source code
│   ├── api/                # API endpoints
│   ├── database/           # Database connections
│   ├── etl/                # ETL processes
│   │   ├── morphology/     # Morphology code processing
│   │   └── names/          # Biblical names processing
│   ├── tvtms/              # Versification mapping
│   ├── utils/              # Utility functions
│   ├── web_app.py          # Main web application
│   └── web_app_minimal.py  # Minimal web application
├── scripts/                # Utility scripts
│   ├── insert_critical_terms.py  # Insert theological terms
│   ├── update_critical_terms.py  # Update theological terms
│   └── check_related_hebrew_words.py  # Verify Hebrew word mappings
├── templates/              # HTML templates
├── .cursor/rules/          # Development rules and patterns
│   └── theological_terms.md  # Rules for theological terms
└── tests/                  # Test files
```

## Hebrew Strong's ID Fixes

We've implemented comprehensive fixes to ensure all Hebrew words have proper Strong's ID mappings:

1. **Extraction Process**: Extracts Strong's IDs from grammar_code field when encoded in various formats
2. **Critical Term Mapping**: Ensures important theological terms like Elohim and YHWH have consistent mappings
3. **Extended ID Handling**: Properly handles extended IDs with letter suffixes (e.g., H1234a)
4. **Standardization**: Provides standardized patterns for handling theological terms

For details, see `HEBREW_STRONGS_FIXES.md`.

## Database Structure

The biblical data is stored in a PostgreSQL database with these key tables:

- `bible.hebrew_ot_words`: Hebrew Old Testament words with morphological tagging
- `bible.greek_nt_words`: Greek New Testament words with morphological tagging
- `bible.hebrew_entries`: Hebrew lexicon entries
- `bible.greek_entries`: Greek lexicon entries

All 308,189 Hebrew words now have proper Strong's ID mappings with 100% coverage.

## Importing Modules

The project uses a consistent import structure:

```python
# Example imports
from src.utils.db_utils import get_db_connection
from src.database.connection import get_connection_from_env
```

See `IMPORT_STRUCTURE.md` for detailed information on the project's import conventions.

## Critical Hebrew Theological Terms

The system properly maps these critical theological terms with consistent Strong's IDs:

| Term | Strong's ID | Hebrew | Translation | Minimum Count | Actual Count |
|------|------------|--------|-------------|--------------|--------------|
| Elohim | H430 | אלהים | God | 2,600 | 2,600+ |
| YHWH | H3068 | יהוה | LORD | 6,000 | 6,525 |
| Adon | H113 | אדון | lord | 335 | 335+ |
| Chesed | H2617 | חסד | lovingkindness | 248 | 248+ |
| Aman | H539 | אמן | faith | 100 | 100+ |

These mappings enable detailed theological analysis of key Hebrew concepts throughout the Bible.

## Data Statistics

The project includes comprehensive biblical data:
- **Total Bible verses**: 31,219
- **Hebrew OT words**: 308,189 words (100% with Strong's ID mapping)
- **Greek NT words**: 142,096 words
- **Versification mappings**: 1,786 mappings across 6 traditions
- **Hebrew morphology codes**: 1,013
- **Greek morphology codes**: 1,676

## API Documentation

The system provides the following API endpoints:

- `/api/lexicon/`: Access to Hebrew and Greek lexicon data
- `/api/text/`: Tagged biblical text with morphological information
- `/api/morphology/`: Morphology code explanations
- `/api/names/`: Biblical proper names data
- `/api/external/`: External biblical resources
- `/api/theological_terms_report`: Counts for key theological terms
- `/api/lexicon/hebrew/validate_critical_terms`: Validates critical Hebrew terms

For detailed API documentation, see the documentation in `docs/api/`.

## Testing

Run the integration tests to verify database integrity and functionality:

```bash
python -m pytest tests/integration
```

For specific test categories:
```bash
# Test database integrity
python -m pytest tests/integration/test_database_integrity.py

# Test versification data
python -m pytest tests/integration/test_versification_data.py

# Test ETL processes
python -m pytest tests/integration/test_etl.py
```

## License

This project is available under a dual license:

1. **Non-Commercial Use License (Free)**: For individuals and organizations using this project without monetary compensation or commercial advantage. This includes personal study, academic research, and non-profit religious use where no fees are charged.

2. **Commercial Use License (Paid)**: Required for any entity or individual using this project in a commercial context, including:
   - Religious organizations charging fees for services using the materials
   - For-profit religious businesses
   - Companies selling products or services based on this project
   - Any use where monetary compensation is received

**Specific Exemptions**:
- The PostgreSQL database structure, schema, and SQL files are freely available for all uses
- The raw biblical data itself is freely available

See the LICENSE file for complete details.

The STEPBible data is licensed under CC BY 4.0 by Tyndale House, Cambridge, UK.

## Acknowledgments

- [STEPBible](https://stepbible.org/) - For the original biblical data
- Tyndale House, Cambridge - For the lexical and tagged Bible resources

## Further Documentation

- `docs/STEPBible_Explorer_System_Build_Guide.md`: Comprehensive guide for setting up and using the system
- `IMPORT_STRUCTURE.md`: Documentation on the import structure
- `HEBREW_STRONGS_FIXES.md`: Details on the fixes for Hebrew Strong's IDs
- `.cursor/rules/theological_terms.md`: Standardized rules for handling theological terms

## Running the New Features

To run and test the theological terms and cross-language mapping features:

```bash
# Start both the API server and web app
make run-all

# In a new terminal, run the integration tests
make test-integration

# Or verify critical theological terms directly
python scripts/check_related_hebrew_words.py
```

### New API Endpoints

- `/api/theological_terms_report`: Returns counts for key theological terms in Hebrew and Greek
- `/api/lexicon/hebrew/validate_critical_terms`: Validates critical Hebrew terms like Elohim (H430)
- `/api/cross_language/terms`: Returns cross-language term mappings (Hebrew/Greek/Arabic)

### New Web Routes

- `/theological_terms_report`: Displays frequency chart for theological terms
- `/hebrew_terms_validation`: Shows validation results for critical Hebrew terms
- `/cross_language`: Displays cross-language mappings table with counts

## Data Source Fallback for ETL and Integration Tests (2024-05-04)

If versification mapping or TVTMS source files are missing in the main data directory, the ETL and integration tests will automatically use files from the secondary data source (STEPBible-Datav2 repo) at:

    C:\Users\mccoy\Documents\Projects\Projects\AiBibleProject\SecondBibleData\STEPBible-Datav2

This ensures robust test and ETL operation even if the main data directory is incomplete.

## ⚠️ Important: TVTMS Data Source Authority

> **Only `data/raw/TVTMS_expanded.txt` is the authoritative source for versification mappings in the ETL pipeline.**
> Do **not** use the `.tsv` file for ETL or integration. The `.tsv` is for reference or manual inspection only.

## Data Files

- TVTMS versification mapping: `data/raw/TVTMS_expanded.txt` (**authoritative for ETL**)
- Do not use the `.tsv` file for ETL or integration.

> **Note:** If you see references to a `.tsv` file in this documentation or code, treat them as non-authoritative and do not use them for ETL or integration.
