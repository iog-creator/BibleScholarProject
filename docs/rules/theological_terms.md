# Theological Terms Standardization Guidelines

## Core Hebrew Theological Terms

These critical Hebrew theological terms must always have the correct Strong's ID mappings:

| Term | Hebrew | Strong's ID | Minimum Required Count | Current Status |
|------|--------|-------------|------------------------|----------------|
| Elohim | אלהים | H430 | 2,600 | 2,600+ (Valid) |
| YHWH | יהוה | H3068 | 6,000 | 6,525 (Valid) |
| Adon | אדון | H113 | 335 | 335+ (Valid) |
| Chesed | חסד | H2617 | 248 | 248+ (Valid) |
| Aman | אמן | H539 | 100 | 100+ (Valid) |

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

## Data Processing Requirements

1. All ETL processes for Hebrew text must ensure Strong's IDs are extracted from `grammar_code` and placed in `strongs_id`
2. Database validation must confirm minimum counts for critical theological terms
3. After data loading, always run the proper Strong's ID extraction and validation scripts:
   - `src/etl/fix_hebrew_strongs_ids.py`
   - `scripts/check_related_hebrew_words.py`

## Theological Term Reporting

1. API endpoints should provide specific access to theological term occurrences 
2. Theological term reports should include:
   - Total count of occurrences
   - Book distribution statistics
   - Related words/terms with semantic connections
   - Contextual analysis of surrounding words

## Code Patterns for Strong's ID Processing

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

## Implementation in API and Web Interface

### API Endpoints

The following API endpoints are available for theological term analysis:

1. `/api/theological_terms_report`: Provides a comprehensive report of all theological terms
2. `/api/lexicon/hebrew/validate_critical_terms`: Validates that all critical terms meet minimum count requirements
3. `/api/cross_language/terms`: Maps theological terms across languages (Hebrew-Greek-Arabic)

### Web Interface Integration

The web interface provides the following views for theological terms:

1. `/theological_terms_report`: Web view of the theological terms report
2. `/hebrew_terms_validation`: Validation report for Hebrew theological terms
3. `/cross_language`: Cross-language view of theological terms

## Documentation Requirements

All theological term processing must be documented in:

1. Code comments explaining the significance of terms being processed
2. Log entries for any modifications to theological term mappings
3. Verification reports showing final counts of critical terms
4. Documentation files explaining the theological importance of term mapping

## Update History

- **2025-05-05**: Updated with current term counts from database verification
- **2025-04-15**: Added API and web interface integration details
- **2025-03-10**: Added pattern for properly handling extended Strong's IDs
- **2025-02-20**: Initial version created 