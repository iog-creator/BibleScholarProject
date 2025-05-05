# BibleScholarProject Column Naming Rules

## Overview

This document describes the column naming conventions and actual column names for key tables in the BibleScholarProject database.

## Table Schema Reference

### bible.hebrew_entries Table

| Column Name      | Data Type | Description                               |
|------------------|-----------|-------------------------------------------|
| strongs_id       | TEXT      | Primary Strong's ID (e.g., H0430)         |
| extended_strongs | TEXT      | Extended Strong's ID with variant letter  |
| hebrew_word      | TEXT      | Original Hebrew word                      |
| transliteration  | TEXT      | Transliteration of Hebrew word            |
| pos              | TEXT      | Part of speech with detailed morphology   |
| gloss            | TEXT      | Brief English gloss term                  |
| definition       | TEXT      | Full definition and usage notes           |
| created_at       | TIMESTAMP | Creation timestamp                        |
| updated_at       | TIMESTAMP | Last update timestamp                     |

**Note:** This differs from the table creation in init_database.py, which used `word_text` and `part_of_speech`. Be sure to match existing column names.

### bible.hebrew_ot_words Table

| Column Name         | Data Type | Description                              |
|---------------------|-----------|------------------------------------------|
| book_name           | TEXT      | Bible book name                          |
| chapter_num         | INTEGER   | Chapter number                           |
| verse_num           | INTEGER   | Verse number                             |
| word_num            | INTEGER   | Word position in verse                   |
| word_text           | TEXT      | Hebrew word as text                      |
| strongs_id          | TEXT      | Strong's ID reference                    |
| grammar_code        | TEXT      | Original grammar code from source        |
| word_transliteration | TEXT     | Transliteration of Hebrew word           |
| translation         | TEXT      | English translation of word              |

### bible.cross_language_terms Table

| Column Name          | Data Type | Description                             |
|----------------------|-----------|-----------------------------------------|
| term_key             | TEXT      | Unique identifier for concept           |
| hebrew_strongs_id    | TEXT      | Hebrew Strong's ID                      |
| greek_strongs_id     | TEXT      | Greek Strong's ID                       |
| arabic_term          | TEXT      | Arabic equivalent term                  |
| theological_category | TEXT      | Category for grouping terms             |
| equivalent_type      | TEXT      | Matching type (exact, partial, etc.)    |
| notes                | TEXT      | Additional information about mapping    |

## Column Naming Conventions

1. Use `snake_case` for all column names
2. Use consistent suffixes:
   - `_id` for identifiers
   - `_name` for names
   - `_num` for numbers
   - `_code` for coded values
   - `_text` for full-text content
   - `_at` for timestamps

3. When referencing columns in queries, use the table name prefix:
   ```sql
   SELECT hebrew_ot_words.strongs_id, hebrew_entries.hebrew_word
   FROM bible.hebrew_ot_words
   JOIN bible.hebrew_entries ON hebrew_ot_words.strongs_id = hebrew_entries.strongs_id
   ```

## Critical Strong's IDs Column Reference

When working with critical theological Strong's IDs, these are the correct column mappings:

| Strong's ID | Hebrew word | transliteration | gloss |
|-------------|-------------|-----------------|-------|
| H430        | אלהים       | elohim          | God   |
| H3068       | יהוה        | YHWH            | LORD  |
| H113        | אדון        | adon            | lord  |
| H2617       | חסד         | chesed          | lovingkindness |
| H539        | אמן         | aman            | believe | 