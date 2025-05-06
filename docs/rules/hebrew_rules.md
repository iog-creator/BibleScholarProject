# Hebrew Text Handling Rules

## Core Hebrew Theological Terms

These critical Hebrew theological terms must always have the correct Strong's ID mappings:

| Term | Hebrew | Strong's ID | Minimum Required Count | Current Status |
|------|--------|-------------|------------------------|----------------|
| Elohim | אלהים | H430 | 2,600 | 2,600+ (Valid) |
| YHWH | יהוה | H3068 | 6,000 | 6,525 (Valid) |
| Adon | אדון | H113 | 335 | 335+ (Valid) |
| Chesed | חסד | H2617 | 248 | 248+ (Valid) |
| Aman | אמן | H539 | 100 | 100+ (Valid) |

These terms are critical for theological analysis and must be properly mapped. The minimum counts are based on scholarly consensus of expected frequencies in the Hebrew Bible.

## Strong's ID Format Standards

### Hebrew Strong's ID Formats

1. **Standard Format**: `H1234` - Basic Strong's ID with 'H' prefix and numeric identifier
2. **Extended Format**: `H1234a` - Strong's ID with letter suffix for distinguishing different words
3. **Database Storage**: Always store Strong's IDs in the dedicated `strongs_id` column, not embedded in `grammar_code`
4. **Validation**: All Strong's IDs should match entries in the `hebrew_entries` lexicon table
5. **Special Codes**: Special codes (H9xxx) used for grammatical constructs should be preserved

### Grammar Code Formats

When Strong's IDs appear in grammar codes, they follow these patterns:

1. **Standard Pattern**: `{H1234}` - Enclosed in curly braces
2. **Extended Pattern**: `{H1234a}` - Extended ID enclosed in curly braces
3. **Prefix Pattern**: `H9001/{H1234}` - Special prefix code followed by ID in braces
4. **Alternate Pattern**: `{H1234}\H1234` - ID in braces followed by backslash and ID

## Hebrew Text Processing

### Handling Vowel Points

When processing Hebrew text:
1. Store unpointed text in separate columns from pointed text
2. Preserve original pointing in the `word_with_points` column
3. Store simplified unpointed text in the `word` column for easier searching
4. Index both columns for efficient querying

Example:
```python
def process_hebrew_word(word_with_points):
    # Remove vowel points for simplified storage
    unpointed_word = remove_hebrew_points(word_with_points)
    
    return {
        'word': unpointed_word,
        'word_with_points': word_with_points
    }
```

### Right-to-Left Text Handling

1. Always store Hebrew text in its native right-to-left format
2. In HTML templates, use the `dir="rtl"` attribute for Hebrew text
3. When displaying Hebrew alongside English, use appropriate CSS to handle bidirectional text

Example HTML:
```html
<div class="hebrew-text" dir="rtl">
    אלהים
</div>
```

## Strong's ID Extraction

Use the following pattern to extract Strong's IDs from grammar code fields:

```python
import re

def extract_strongs_id(grammar_code):
    """Extract Strong's ID from grammar_code field."""
    if not grammar_code:
        return None
        
    # Try standard pattern in curly braces
    match = re.search(r'\{(H[0-9]+[A-Za-z]?)\}', grammar_code)
    if match:
        return match.group(1)
        
    # Try prefix pattern
    match = re.search(r'H[0-9]+/\{(H[0-9]+)\}', grammar_code)
    if match:
        return match.group(1)
        
    # Try alternate pattern
    match = re.search(r'\{(H[0-9]+)\}\\H[0-9]+', grammar_code)
    if match:
        return match.group(1)
        
    return None
```

## Handling Extended Strong's IDs

Some Hebrew words have extended Strong's IDs with letter suffixes (e.g., H1234a) to distinguish between different words with the same base ID. These extended IDs require special handling:

```python
def get_base_strongs_id(extended_id):
    """Extract the base Strong's ID from an extended ID."""
    if not extended_id:
        return None
    
    # Match the base ID pattern (remove letter suffix if present)
    match = re.match(r'(H[0-9]+)[a-z]?', extended_id)
    if match:
        return match.group(1)
    
    return extended_id
```

## Critical Theological Term Validation

Use this pattern to validate critical theological terms:

```python
def validate_critical_terms(conn):
    """Validate minimum counts of critical theological terms."""
    critical_terms = {
        "H430": {"name": "Elohim", "min_count": 2600},
        "H3068": {"name": "YHWH", "min_count": 6000},
        "H113": {"name": "Adon", "min_count": 335},
        "H2617": {"name": "Chesed", "min_count": 248},
        "H539": {"name": "Aman", "min_count": 100}
    }
    
    cursor = conn.cursor()
    all_valid = True
    
    for strongs_id, info in critical_terms.items():
        cursor.execute(
            "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id = %s",
            (strongs_id,)
        )
        count = cursor.fetchone()[0]
        
        if count < info["min_count"]:
            print(f"Error: {info['name']} ({strongs_id}) has only {count} occurrences, expected {info['min_count']}")
            all_valid = False
        else:
            print(f"Valid: {info['name']} ({strongs_id}) has {count} occurrences")
    
    return all_valid
```

## Hebrew Word Analysis

When performing analysis on Hebrew words:

1. Always account for inflected forms of the same lexical root
2. Consider prefixed and suffixed forms in word searches
3. Link words back to their lexical entries
4. Include contextual examples in reports
5. For theological terms, provide distribution statistics by book

Example query for word distribution by book:
```sql
SELECT 
    b.name AS book_name, 
    COUNT(*) AS word_count
FROM 
    bible.hebrew_ot_words w
JOIN 
    bible.verses v ON w.verse_id = v.id
JOIN
    bible.books b ON v.book_name = b.name
WHERE 
    w.strongs_id = 'H3068'  -- YHWH
GROUP BY 
    b.name
ORDER BY 
    b.book_order;
```

## Update History

- **2025-05-05**: Updated term counts based on current database validation
- **2025-04-10**: Added Hebrew right-to-left text handling
- **2025-03-01**: Added extended Strong's ID handling
- **2025-02-01**: Initial version created 