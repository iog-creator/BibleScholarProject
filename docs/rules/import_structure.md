# Import Structure Guidelines

## Core Principles

1. Always use absolute imports from the `src` package
2. Never use relative imports (e.g., `from ..utils import x`)
3. Keep import statements at the top of the file
4. Group imports by standard library, third-party, and local

## Standard Import Format

Follow this import format for all Python files:

```python
# Standard library imports
import os
import re
import logging
from datetime import datetime

# Third-party imports
import pandas as pd
import numpy as np
import psycopg2
from flask import Flask, request, jsonify

# Local imports
from src.database.connection import get_db_connection
from src.utils.file_utils import read_data_file
from src.etl.helpers import process_batch
```

## Package Structure

The BibleScholarProject uses the following package structure:

```
src/
├── api/            # API endpoints
├── database/       # Database connections and operations
├── etl/            # ETL processes
│   ├── morphology/ # Morphology processing
│   └── names/      # Name processing
├── tvtms/          # Versification mapping
└── utils/          # Utility functions
```

## Import Examples by Module

### API Modules

```python
# In src/api/lexicon_api.py
from flask import Flask, request, jsonify
from src.database.connection import get_db_connection
from src.utils.logging_config import setup_logger
```

### ETL Modules

```python
# In src/etl/hebrew_ot.py
import pandas as pd
from src.database.connection import get_db_connection
from src.utils.file_utils import read_data_file
from src.utils.db_utils import execute_batch_insert
```

### Database Modules

```python
# In src.database.connection.py
import os
import psycopg2
from src.utils.logging_config import setup_logger
```

## Common Issues to Avoid

1. **Circular Imports**: Never create circular dependencies between modules
   ```python
   # WRONG: Circular dependency
   # In src/utils/helpers.py
   from src.etl.process import process_data
   
   # In src/etl/process.py
   from src.utils.helpers import helper_function
   ```

2. **Wildcard Imports**: Never use wildcard imports
   ```python
   # WRONG: Wildcard import
   from src.utils.constants import *
   
   # RIGHT: Explicit import
   from src.utils.constants import MAX_BATCH_SIZE, DEFAULT_ENCODING
   ```

3. **Direct Script Execution**: Always check for `__name__ == "__main__"` before running code
   ```python
   # At the end of executable scripts
   if __name__ == "__main__":
       main()
   ```

## Import Verification

Use the `check_imports.py` script to verify proper import structure:

```bash
python check_imports.py
```

If issues are found, use `fix_imports.py` to automatically fix common problems:

```bash
python fix_imports.py
```

## Update History

- **2025-05-05**: Added import verification tools
- **2025-03-15**: Added common issues section
- **2025-02-01**: Initial version created 