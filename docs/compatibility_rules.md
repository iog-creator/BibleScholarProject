# BibleScholarProject Compatibility Rules

## Overview

This document describes compatibility patterns and rules for the BibleScholarProject to ensure consistent behavior across different environments and systems.

## Import Paths

The BibleScholarProject can be run in two main modes, which require different import strategies:

1. **Development mode** - running scripts directly
2. **Installed mode** - running as an installed package

### Import Resolution

To handle both modes, use the following pattern in entry-point scripts:

```python
import os
import sys

# Add parent directory to path for development mode
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # Try absolute import first (installed mode)
    from src.database.connection import get_db_connection
except ImportError:
    try:
        # Try relative import (development mode within package)
        from ..database.connection import get_db_connection
    except ImportError:
        # Fall back to directly modifying path and using absolute import
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.database.connection import get_db_connection
```

## Running Scripts

When running scripts directly, ensure you are in the project root directory:

```bash
# Good
python src/etl/fix_hebrew_strongs_ids.py

# Also good (using entry points defined in setup.py)
fix-hebrew-strongs

# Avoid
cd src/etl && python fix_hebrew_strongs_ids.py  # Import errors likely
```

## Windows-specific Rules

On Windows, handle Unicode and filesystem issues with these practices:

1. Use UTF-8 encoding when reading/writing files with Hebrew or Arabic text:
   ```python
   with open(file_path, 'r', encoding='utf-8') as f:
       content = f.read()
   ```

2. Use pathlib for cross-platform path handling:
   ```python
   from pathlib import Path
   
   data_dir = Path("data") / "raw"
   file_path = data_dir / "hebrew_terms.txt"
   ```

3. Use Out-String -Stream instead of cat for PowerShell piping:
   ```powershell
   # Good
   psql -U postgres -d bible_db -c "SELECT * FROM bible.verses LIMIT 5;" | Out-String -Stream
   
   # Avoid
   psql -U postgres -d bible_db -c "SELECT * FROM bible.verses LIMIT 5;" | cat
   ```

## Database Connection

To handle connection issues across different environments:

1. Add timeout and reconnection logic:
   ```python
   def get_db_connection_with_retry(max_retries=3, retry_delay=2):
       for attempt in range(max_retries):
           try:
               conn = get_db_connection()
               if conn:
                   return conn
           except Exception as e:
               logger.warning(f"Connection attempt {attempt+1} failed: {e}")
               time.sleep(retry_delay)
       
       logger.error(f"Failed to connect after {max_retries} attempts")
       return None
   ```

2. Always check table existence before operations:
   ```python
   if not check_table_exists(conn, 'bible', 'hebrew_entries'):
       # Handle missing table
   ``` 