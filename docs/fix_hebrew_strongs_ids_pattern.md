# Hebrew Strong's ID Fixing Pattern

## Overview

This document describes the specific pattern and workflow for successfully fixing Hebrew Strong's IDs in the BibleScholarProject.

## Common Issues with Hebrew Strong's IDs

The project has encountered several consistent issues with Hebrew Strong's IDs:

1. Missing Strong's IDs in the `strongs_id` column despite presence in `grammar_code`
2. Inconsistent format with some IDs stored as H0430 and others as H430
3. Special case handling needed for critical theological terms
4. Extended Strong's IDs (with letter suffixes) not matching lexicon entries

## Fix Pattern

The proper approach to fixing Hebrew Strong's IDs follows this pattern:

### 1. Check schema and column names first

```python
def check_schema_before_fixing(conn):
    """Check if the table schema matches expected columns before fixing."""
    with conn.cursor() as cursor:
        # Check hebrew_entries columns
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = 'bible' AND table_name = 'hebrew_entries'
            ORDER BY ordinal_position
        """)
        hebrew_entries_columns = [row[0] for row in cursor.fetchall()]
        
        # Check hebrew_ot_words columns
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = 'bible' AND table_name = 'hebrew_ot_words'
            ORDER BY ordinal_position
        """)
        hebrew_ot_words_columns = [row[0] for row in cursor.fetchall()]
        
        # Print the actual schema for debugging
        logger.debug(f"hebrew_entries columns: {hebrew_entries_columns}")
        logger.debug(f"hebrew_ot_words columns: {hebrew_ot_words_columns}")
        
        # Verify critical columns exist
        required_entries_columns = ['strongs_id', 'hebrew_word'] 
        required_words_columns = ['strongs_id', 'grammar_code', 'word_text']
        
        if not all(col in hebrew_entries_columns for col in required_entries_columns):
            logger.error(f"Missing required columns in hebrew_entries: {required_entries_columns}")
            return False
            
        if not all(col in hebrew_ot_words_columns for col in required_words_columns):
            logger.error(f"Missing required columns in hebrew_ot_words: {required_words_columns}")
            return False
            
        return True
```

### 2. Extract Strong's IDs from grammar_code

Use regular expressions to extract Strong's IDs from grammar codes:

```python
def extract_strongs_from_grammar(grammar_code):
    """Extract Strong's ID from grammar code patterns."""
    if not grammar_code:
        return None
        
    # Try various patterns in priority order
    patterns = [
        r'\{(H\d+[A-Za-z]?)\}',  # Standard format {H1234} or {H1234A}
        r'(H\d+[A-Za-z]?)/',     # Prefix format H1234/
        r'\\(H\d+[A-Za-z]?)',    # Alternate format \H1234
    ]
    
    for pattern in patterns:
        match = re.search(pattern, grammar_code)
        if match:
            return match.group(1)
            
    return None
```

### 3. Special handling for critical theological terms

Always explicitly handle critical theological terms:

```python
def handle_critical_terms(conn):
    """Handle critical theological terms with special care."""
    critical_terms = {
        "H430": {"hebrew": "אלהים", "min_count": 2600},
        "H3068": {"hebrew": "יהוה", "min_count": 6000},
        "H113": {"hebrew": "אדון", "min_count": 335},
        "H2617": {"hebrew": "חסד", "min_count": 248},
        "H539": {"hebrew": "אמן", "min_count": 100}
    }
    
    with conn.cursor() as cursor:
        for strongs_id, info in critical_terms.items():
            # Check current count
            cursor.execute(
                "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id = %s",
                (strongs_id,)
            )
            count = cursor.fetchone()[0]
            
            if count < info["min_count"]:
                # Direct word mapping for critical terms
                cursor.execute(
                    """
                    UPDATE bible.hebrew_ot_words
                    SET strongs_id = %s
                    WHERE word_text = %s AND (strongs_id IS NULL OR strongs_id != %s)
                    """,
                    (strongs_id, info["hebrew"], strongs_id)
                )
                
                updated = cursor.rowcount
                logger.info(f"Updated {updated} occurrences of {info['hebrew']} ({strongs_id})")
```

### 4. Always validate results after fixing

```python
def validate_fixes(conn):
    """Validate the fixes by checking counts of critical terms."""
    critical_terms = {
        "H430": {"name": "Elohim", "min_count": 2600},
        "H3068": {"name": "YHWH", "min_count": 6000},
        "H113": {"name": "Adon", "min_count": 335},
        "H2617": {"name": "Chesed", "min_count": 248},
        "H539": {"name": "Aman", "min_count": 100}
    }
    
    with conn.cursor() as cursor:
        for strongs_id, info in critical_terms.items():
            cursor.execute(
                "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id = %s",
                (strongs_id,)
            )
            count = cursor.fetchone()[0]
            
            if count < info["min_count"]:
                logger.warning(f"Low count for {info['name']} ({strongs_id}): {count} < {info['min_count']}")
            else:
                logger.info(f"Validated {info['name']} ({strongs_id}): {count} occurrences")
```

## Running the Fix Process

The fix should be run in this order:

1. Check schema compatibility
2. Extract and update Strong's IDs from grammar_code
3. Handle critical theological terms separately
4. Validate results
5. Generate a summary report

Always ensure tables exist using `check_table_exists` before any operations. 