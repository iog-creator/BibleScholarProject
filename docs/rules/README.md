---
title: Rules Documentation
description: Development rules and guidelines for the BibleScholarProject
last_updated: 2025-05-08
related_docs:
  - ../README.md
  - ../features/README.md
  - ../guides/README.md
  - ../reference/README.md
---
# Rules Documentation

This directory contains development rules and guidelines for the BibleScholarProject.

## Rules Index

- [Database Access](database_access.md)
- [Documentation Usage](documentation_usage.md)
- [Parser Strictness](parser_strictness.md)
- [Rule Creation Guide](rule_creation_guide.md)

## Purpose of Rules

Rules provide consistent standards and guidelines for development in the BibleScholarProject. They ensure:

1. Consistent coding practices across the project
2. Adherence to security and data integrity standards
3. Proper documentation and testing procedures
4. Compatibility across components

## Adding New Rules

When adding new rules:

1. Create a new markdown file following the documentation standards
2. Include proper frontmatter with title, description, and cross-references
3. Update this README.md to include a link to the new rule
4. Cross-reference related documentation in the frontmatter

## Cross-References
- [Main Documentation Index](../README.md)
- [Features Documentation](../features/README.md)
- [Guides Documentation](../guides/README.md)
- [Reference Documentation](../reference/README.md)

# BibleScholarProject Rules Documentation

This directory contains standardized rules and guidelines for the BibleScholarProject. These rules ensure consistency and quality across the codebase, data processing, and documentation.

## Rules Categories

### Core Rules
- [pgVector Semantic Search](pgvector_semantic_search.md): Guidelines for semantic search implementation using pgvector
- [Database Access](database_access.md): Patterns for database access and connection management
- [Documentation Usage](documentation_usage.md): Guidelines for using and maintaining documentation
- [DSPy Generation](dspy_generation.md): Guidelines for generating DSPy training data
- [DB Test Skip](db_test_skip.md): Rules for managing database-dependent tests
- [Parser Strictness](parser_strictness.md): Configuration for parser strictness levels

> **Note:** Older or superseded rules are moved to the `archive/` directory for historical reference and are not part of the active rule set.

## Rules Implementation

### Cursor Rules Integration
All rules in this directory have corresponding `.mdc` files in the `.cursor/rules/` directory that provide AI-assisted coding guidance. The Cursor integration allows the AI assistant to automatically apply these rules when working with relevant files.

### Rule Application Scope

| Rule | Applies To | Key Requirements |
|------|------------|------------------|
| pgvector_semantic_search | Semantic search, vector search API | Environment variable config, vector format, batch processing |
| database_access | Database operations, model code | Connection management, transaction handling |
| documentation_usage | All Python files | Documentation standards, update process |
| dspy_generation | DSPy and data processing | Data format, batch processing, theological validation |
| db_test_skip | Database test files | Skipping logic, pytest integration |
| parser_strictness | ETL parsers, data loaders | Configurable strictness levels |

## Critical Rules

The following rules are considered critical and must always be followed:

1. **Database Connection Management**: Always use the proper connection utilities
2. **Semantic Search Configuration**: Always use environment variables for configuration
3. **Data Validation**: Always validate data after processing
4. **Documentation Updates**: Always update documentation when changing functionality

## Rule Verification

Rules can be verified through:

1. Automated tests in the `tests/` directory
2. Database validation queries
3. Linting and static analysis tools
4. Documentation review

## Updating Rules

When updating rules:

1. Update both the `.md` file in this directory and the corresponding `.mdc` file in `.cursor/rules/`
2. Document the changes in the "Update History" section of the rule file
3. Update any code examples to reflect the new guidelines
4. Ensure all tests pass with the updated rules

## Rule Relationship Diagram

```
┌────────────────────────────┐     ┌──────────────────────┐
│  Semantic Search (pgvector)│────▶│  Database Access     │
└────────────────────────────┘     └──────────────────────┘
          │                                 │
          ▼                                 ▼
┌────────────────────────────┐     ┌──────────────────────┐
│  DSPy Training Generation  │     │  Documentation Usage │
└────────────────────────────┘     └──────────────────────┘
```

