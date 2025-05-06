# BibleScholarProject Rules Documentation

This directory contains standardized rules and guidelines for the BibleScholarProject. These rules ensure consistency and quality across the codebase, data processing, and documentation.

## Rules Categories

### Theological Rules
- [Theological Terms](theological_terms.md): Guidelines for handling critical theological terms and their Strong's ID mappings
- [Hebrew Rules](hebrew_rules.md): Special handling rules for Hebrew text and Strong's IDs

### ETL and Data Processing Rules
- [ETL Rules](etl_rules.md): Standards for data extraction, transformation, and loading
- [TVTMS Rules](tvtms_rules.md): Guidelines for versification mapping processing
- [Parser Strictness](parser_strictness.md): Configuration for parser strictness levels

### Database Rules
- [Database Access](database_access.md): Patterns for database access and connection management
- [Database Testing](db_test_skip.md): Rules for managing database-dependent tests

### Development Standards
- [Import Structure](import_structure.md): Standards for Python import organization
- [DataFrame Handling](dataframe_handling.md): Guidelines for pandas DataFrame operations
- [Model Validation](model_validation.md): Standards for ML model validation
- [Documentation Usage](documentation_usage.md): Guidelines for using and maintaining documentation

### AI and Training Data
- [DSPy Generation](dspy_generation.md): Guidelines for generating DSPy training data

## Rules Implementation

### Cursor Rules Integration
All rules in this directory have corresponding `.mdc` files in the `.cursor/rules/` directory that provide AI-assisted coding guidance. The Cursor integration allows the AI assistant to automatically apply these rules when working with relevant files.

### Rule Application Scope

| Rule | Applies To | Key Requirements |
|------|------------|------------------|
| Theological Terms | Hebrew text processing, API endpoints | Minimum term counts, proper Strong's ID extraction |
| Hebrew Rules | Hebrew word analysis, ETL processes | Strong's ID format validation, grammar code processing |
| ETL Rules | All data processing scripts | Validation, logging, error handling |
| Database Access | Database operations, model code | Connection management, transaction handling |
| Import Structure | All Python modules | Import organization, dependency management |
| Parser Strictness | ETL parsers, data loaders | Configurable strictness levels |
| TVTMS Rules | Versification processing | File format requirements, count validations |
| DataFrame Handling | Pandas operations | Type enforcement, null handling |

## Critical Rules

The following rules are considered critical and must always be followed:

1. **Theological Term Counts**: All theological terms must meet minimum occurrence requirements
2. **Database Connection Management**: Always use the proper connection utilities
3. **Strong's ID Extraction**: Always extract Strong's IDs from grammar codes to dedicated fields
4. **Data Validation**: Always validate data after processing

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
┌────────────────────┐     ┌─────────────────┐     ┌───────────────────┐
│  Theological Rules  │────▶│    ETL Rules    │────▶│  Database Rules   │
└────────────────────┘     └─────────────────┘     └───────────────────┘
          │                        │                        │
          │                        │                        │
          ▼                        ▼                        ▼
┌────────────────────┐     ┌─────────────────┐     ┌───────────────────┐
│  Hebrew Processing  │     │ Data Validation │     │  API Endpoints    │
└────────────────────┘     └─────────────────┘     └───────────────────┘
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
type: always
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

- `type`: Usually "always" for our rules
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
| documentation_usage | Documentation standards | All Python files |
| theological_terms | Hebrew theological term handling | Hebrew ETL files |
| dspy_generation | DSPy training data generation | DSPy and data processing |
| db_test_skip | Database testing guidelines | Database test files |
| etl_rules | ETL processing standards | ETL pipeline files |
| pandas_dataframe_type_enforcement | Pandas type handling | DataFrame processing files |
| model_validation | ML model validation | Model-related files |
| tvtms_txt_only | TVTMS file format standards | TVTMS processing files |

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