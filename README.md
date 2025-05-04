# BibleScholarProject

A comprehensive system for processing, analyzing, and exploring biblical texts with lexical information, morphological analysis, and multilingual support.

## Overview

BibleScholarProject is a standalone application for accessing and analyzing biblical data from the STEPBible project. The system includes:

- **Lexicon Integration**: Hebrew and Greek lexicon data with detailed definitions and grammar information.
- **Tagged Text Analysis**: Process Bible texts with morphological tagging, linking words to lexicon entries.
- **Multilingual Support**: Including Hebrew, Greek, and Arabic texts with parallel viewing capabilities.
- **Morphology Code Expansion**: Detailed grammatical information for Hebrew and Greek words.
- **Proper Name Identification**: Biblical proper names with references and relationships.
- **Versification Mapping**: Cross-reference verses between different Bible traditions.
- **REST API**: Access biblical data programmatically through a comprehensive API.
- **Web Interface**: User-friendly interface for exploring the biblical data.
- **External Resources Integration**: Connect with biblical commentaries and academic resources.

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

5. Process the biblical data:
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
│   ├── tvtms/              # Versification mapping
│   ├── utils/              # Utility functions
│   ├── web_app.py          # Main web application
│   └── web_app_minimal.py  # Minimal web application
├── templates/              # HTML templates
└── tests/                  # Test files
```

## Importing Modules

The project uses a consistent import structure:

```python
# Example imports
from src.utils.db_utils import get_db_connection
from src.database.connection import get_connection_from_env
```

See `IMPORT_STRUCTURE.md` for detailed information on the project's import conventions.

## API Documentation

The system provides the following API endpoints:

- `/api/lexicon/`: Access to Hebrew and Greek lexicon data
- `/api/text/`: Tagged biblical text with morphological information
- `/api/morphology/`: Morphology code explanations
- `/api/names/`: Biblical proper names data
- `/api/external/`: External biblical resources

For detailed API documentation, see the documentation in `docs/api/`.

## License

This project is licensed under the MIT License. The STEPBible data is licensed under CC BY 4.0 by Tyndale House, Cambridge, UK.

## Acknowledgments

- [STEPBible](https://stepbible.org/) - For the original biblical data
- Tyndale House, Cambridge - For the lexical and tagged Bible resources

## Further Documentation

- `docs/STEPBible_Explorer_System_Build_Guide.md`: Comprehensive guide for setting up and using the system
- `IMPORT_STRUCTURE.md`: Documentation on the import structure
<<<<<<< HEAD
- `FINAL_INTEGRATION_SUMMARY.md`: Summary of the integration process 
=======
- `FINAL_INTEGRATION_SUMMARY.md`: Summary of the integration process 
>>>>>>> 7ce9bae97b2e6d0fe65169a363af093a8e5043a4
