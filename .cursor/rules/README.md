# BibleScholarProject Cursor Rules

This directory contains Cursor Rules for the BibleScholarProject. These rules provide consistent patterns, guidance, and standards for working with the codebase.

## Documentation Integration

All cursor rules are now integrated with the main documentation system. Each rule should reference its corresponding documentation file, and each documentation file should reference its corresponding rule.

For the full documentation structure, see [Documentation Structure](../../docs/README.md).

## Directory Structure

The cursor rules are organized into the following directories:

```
.cursor/rules/
├── README.md                    # This file
├── available_rules.json         # Registry of active rules
├── features/                    # Feature-specific rules
│   └── pgvector_semantic_search.mdc # Semantic search implementation
└── standards/                   # Standard development rules
    ├── api_standards.mdc        # API implementation standards
    ├── database_access.mdc      # Database access patterns 
    ├── db_test_skip.mdc         # Database test skipping guidelines
    ├── documentation_usage.mdc  # Documentation standards
    ├── dspy_generation.mdc      # DSPy data generation guidelines
    └── parser_strictness.mdc    # Parser strictness guidelines
```

> **Note:** Older or superseded rules are moved to the `archive/` directory for historical reference and are not part of the active rule set.

## Rule Types

| Rule Type       | Description                                                                                  |
| --------------- | -------------------------------------------------------------------------------------------- |
| Always          | Always included in the model context (set `alwaysApply: true`)                                |
| Auto Attached   | Included when files matching a glob pattern are referenced                                   |
| Agent Requested | Rule is available to the AI, which decides whether to include it. Must provide a description |
| Manual          | Only included when explicitly mentioned using @ruleName                                      |

## Available Rules

| Rule | Type | Description | Auto-attaches to |
|------|------|-------------|------------------|
| `features/pgvector_semantic_search.mdc` | Always | Guidelines for pgvector semantic search | `src/utils/generate_verse_embeddings.py`, etc. |
| `standards/api_standards.mdc` | Auto Attach | API implementation standards | `src/api/**/*.py`, etc. |
| `standards/database_access.mdc` | Auto Attach | Standards for database access | `src/database/**/*.py`, etc. |
| `standards/db_test_skip.mdc` | Agent Requested | Guidelines for skipping database tests | `tests/**/*.py`, etc. |
| `standards/documentation_usage.mdc` | Always | Documentation standards and usage | `**/*.py` |
| `standards/dspy_generation.mdc` | Always | Guidelines for DSPy training data generation | `tests/**/dspy*.py`, etc. |
| `standards/parser_strictness.mdc` | Agent Requested | Guidelines for ETL parser strictness levels | `**/etl/**/*parser*.py`, etc. |

## Creating and Updating Rules

When creating or updating cursor rules:

1. Check if a rule already exists for the feature/component
2. Place the rule in the appropriate directory (`features/` or `standards/`)
3. Ensure the rule references the corresponding documentation file
4. Use the standard rule template:

```
type: always|auto
title: Rule Title
description: Brief description of what the rule does
globs: 
  - "pattern/to/match/*.py"
  - "other/pattern/*.js"
alwaysApply: false
---

# Rule Title

For detailed documentation, see [Documentation Title](docs/path/to/file.md).

Rule content goes here...
```

## Using Rules

### Auto-attachment

Rules will be automatically attached to files based on the glob patterns defined in each rule's metadata. For example, the database_access rule automatically attaches to database-related files.

### Manual References

You can manually reference a rule in chats using `@ruleName`:

```
@database_access How should I structure this database function?
```

## Troubleshooting

If a rule isn't being applied:
- Check that the rule file has proper metadata with description and appropriate glob patterns
- Ensure the rule filename has the `.mdc` extension
- Verify that the glob patterns correctly match the files where you expect the rule to apply
- Try referencing the rule manually with `@ruleName` syntax

## Documentation Validation

To validate that all rules properly reference documentation and vice versa:

```bash
python scripts/validate_documentation.py
```

## See Also

- [Documentation Standards](../../docs/CONTRIBUTING.md)
- [Rule Creation Guide](.cursor/rules/rule_creation_guide.mdc) 