# BibleScholarProject Database Schema

This document outlines the database schema used in the BibleScholarProject. All tables are stored in the PostgreSQL database under the `bible_db` database.

## Schema Overview

The database uses the `bible` schema for all tables. The main schema components include:

1. **Bible Text Tables** - Core tables for storing Bible text in multiple languages and translations
2. **Lexicon Tables** - Hebrew and Greek lexical entries
3. **Word Analysis Tables** - Detailed word-level analysis including morphology and Strong's IDs
4. **Versification Tables** - Tables for managing different versification systems

## Core Tables

### Bible Text Tables

#### `bible.verses`

Stores the raw text of Bible verses from multiple translations.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| book_name | VARCHAR(50) | Full book name (e.g., "Genesis", "John") |
| chapter_num | INTEGER | Chapter number |
| verse_num | INTEGER | Verse number |
| verse_text | TEXT | Complete verse text |
| translation_source | VARCHAR(20) | Translation identifier (e.g., "KJV", "ASV", "TAGNT") |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Record update timestamp |

**Constraints:**
- Unique constraint on (book_name, chapter_num, verse_num, translation_source)

**Available Translations:**

| Translation | Description | Verse Count | Source Type |
|-------------|-------------|-------------|------------|
| KJV | King James Version (1611) | 31,100 | Public Domain |
| ASV | American Standard Version (1901) | 31,103 | Public Domain |
| ESV | English Standard Version | 4 | Licensed (sample only) |
| TAGNT | Translators Amalgamated Greek NT | 7,958 | Open License |
| TAHOT | Translators Amalgamated Hebrew OT | 23,261 | Open License |

#### `bible.translations`

Stores information about Bible translations.

| Column | Type | Description |
|--------|------|-------------|
| translation_id | SERIAL | Primary key |
| translation_code | VARCHAR | Short code identifier (e.g., "KJV", "ASV") |
| translation_name | VARCHAR | Full name of the translation |
| language | VARCHAR | Language of the translation |
| year | INTEGER | Year published |
| is_public_domain | BOOLEAN | Whether translation is public domain |
| license_info | TEXT | Licensing information if applicable |

### Lexicon Tables

#### `bible.hebrew_entries`

Hebrew lexicon entries.

| Column | Type | Description |
|--------|------|-------------|
| entry_id | SERIAL | Primary key |
| strongs_id | VARCHAR | Strong's ID (format: H1234) |
| lemma | VARCHAR | Hebrew lemma |
| transliteration | VARCHAR | Transliteration |
| definition | TEXT | Definition |
| usage | TEXT | Common usage |

#### `bible.greek_entries`

Greek lexicon entries.

| Column | Type | Description |
|--------|------|-------------|
| entry_id | SERIAL | Primary key |
| strongs_id | VARCHAR | Strong's ID (format: G1234) |
| lemma | VARCHAR | Greek lemma |
| transliteration | VARCHAR | Transliteration |
| definition | TEXT | Definition |
| usage | TEXT | Common usage |

### Word Analysis Tables

#### `bible.hebrew_ot_words`

Hebrew Old Testament words with morphological analysis.

| Column | Type | Description |
|--------|------|-------------|
| word_id | SERIAL | Primary key |
| verse_id | INTEGER | Foreign key to verses table |
| word_position | INTEGER | Position of word in verse |
| word_text | VARCHAR | Original Hebrew text |
| strongs_id | VARCHAR | Strong's ID (H1234) |
| grammar_code | VARCHAR | Grammar/morphology code |
| transliteration | VARCHAR | Transliteration |

#### `bible.greek_nt_words`

Greek New Testament words with morphological analysis.

| Column | Type | Description |
|--------|------|-------------|
| word_id | SERIAL | Primary key |
| verse_id | INTEGER | Foreign key to verses table |
| word_position | INTEGER | Position of word in verse |
| word_text | VARCHAR | Original Greek text |
| strongs_id | VARCHAR | Strong's ID (G1234) |
| grammar_code | VARCHAR | Grammar/morphology code |
| transliteration | VARCHAR | Transliteration |

### Versification Tables

#### `bible.versification_systems`

Versification systems metadata.

| Column | Type | Description |
|--------|------|-------------|
| system_id | SERIAL | Primary key |
| system_name | VARCHAR | Name of versification system |
| description | TEXT | Description of system |

#### `bible.verse_mappings`

Maps verses between different versification systems.

| Column | Type | Description |
|--------|------|-------------|
| mapping_id | SERIAL | Primary key |
| source_system_id | INTEGER | Foreign key to source versification system |
| target_system_id | INTEGER | Foreign key to target versification system |
| source_book | VARCHAR | Book name in source system |
| source_chapter | INTEGER | Chapter in source system |
| source_verse | INTEGER | Verse in source system |
| target_book | VARCHAR | Book name in target system |
| target_chapter | INTEGER | Chapter in target system |
| target_verse | INTEGER | Verse in target system |

## Critical Theological Term Constraints

For theological term analysis, the database must maintain minimum counts for critical terms:

| Term | Strong's ID | Minimum Required Count |
|------|------------|------------------------|
| Elohim | H430 | 2,600 |
| YHWH | H3068 | 6,000 |
| Adon | H113 | 335 |
| Chesed | H2617 | 248 |
| Aman | H539 | 100 |

## Database Access

Always use the connection utility from the database module:

```python
from src.database.connection import get_connection

def example_query():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bible.verses LIMIT 10")
        return cursor.fetchall()
```

## Schema Verification

The schema can be verified using the `check_db_schema.py` script:

```bash
python check_db_schema.py
```

## Translation Comparison Queries

To compare the same verse across different translations:

```sql
SELECT translation_source, verse_text
FROM bible.verses
WHERE book_name = 'John' AND chapter_num = 3 AND verse_num = 16
ORDER BY translation_source;
```

## Verse Count Verification

To verify the expected verse counts for each translation:

```sql
SELECT translation_source, COUNT(*) 
FROM bible.verses 
GROUP BY translation_source
ORDER BY translation_source;
```

Expected counts:
- KJV: 31,100
- ASV: 31,103
- TAGNT: 7,958
- TAHOT: 23,261 