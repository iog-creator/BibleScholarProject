# Bible Scholar Project - Data Verification

This document outlines the comprehensive approach to data verification in the Bible Scholar Project. Ensuring data accuracy and integrity is critical when dealing with biblical texts and theological content.

## Verification Levels

The project implements a multi-level verification approach:

1. **Raw Data Validation** - Verifying source files from STEPBible
2. **ETL Process Validation** - Ensuring data is correctly transformed and loaded
3. **Database Integrity Validation** - Checking database constraints and relationships
4. **Theological Term Validation** - Verifying accurate representation of key theological terms
5. **Cross-Reference Validation** - Ensuring proper linking between related content

## Verification Tools

### verify_data_processing.py

The primary verification script (`verify_data_processing.py`) performs comprehensive checks across all levels of data validation. It can be run with:

```bash
python verify_data_processing.py [--theological] [--books=Book1,Book2] [--verbose]
```

Options:
- `--theological` - Run focused theological term validation
- `--books` - Verify only specific books (comma-separated)
- `--verbose` - Display detailed output for each verification step

### Verification Components

#### 1. Statistical Verification

Ensures expected counts match actual data:

- **Books**: 66 books (39 OT + 27 NT)
- **Verses**: ~31,102 verses
- **Hebrew Words**: ~306,757 total words, ~8,674 unique words
- **Greek Words**: ~138,162 total words, ~5,437 unique words
- **Strong's IDs**: ~8,674 Hebrew Strong's IDs, ~5,624 Greek Strong's IDs

#### 2. Theological Term Verification

Tests the accurate representation of key theological terms:

**Hebrew Terms**:
- יהוה (YHWH/LORD) - H3068: ~6,828 occurrences
- אלהים (Elohim/God) - H430: ~2,600 occurrences
- משיח (Mashiach/Messiah) - H4899: ~39 occurrences
- אדון (Adon/Lord) - H113: ~335 occurrences
- רוח (Ruach/Spirit) - H7307: ~378 occurrences

**Greek Terms**:
- θεός (Theos/God) - G2316: ~1,300+ occurrences
- κύριος (Kyrios/Lord) - G2962: ~720+ occurrences
- χριστός (Christos/Christ) - G5547: ~529 occurrences
- πνεῦμα (Pneuma/Spirit) - G4151: ~379 occurrences
- πίστις (Pistis/Faith) - G4102: ~243 occurrences

#### 3. Critical Passage Verification

Verifies the integrity of theologically significant passages:

**Old Testament**:
- Genesis 1:1-3 (Creation narrative)
- Exodus 3:14-15 (I AM WHO I AM)
- Deuteronomy 6:4-5 (Shema)
- Isaiah 7:14, 9:6-7, 53:1-12 (Messianic prophecies)
- Psalm 22 (Messianic psalm)

**New Testament**:
- John 1:1-18 (Word becoming flesh)
- Romans 3:21-26 (Justification by faith)
- 1 Corinthians 15:1-8 (Resurrection account)
- Philippians 2:5-11 (Christ's humiliation and exaltation)
- Hebrews 1:1-4 (Supremacy of Christ)

#### 4. Linguistic Verification

Ensures proper linguistic representation:

- Hebrew morphology codes match expected patterns
- Greek grammar codes are properly formatted
- Word counts in each verse match between source and database
- Strong's IDs are correctly mapped to words

## Database Validation Queries

The verification process includes these database checks:

```sql
-- Verify book counts
SELECT COUNT(*) FROM bible.books;

-- Verify verse counts by testament
SELECT b.testament, COUNT(v.id) FROM bible.verses v
JOIN bible.books b ON v.book_name = b.name
GROUP BY b.testament;

-- Verify Hebrew word counts
SELECT COUNT(*) FROM bible.hebrew_ot_words;

-- Verify Greek word counts
SELECT COUNT(*) FROM bible.greek_nt_words;

-- Verify key theological terms
SELECT strongs_id, COUNT(*) FROM bible.hebrew_ot_words
WHERE strongs_id IN ('H3068', 'H430', 'H4899', 'H113', 'H7307')
GROUP BY strongs_id;
```

## Verification Reports

The verification process generates detailed reports:

1. **Summary Report** - Overall verification status with counts and statistics
2. **Theological Terms Report** - Focused validation of key theological terms
3. **Error Report** - Detailed list of any verification failures
4. **Database Statistics Report** - Comprehensive database metrics

## Adding New Verifications

To add new theological terms to verify:

1. Edit the `THEOLOGICAL_TERMS` dictionary in the verification script
2. Provide the term, Strong's ID, and expected minimum occurrence count
3. Add any associated passages that should be checked for this term

Example:
```python
THEOLOGICAL_TERMS = {
    "hebrew": {
        "ברית": {"strongs_id": "H1285", "min_occurrences": 280},  # Covenant
        ...
    }
}

CRITICAL_PASSAGES = {
    "Genesis 15:18": ["H1285"],  # Covenant with Abraham
    ...
}
```

## Theological Testing Guidelines

When verifying theological content:

1. **Textual Accuracy**: Prioritize fidelity to the original text
2. **Term Consistency**: Ensure theological terms are consistently tagged
3. **Contextual Sensitivity**: Verify terms within their proper contexts
4. **Cross-Language Correspondence**: Check term mapping across languages

## Continuous Verification

The verification process is integrated into the CI/CD pipeline to ensure continuous data quality:

1. Pre-ETL verification of source data formats
2. Post-ETL verification of data transformation accuracy 
3. Database schema and constraint validation
4. API response validation through integration tests

## Future Enhancements

As documented in `TODO.md`, planned verification improvements include:

1. Adding more theological terms to verify
2. Implementing HTML report output for verification results
3. Adding visualizations of term distributions
4. Enhancing cross-language verification between Hebrew, Greek, and Arabic
5. Improving detection of extended Strong's IDs 