This diagram shows how rules interact with each other and influence different parts of the system.

## Rules Documentation Format

Each rule document follows a standard format:

1. **Overview**: Brief description of the rule's purpose
2. **Guidelines**: Specific guidelines to follow
3. **Code Examples**: Examples of proper implementation
4. **Validation**: How to verify the rule is being followed
5. **Update History**: Record of changes to the rule

# Cursor Rules Management

This document outlines the standardized process for creating and managing cursor rules in the BibleScholar project.

## Overview

Cursor rules provide context-aware guidance to AI assistants working with our codebase. They help ensure consistent coding patterns, documentation practices, and adherence to project-specific requirements.

## Standard Process for Managing Rules

We use a single, consistent approach for creating and updating cursor rules:

1. Rules are defined in Markdown files (`.mdc`) in the `.cursor/rules/` directory
2. Each rule has a standardized structure with YAML frontmatter and content sections
3. Rules are created and updated using our standard PowerShell script

## Rule Structure

Every cursor rule must follow this structure:

```markdown
---
type: always|auto|agent_requested|manual
title: Rule Title
description: Brief description of what the rule enforces
globs:
  - "pattern/to/match/*.py"
  - "another/pattern/*.py"
alwaysApply: true|false
---

# Rule Title

Detailed explanation and guidelines...
```

### Frontmatter Components

- `type`: Rule type (always, auto, agent_requested, manual)
- `title`: Concise title of the rule
- `description`: Brief explanation of the rule's purpose
- `globs`: Array of glob patterns that determine when rule applies
- `alwaysApply`: Boolean indicating if rule should always be applied

## Standard Rule Creation Process

To create or update cursor rules:

1. Create rule content in `tmp_rules_rebuild/[rule_name]_content.txt`
2. Run our standard rule creation script:

```powershell
# Create new rule
.\scripts\cursor_rules\create_rule.ps1 -RuleName "rule_name" -Title "Rule Title" -Description "Rule description" -Globs @("glob1", "glob2") -AlwaysApply $true

# Update existing rule
.\scripts\cursor_rules\update_rule.ps1 -RuleName "rule_name" 
```

## Cleanup and Organization

For maintaining clean rule organization:

1. Keep all rule content files in `tmp_rules_rebuild/`
2. Use consistent naming: `[rule_name]_content.txt`
3. Run periodic cleanup to remove unused temporary files

## Available Rules

The following cursor rules are currently defined:

| Rule | Purpose | Applies To |
|------|---------|------------|
| pgvector_semantic_search | Semantic search implementation | Vector search, API, DSPy |
| database_access | Database access patterns | Database code |
| documentation_usage | Documentation standards | All Python files |
| dspy_generation | DSPy training data generation | DSPy and data processing |
| db_test_skip | Database testing guidelines | Database test files |
| parser_strictness | ETL parser strictness | ETL/data loader files |

## Adding New Rules

When adding new rules:

1. Identify need for consistent guidance in specific area
2. Create content file with comprehensive guidelines
3. Use the standard script to generate properly formatted rule
4. Add rule to the table in this document
5. Remove any temporary files created during development

## Troubleshooting

If rules aren't being applied correctly:

1. Verify frontmatter format (check for exact YAML syntax)
2. Confirm glob patterns correctly match intended files
3. Ensure rule content follows Markdown formatting
4. Check Cursor's rule logs for any error messages 

## Cross-References
- [Documentation Index](../README.md)
- [Database Schema](../reference/DATABASE_SCHEMA.md)
- [ETL Pipeline](../features/etl_pipeline.md)
- [Rule Creation Guide](./rule_creation_guide.md)

# Rules Directory

This directory contains development rules and guidelines for the BibleScholarProject.

See the [Documentation Index](../README.md) for the full documentation structure. 