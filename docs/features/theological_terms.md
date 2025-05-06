# Theological Terms

This document provides comprehensive documentation for the theological terms handling in the BibleScholarProject, focusing on critical Hebrew theological terms and their proper Strong's ID mappings.

*This document is complemented by the [theological_terms](.cursor/rules/features/theological_terms.mdc) cursor rule.*

## Overview

The BibleScholarProject places special emphasis on correctly identifying and mapping critical theological terms across Bible translations. Accurate Strong's ID mapping for these terms is essential for:

1. Theological analysis and comparison
2. Cross-language term mapping
3. Semantic search enhancements
4. Validation of translations' theological accuracy

## Technical Implementation

### Core Hebrew Theological Terms

These critical Hebrew theological terms must always have the correct Strong's ID mappings:

| Term | Hebrew | Strong's ID | Minimum Required Count | Current Status |
|------|--------|-------------|------------------------|----------------|
| Elohim | אלהים | H430 | 2,600 | 2,600+ (Valid) |
| YHWH | יהוה | H3068 | 6,000 | 6,525 (Valid) |
| Adon | אדון | H113 | 335 | 335+ (Valid) |
| Chesed | חסד | H2617 | 248 | 248+ (Valid) |
| Aman | אמן | H539 | 100 | 100+ (Valid) |

### Strong's ID Format Standards

#### Hebrew Strong's ID Formats

1. **Standard Format**: `H1234` - Basic Strong's ID with 'H' prefix and numeric identifier
2. **Extended Format**: `H1234a` - Strong's ID with letter suffix for distinguishing different words
3. **Database Storage**: Always store Strong's IDs in the dedicated `strongs_id` column, not embedded in `grammar_code`
4. **Validation**: All Strong's IDs should match entries in the `hebrew_entries` lexicon table
5. **Special Codes**: Special codes (H9xxx) used for grammatical constructs should be preserved

#### Grammar Code Formats

When Strong's IDs appear in grammar codes, they follow these patterns:

1. **Standard Pattern**: `{H1234}` - Enclosed in curly braces
2. **Extended Pattern**: `{H1234a}` - Extended ID enclosed in curly braces
3. **Prefix Pattern**: `H9001/{H1234}` - Special prefix code followed by ID in braces
4. **Alternate Pattern**: `{H1234}\H1234` - ID in braces followed by backslash and ID

### Database Integration

The theological terms system connects with these database tables:

1. `bible.hebrew_ot_words` - Contains Hebrew words with their Strong's IDs
2. `bible.hebrew_entries` - Hebrew lexicon entries with definitions
3. `bible.cross_language_terms` - Maps theological terms across languages
4. `bible.verses` - Biblical text containing the terms

### API Implementation

The system provides several API endpoints for theological term analysis:

1. `/api/theological_terms_report`: Provides a comprehensive report of all theological terms
   ```python
   @app.route('/api/theological_terms_report')
   def theological_terms_report():
       """Generate report of theological terms with counts and distribution."""
       with get_connection() as conn:
           cursor = conn.cursor()
           
           # Get critical terms data
           critical_terms = get_critical_terms()
           results = {}
           
           for strongs_id, info in critical_terms.items():
               # Get overall count
               cursor.execute(
                   "SELECT COUNT(*) FROM bible.hebrew_ot_words WHERE strongs_id = %s",
                   (strongs_id,)
               )
               total_count = cursor.fetchone()[0]
               
               # Get distribution by book
               cursor.execute("""
                   SELECT v.book_name, COUNT(*) as term_count
                   FROM bible.hebrew_ot_words w
                   JOIN bible.verses v ON w.verse_id = v.id
                   WHERE w.strongs_id = %s
                   GROUP BY v.book_name
                   ORDER BY COUNT(*) DESC
               """, (strongs_id,))
               
               book_distribution = cursor.fetchall()
               
               # Add to results
               results[strongs_id] = {
                   "name": info["name"],
                   "hebrew": info.get("hebrew", ""),
                   "min_count": info["min_count"],
                   "total_count": total_count,
                   "book_distribution": book_distribution,
                   "is_valid": total_count >= info["min_count"]
               }
               
           return jsonify(results)
   ```

