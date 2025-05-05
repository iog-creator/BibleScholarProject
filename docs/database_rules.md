# BibleScholarProject Database Rules

## Overview

This document describes the database access patterns and rules for the BibleScholarProject.

## Database Connection

Always use the centralized database connection module:

```python
from src.database.connection import get_db_connection

def my_function():
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return
    
    try:
        # Use connection...
    finally:
        conn.close()
```

## Schema and Table Conventions

1. All application tables should be in the `bible` schema
2. Always check if tables exist before attempting operations:
   ```python
   from src.database.connection import check_table_exists
   
   if not check_table_exists(conn, 'bible', 'hebrew_ot_words'):
       logger.error("Required table does not exist")
       return
   ```

3. Table naming conventions:
   - Use lowercase snake_case for table names
   - Use singular for reference tables (e.g., `hebrew_entry`)
   - Use plural for data tables (e.g., `hebrew_ot_words`)

## Hebrew Strong's IDs

1. Hebrew Strong's IDs follow the format `HNNNN` where `NNNN` is a number (e.g., `H0430`)
2. Extended IDs may have a letter suffix (e.g., `H0430a`)
3. When querying, use case-insensitive comparison:
   ```sql
   SELECT * FROM bible.hebrew_entries WHERE LOWER(strongs_id) = LOWER('H0430')
   ```

4. Critical theological terms with their expected minimum counts:
   - H430 (Elohim): 2600+ occurrences
   - H3068 (YHWH): 6000+ occurrences
   - H113 (Adon): 335+ occurrences
   - H2617 (Chesed): 248+ occurrences
   - H539 (Aman): 100+ occurrences

## Error Handling

Always use transactions and proper error handling:

```python
try:
    cursor = conn.cursor()
    # Database operations...
    conn.commit()
except Exception as e:
    conn.rollback()
    logger.error(f"Database error: {e}")
finally:
    cursor.close()
```

## SQL Query Best Practices

1. Use parameterized queries to prevent SQL injection:
   ```python
   cursor.execute("SELECT * FROM bible.verses WHERE book_name = %s", (book_name,))
   ```

2. For large batch inserts, use `execute_values`:
   ```python
   from psycopg2.extras import execute_values
   
   values = [(1, 'Gen', 1, 1), (2, 'Gen', 1, 2)]
   execute_values(
       cursor,
       "INSERT INTO bible.verses (id, book_name, chapter_num, verse_num) VALUES %s",
       values
   )
   ```

3. Use explicit schema references in all queries:
   ```sql
   SELECT * FROM bible.verses -- Good
   ```
   instead of:
   ```sql
   SELECT * FROM verses -- Avoid
   ``` 