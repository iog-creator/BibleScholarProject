# BibleScholarProject Import Structure

## Overview
This document explains the Python import structure used in BibleScholarProject and the decisions made to ensure a consistent and maintainable codebase.

## Package Structure

The project follows a standard Python package structure:

```
BibleScholarProject/
├── src/                     # Main package
│   ├── __init__.py
│   ├── api/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── lexicon_api.py
│   │   ├── morphology_api.py
│   │   ├── proper_names_api.py
│   │   └── tagged_text_api.py
│   ├── database/            # Database connection and operations
│   │   ├── __init__.py
│   │   └── connection.py
│   ├── etl/                 # ETL processes
│   │   └── __init__.py
│   ├── tvtms/               # TVTMS module
│   │   └── __init__.py
│   ├── utils/               # Utility functions
│   │   ├── __init__.py
│   │   └── db_utils.py
│   └── web_app.py           # Main web application
```

## Import Principles

1. **Absolute Imports with Package Root**
   - All internal imports use the `src` package as the root
   - Example: `from src.database import connection`

2. **No Relative Imports**
   - To maintain consistency and readability, relative imports are avoided
   - This makes it easier to understand the import structure

3. **Explicit Imports**
   - Explicit imports are preferred over wildcard imports
   - Example: `from src.utils.db_utils import get_db_connection` instead of `from src.utils.db_utils import *`

## Key Import Relationships

- **API Modules**: Import `get_db_connection` from `src.utils.db_utils`
- **Database Modules**: Import from `src.database.connection`
- **ETL Modules**: Import from `src.etl`
- **TVTMS Module**: Import from `src.tvtms`

## Import Fixes Applied

Several import-related issues were addressed to ensure proper functionality:

1. **Import Path Updates**
   - Updated imports to use `src.` prefix
   - Fixed incorrect import paths (e.g., `from src.database.db_utils` to `from src.utils.db_utils`)

2. **Function Additions**
   - Added `get_db_connection()` to `src.utils.db_utils` which was required by API modules

3. **Package Structure Enforcement**
   - Added `__init__.py` files to ensure proper package recognition
   - Ensured consistent naming and package organization

## Tools for Import Management

Two utility scripts are provided to help maintain import consistency:

1. **check_imports.py**
   - Verifies that modules can be imported correctly
   - Identifies import issues for troubleshooting

2. **fix_imports.py**
   - Automatically fixes common import issues
   - Updates import paths to use the correct package structure

## Best Practices for Future Development

1. **Maintain Package Structure**
   - Keep the existing package structure when adding new modules
   - Place new files in the appropriate directories

2. **Follow Import Conventions**
   - Use `src.` prefix for all internal imports
   - Be explicit about what is being imported

3. **Test Imports**
   - After adding new modules, run `check_imports.py` to verify import functionality
   - If issues are found, run `fix_imports.py` to attempt automatic fixes

4. **Document Dependencies**
   - Document any new external dependencies in `requirements.txt`
   - Note any special import requirements in module docstrings 