---
title: Cursor Rules Scripts
description: Scripts for managing and maintaining Cursor AI rules
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../../docs/rules/rule_creation_guide.md
  - ../../docs/reference/cursor_rules_guide.md
---
# Cursor Rules Scripts

This directory contains scripts for managing and maintaining Cursor AI rules in the BibleScholarProject.

## Scripts

- `fix_mdc_files.py` - Fix and standardize MDC files for cursor rules
- `deploy_rules.py` - Deploy cursor rules to the .cursor/rules directory
- `validate_rules.py` - Validate cursor rules for correctness
- `generate_rule_mapping.py` - Generate mapping of old to new rule locations
- `backup_rules.py` - Create backups of cursor rules

## Cursor Rules

Cursor rules are special markdown files with specific frontmatter that provide guidance to the Cursor AI when working with the codebase. They help enforce coding standards, document patterns, and guide development.

## Usage

Most scripts can be run directly with Python. For example:

```
python fix_mdc_files.py
```

## Cross-References
- [Scripts Directory](../README.md)
- [Rule Creation Guide](../../docs/rules/rule_creation_guide.md)
- [Cursor Rules Guide](../../docs/reference/cursor_rules_guide.md) 