2. `/api/lexicon/hebrew/validate_critical_terms`: Validates that all critical terms meet minimum count requirements
3. `/api/cross_language/terms`: Maps theological terms across languages (Hebrew-Greek-Arabic)

## Data Processing

### Extracting Strong's IDs from Grammar Code

```python
# Pattern for extracting Strong's IDs from grammar_code
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

### Validating Critical Term Counts

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

### Processing Steps

1. All ETL processes for Hebrew text must ensure Strong's IDs are extracted from `grammar_code` and placed in `strongs_id`
2. Database validation must confirm minimum counts for critical theological terms
3. After data loading, always run the proper Strong's ID extraction and validation scripts:
   - `src/etl/fix_hebrew_strongs_ids.py`
   - `scripts/check_related_hebrew_words.py`

## Usage Examples

### API Usage

```python
import requests

# Get theological terms report
response = requests.get("http://localhost:5000/api/theological_terms_report")
terms_report = response.json()

# Validate critical terms
response = requests.get("http://localhost:5000/api/lexicon/hebrew/validate_critical_terms")
validation_result = response.json()

# Get cross-language term mappings
response = requests.get("http://localhost:5000/api/cross_language/terms")
cross_language_terms = response.json()
```

### Database Query Examples

```python
# Count occurrences of a specific theological term
with get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) 
        FROM bible.hebrew_ot_words 
        WHERE strongs_id = 'H430'
    """)
    elohim_count = cursor.fetchone()[0]
    print(f"Elohim (H430) occurs {elohim_count} times")

# Get distribution of YHWH by book
with get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.book_name, COUNT(*) as yhwh_count
        FROM bible.hebrew_ot_words w
        JOIN bible.verses v ON w.verse_id = v.id
        WHERE w.strongs_id = 'H3068'
        GROUP BY v.book_name
        ORDER BY COUNT(*) DESC
    """)
    book_distribution = cursor.fetchall()
    for book, count in book_distribution:
        print(f"{book}: {count}")
```

### Web Interface

The web interface provides the following views for theological terms:

1. `/theological_terms_report`: Web view of the theological terms report
2. `/hebrew_terms_validation`: Validation report for Hebrew theological terms
3. `/cross_language`: Cross-language view of theological terms

## Troubleshooting

### Common Issues

1. **Missing Strong's IDs**
   - Ensure `fix_hebrew_strongs_ids.py` has been run
   - Check for malformed grammar codes that don't match extraction patterns
   - Verify lexicon table contains the expected Strong's IDs

2. **Count Discrepancies**
   - Compare counts with reference sources (e.g., STEP Bible)
   - Check for missing verses or books in the database
   - Ensure all translations are properly processed

3. **Cross-Language Mapping Issues**
   - Verify cross-language terms table is populated
   - Check for correct joining keys between tables
   - Ensure proper handling of character encoding for non-Latin scripts

## Related Documentation

- [Hebrew Rules](../rules/hebrew_rules.md) - Special handling for Hebrew text
- [Database Schema](../reference/DATABASE_SCHEMA.md) - Database structure details
- [API Reference](../reference/API_REFERENCE.md) - Complete API documentation

## Modification History

| Date | Change | Author |
|------|--------|--------|
| 2025-05-06 | Consolidated theological terms documentation | BibleScholar Team |
| 2025-05-05 | Updated with current term counts from database verification | BibleScholar Team |
| 2025-04-15 | Added API and web interface integration details | BibleScholar Team |
| 2025-03-10 | Added pattern for properly handling extended Strong's IDs | BibleScholar Team |
| 2025-02-20 | Initial version created | BibleScholar Team | 