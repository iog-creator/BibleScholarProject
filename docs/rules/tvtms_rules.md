# TVTMS Versification Rules

## Data Source Authority

> **⚠️ Important: Only `data/raw/TVTMS_expanded.txt` is the authoritative source for versification mappings in the ETL pipeline.**
> 
> Do **not** use the `.tsv` file for ETL or integration. The `.tsv` is for reference or manual inspection only.

## File Format

The TVTMS data must follow this format:

1. **Column Headers**: `SourceType, SourceRef, StandardRef, Action, NoteMarker, NoteA, NoteB, Ancient Versions, Tests`
2. **Separator**: Tab-separated values in the `.txt` file
3. **Expected Count**: Approximately 1,786 versification mappings (current count)
4. **Book Coverage**: Must include at least 80% of biblical books; warning if below 90%

## Versification Traditions

The system supports these versification traditions:

1. **English** (default)
2. **Hebrew**
3. **Greek** (LXX)
4. **Latin** (Vulgate)
5. **Aramaic**
6. **Syriac**

## Mapping Types

The following mapping types are supported in the `Action` column:

1. `Psalm title`
2. `Missing verse`
3. `Merged verse`
4. `Split verse`
5. `Chapter difference`
6. `Different verse order`
7. `Alternative versification`

## Database Handling

When working with the database tables for versification:

1. Always ensure fields that represent numeric values (chapters, verses) are properly typed or cast:
   ```sql
   SELECT * FROM bible.versification_mappings
   WHERE source_chapter::integer = 3 AND source_verse::integer = 0;
   ```

2. Always handle both source and target traditions:
   ```python
   def get_mapping(source_tradition, source_ref, target_tradition):
       """Get mapping between versification traditions."""
       cursor = conn.cursor()
       cursor.execute(
           """
           SELECT * FROM bible.versification_mappings
           WHERE source_tradition = %s 
           AND source_book = %s
           AND source_chapter = %s
           AND source_verse = %s
           AND target_tradition = %s
           """,
           (source_tradition, source_ref.book, source_ref.chapter, source_ref.verse, target_tradition)
       )
       return cursor.fetchone()
   ```

## Special Cases

The versification system must correctly handle these special cases:

1. **Psalm Titles**: Represented as verse 0 (e.g., Psalm 3:0)
2. **Missing Verses**: Properly mapped to the closest equivalent
3. **3 John 1:15**: Special case in some traditions vs. 3 John 1:14 in others
4. **Split Chapters**: When one chapter in a tradition maps to multiple chapters in another
5. **Merged Verses**: When verses are combined in different traditions

Example:
```python
def handle_psalm_title(psalm_number):
    """Special handling for psalm titles."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM bible.versification_mappings
        WHERE source_book = 'Psa'
        AND source_chapter::integer = %s
        AND source_verse::integer = 0
        """,
        (psalm_number,)
    )
    return cursor.fetchone()
```

## TVTMS Parser Configuration

The TVTMSParser should follow these rules:

1. **Default Strictness**: Use `tolerant` mode for production
2. **Use Explicit Types**: Convert numeric string fields to integers
3. **Handle Unicode**: Properly process Unicode in book names and notes
4. **Validate Mappings**: Always validate mappings against known traditions and books

Example parser initialization:
```python
from src.tvtms.parser import TVTMSParser

parser = TVTMSParser(
    strictness="tolerant",
    validate_books=True,
    convert_types=True
)
mappings = parser.parse_file("data/raw/TVTMS_expanded.txt")
```

## Integration Testing

When testing TVTMS integrations:

1. Use sample files with the correct format
2. Test all mapping types
3. Verify special cases explicitly
4. Check for proper error handling with malformed data

Example test:
```python
def test_psalm_title_mapping():
    """Test proper handling of psalm titles (verse 0)."""
    conn = get_test_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM bible.versification_mappings
        WHERE source_book = 'Psa'
        AND source_chapter::integer = 3
        AND source_verse::integer = 0
        """
    )
    mapping = cursor.fetchone()
    assert mapping is not None, "Psalm 3:0 mapping should exist"
    assert mapping['mapping_type'] == 'Psalm title'
```

## Update History

- **2025-05-05**: Updated expected mapping count to 1,786
- **2025-04-10**: Added special case handling
- **2025-03-01**: Added parser configuration guidelines
- **2025-02-01**: Initial version created 