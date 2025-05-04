# BibleScholarProject Import Rules

## Overview

This document describes the import patterns and rules for the BibleScholarProject.

## Python Module Structure

The BibleScholarProject follows these module import patterns:

1. When running scripts directly, use relative imports for local modules:
   ```python
   # If inside src/etl/script.py importing from src/database/connection.py
   from ...database.connection import get_db_connection
   ```

2. When running as an installed package, use absolute imports:
   ```python
   # If the package is installed
   from src.database.connection import get_db_connection
   ```

3. For main scripts or entry points that will be run directly, include sys.path modification to allow absolute imports:
   ```python
   import os
   import sys
   sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   from src.database.connection import get_db_connection
   ```

## External Dependencies

List imports in the following order:
1. Standard library imports
2. Third-party package imports
3. Local application imports

Example:
```python
# Standard library
import os
import sys
import logging

# Third-party packages
import psycopg2
from flask import Flask, jsonify
from dotenv import load_dotenv

# Local modules
from database.connection import get_db_connection
from etl.fix_hebrew_strongs_ids import update_hebrew_strongs_ids
```

## Import Rules for Database Access

Always import database connections from the central module:
```python
from src.database.connection import get_db_connection, check_table_exists
```

## Implementation Notes

These rules were created to address the "No module named 'src'" errors that can occur when running scripts directly versus as an installed package. 