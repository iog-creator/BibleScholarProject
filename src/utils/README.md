# Utility Functions

This directory contains utility functions and helpers used throughout the STEPBible Explorer project.

## Modules

- **file_utils.py**: File operations and path handling utilities
- **db_utils.py**: Database connection and query utilities
- **text_utils.py**: Text processing utilities for handling Bible references, Strong's numbers, etc.
- **logging_config.py**: Logging configuration utilities for consistent logging across components

## Usage Examples

### File Utilities

```python
from src.utils.file_utils import open_file_with_encoding, ensure_directory_exists

# Open a file with proper encoding
with open_file_with_encoding("data/raw/sample.txt") as f:
    content = f.read()

# Ensure a directory exists
ensure_directory_exists("logs/etl")
```

### Database Utilities

```python
from src.utils.db_utils import get_connection_from_env, execute_query

# Get a database connection
conn = get_connection_from_env()

# Execute a query
results = execute_query(conn, "SELECT * FROM bible.books")
```

### Text Utilities

```python
from src.utils.text_utils import parse_reference, clean_strong_number

# Parse a Bible reference
book, chapter, verse = parse_reference("Gen.1.1")

# Clean a Strong's number
strongs_id = clean_strong_number("H0123")
```

### Logging Utilities

```python
from src.utils.logging_config import configure_etl_logging

# Configure logging for an ETL component
logger = configure_etl_logging("etl_lexicons")

# Use the logger
logger.info("Starting lexicon processing")
logger.error("An error occurred: %s", str(error))
``` 