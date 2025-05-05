# BibleScholarProject Cursor Rules

This directory contains Cursor Rules for the BibleScholarProject. These rules provide consistent patterns, guidance, and standards for working with the codebase.

## What are Cursor Rules?

Cursor Rules are scoped instructions that can be attached to specific files or referenced manually. They help maintain consistency across the project and provide relevant context to AI assistants when working with specific parts of the codebase.

## Rule Structure

Each rule file is written in **MDC** (`.mdc`), a lightweight format that supports metadata and content in a single file. The structure consists of:

```
---
description: Brief description of what the rule does
globs: 
  - "pattern/to/match/*.py"
  - "other/pattern/*.js"
alwaysApply: false
---

# Rule Title

Rule content goes here...

@referenced_file.py
```

### Rule Types

| Rule Type       | Description                                                                                  |
| --------------- | -------------------------------------------------------------------------------------------- |
| Always          | Always included in the model context (set `alwaysApply: true`)                                |
| Auto Attached   | Included when files matching a glob pattern are referenced                                   |
| Agent Requested | Rule is available to the AI, which decides whether to include it. Must provide a description |
| Manual          | Only included when explicitly mentioned using @ruleName                                      |

## Available Rules

| Rule | Description | Auto-attaches to |
|------|-------------|------------------|
| `database_access.mdc` | Standards for database access and connection management | `**/database/**/*.py`, `**/src/**/*db*.py` |
| `db_test_skip.mdc` | Guidelines for skipping database tests | `**/tests/**/*db*.py`, `**/tests/**/*database*.py` |
| `dspy_generation.mdc` | Guidelines for DSPy training data generation | `**/dspy/**/*.py`, `**/data/processed/dspy_*.py` |
| `etl_parser_strictness.mdc` | Guidelines for ETL parser strictness levels | `**/etl/**/*parser*.py`, `**/scripts/**/*parser*.py` |
| `etl_rules.mdc` | Standards for ETL processes and data pipeline processing | `**/etl/**/*.py`, `**/scripts/**/*.py` |
| `greek_morphology_count_tolerance.mdc` | Guidelines for acceptable tolerance in Greek morphology counts | `**/etl/**/*greek*.py`, `**/tests/**/*greek*.py` |
| `hebrew_rules.mdc` | Guidelines for processing Hebrew theological terms | `**/etl/**/*hebrew*.py`, `**/etl/fix_hebrew_strongs_ids.py` |
| `import_structure.mdc` | Import structure standards for the BibleScholarProject | `**/*.py` |
| `model_validation.mdc` | Guidelines for ML model validation and evaluation | `**/model/**/*.py`, `**/dspy/**/*.py` |
| `pandas_dataframe_type_enforcement.mdc` | Guidelines for enforcing data types in pandas DataFrames | `**/etl/**/*.py`, `**/scripts/**/*pandas*.py` |
| `pandas_null_handling.mdc` | Guidelines for handling null values in pandas DataFrames | `**/etl/**/*.py`, `**/scripts/**/*pandas*.py` |
| `theological_terms.mdc` | Standards for theological terms handling | `**/etl/**/*term*.py`, `**/api/**/*theological*.py` |
| `tvtms_expected_count.mdc` | Expected count validations for TVTMS processing | `**/tvtms/**/*.py`, `**/scripts/*tvtms*.py` |
| `tvtms_txt_only.mdc` | TVTMS file format handling guidelines | `**/tvtms/**/*.py`, `**/scripts/*tvtms*.py` |

## Using Rules

### Auto-attachment

Rules will be automatically attached to files based on the glob patterns defined in each rule's metadata. For example, the database_access rule automatically attaches to database-related files.

### Manual References

You can manually reference a rule in chats using `@ruleName`:

```
@database_access How should I structure this database function?
```

### File References in Rules

Rules can reference other files to include them as context when the rule is triggered. Use the `@filename` syntax:

```
# Database Connection Pattern

Always use the following pattern for database connections:

@src/database/connection.py
```

## Examples

1. When working with Hebrew text processing, the `hebrew_rules` will automatically be applied to provide guidance on Strong's ID handling, critical theological terms, and more.

2. If you're implementing a new ETL process, reference `@etl_rules` to understand the standards for logging, error handling, and file path management.

3. For database work, `@database_access` will provide guidelines on connection management, query construction, error handling, and more.

## Creating New Rules

To create a new rule:

1. Use `Cmd + Shift + P` > "New Cursor Rule"
2. Or create a new `.mdc` file in this directory

Follow the MDC structure outlined above.

## Best Practices

1. Keep rules focused and concise
2. Include concrete examples
3. Reference specific files when helpful using `@filename` syntax
4. Use explicit auto-attachment patterns
5. Provide guidance that would be useful to someone new to the project

## Rule Details

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

### 3. Data Source Fallback Rule (`etl_rules.mdc`)
- **Scope:** All ETL and integration test scripts that load versification mapping or TVTMS source files.
- **When to Apply:**
  - Apply whenever a script or test depends on external data files that may be missing from the main data directory.
- **How to Apply:**
  - Always check the main data directory for required files first.
  - If files are missing, automatically use the secondary data source (STEPBible-Datav2 repo) at:

        C:\Users\mccoy\Documents\Projects\Projects\AiBibleProject\SecondBibleData\STEPBible-Datav2

  - Do not fail or skip the ETL/test if the file is present in the secondary source.
  - Document this fallback logic in the script or test.
- **Example:** See `etl_rules.mdc` for a Python code example.

### 4. DSPy Training Generation Guidelines (`dspy_generation.mdc`)
- **Scope:** All scripts generating DSPy training data for AI model training.
- **When to Apply:**
  - When creating or modifying scripts that generate DSPy-formatted training data.
  - When implementing theological term checking in data generation pipelines.
- **How to Apply:**
  - Ensure all DSPy training data includes theological term integrity checks for critical terms.
  - Process data in batches of at least 100 records at a time, not one by one.
  - Log summary statistics for all generated training examples.
  - Include web interaction examples with clear parameter and response patterns.
- **Example:**
  ```python
  def generate_theological_terms_dataset(conn, batch_size=100):
      """Generate theological term training data in batches."""
      terms_data = []
      offset = 0
      
      while True:
          # Process in batches, not one record at a time
          batch = fetch_theological_terms_batch(conn, offset, batch_size)
          if not batch:
              break
              
          terms_data.extend(process_batch(batch))
          offset += batch_size
          
      # Log statistics about critical terms
      log_critical_term_statistics(terms_data)
      return terms_data
  ```

## Troubleshooting

If a rule isn't being applied:
- Check that the rule file has proper metadata with description and appropriate glob patterns
- Ensure the rule filename has the `.mdc` extension
- Verify that the glob patterns correctly match the files where you expect the rule to apply
- Try referencing the rule manually with `@ruleName` syntax

## References
- See each `.mdc` file for detailed rule text and examples.
- [DSPy Programming Overview](https://dspy.ai/learn/programming/overview/)
- [Cursor Documentation - Rules](https://docs.cursor.com/context/rules) 