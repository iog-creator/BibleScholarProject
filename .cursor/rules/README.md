# Cursor Rules Summary

This directory contains all Cursor rules for the BibleScholarProject. Each rule specifies standards for code, data processing, and AI training data logging.

## Rule List

### 1. DSPy Training Data Logging (`etl_rules.mdc`)
- **Scope:** All ETL and API scripts that process, transform, or expose data relevant for AI model training.
- **When to Apply:**
  - Apply in every ETL/API script that handles Bible text, lexicon, morphology, or proper names data.
  - Do NOT apply in scripts that only handle system admin, user authentication, or sensitive data.
- **How to Apply:**
  - For each processed data item (word, verse, entry, API response), log a training example to the appropriate `.jsonl` file in `data/processed/dspy_training_data/`.
  - Use the schema: `{ "context": ..., "labels": ..., "metadata": ... }`.
- **Example:**
  ```python
  context = f"{word['book_name']} {word['chapter_num']}:{word['verse_num']} {word['word_text']}"
  labels = {'strongs_id': word['strongs_id'], 'lemma': word['word_text'], 'morphology': word['grammar_code']}
  metadata = {'verse_ref': verse_ref, 'word_num': word['word_num']}
  append_dspy_training_example('data/processed/dspy_training_data/hebrew_ot_tagging.jsonl', context, labels, metadata)
  ```
- **Incorrect Application:**
  - Logging user credentials, passwords, or connection strings.
  - Logging data from admin-only or non-training-related scripts.

### 2. Database Access (`database_access.mdc`)
- **Scope:** All code that connects to or queries the database.
- **When to Apply:**
  - Always use the connection utility from the database module.
  - Never log sensitive information in DSPy training data.
- **How to Apply:**
  - Use `get_db_connection()` for all database access.
  - Do not include sensitive fields in `context` or `labels` when logging training data.

## References
- See each `.mdc` file for detailed rule text and examples.
- [DSPy Programming Overview](https://dspy.ai/learn/programming/overview/)

## Available Rules

The following rule files provide guidance for various aspects of the project:

1. **import_rules.md** - Standard import patterns for Python modules
2. **database_rules.md** - Database access patterns and schema conventions
3. **etl_rules.md** - ETL (Extract, Transform, Load) process patterns
4. **compatibility_rules.md** - Cross-platform compatibility guidelines
5. **column_names.md** - Database column name references
6. **fix_hebrew_strongs_ids_pattern.md** - Specific pattern for fixing Hebrew Strong's IDs

## Using These Rules

These rules should be referenced when:

1. Creating new modules or scripts
2. Modifying existing code
3. Working with the database
4. Implementing ETL processes
5. Making code compatible across platforms

The rules were created to address specific issues encountered in the project, including import path problems and database schema mismatches.

## Implementation

Rules in this directory are automatically applied by Cursor AI when suggesting or modifying code to ensure consistency across the project. 