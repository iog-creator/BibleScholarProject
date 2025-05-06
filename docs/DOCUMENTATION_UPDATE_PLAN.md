# BibleScholarProject Documentation Reorganization Plan

## Overview

This document outlines the comprehensive plan for reorganizing and consolidating the BibleScholarProject documentation. The goal is to create a clear, consistent, and maintainable documentation structure that follows the "single source of truth" principle and makes information easily discoverable for contributors and users.

## Implementation Progress

### Completed Changes
- Created new directory structure (`docs/features/`, `docs/guides/`, `docs/reference/`)
- Created `docs/CONTRIBUTING.md` with comprehensive documentation standards
- Created consolidated semantic search documentation in `docs/features/semantic_search.md`
- Created consolidated theological terms documentation in `docs/features/theological_terms.md`
- Moved Database Schema documentation to `docs/reference/DATABASE_SCHEMA.md`
- Moved API Reference documentation to `docs/reference/API_REFERENCE.md`
- Moved DSPy Training Guide to `docs/guides/dspy_training_guide.md`
- Updated `docs/README.md` to reflect new structure and point to consolidated documents
- Updated cursor rule `.cursor/rules/pgvector_semantic_search.mdc` to reference consolidated documentation
- Created new cursor rules directory structure (`.cursor/rules/features/`, `.cursor/rules/standards/`)
- Created cursor rules for theological terms, database access, API standards, and DSPy generation
- Created `scripts/validate_documentation.py` for documentation validation
- Created `standards/documentation_usage.mdc` cursor rule for documentation standards
- Updated `.cursor/rules/README.md` to align with new structure
- Deleted redundant files after consolidation
- Standardized cursor rule types across all rule files:
  - Changed features rules to "always" type (pgvector_semantic_search, theological_terms, etl_pipeline, bible_translations)
  - Changed standards rules to appropriate types (documentation_usage to "always", database_access and api_standards to "auto attach")
  - Fixed inconsistent YAML frontmatter formatting across all rule files
  - Fixed file references to match new documentation structure
  - Ensured all rules have proper globs configured for auto-attachment
- Consolidated `docs/TESTING_FRAMEWORK.md` into `docs/guides/testing_framework.md`
- Consolidated `docs/DATA_VERIFICATION.md` into `docs/guides/data_verification.md`
- Consolidated `docs/etl_rules.md` into `docs/features/etl_pipeline.md`
- Created new `docs/reference/SYSTEM_ARCHITECTURE.md` based on `docs/ORGANIZATION.md`
- Updated main `docs/README.md` to reflect the new documentation structure
- Completed consolidation of other feature documentation:
  - `docs/BIBLE_TRANSLATIONS.md` → `docs/features/bible_translations.md`
  - `docs/TESTING_FRAMEWORK.md` → `docs/guides/testing_framework.md`
  - `docs/etl_rules.md` → `docs/features/etl_pipeline.md`
  - `docs/DATA_VERIFICATION.md` → `docs/guides/data_verification.md`
- Moved appropriate files to their new locations according to the directory structure
- Updated cross-references between documentation files
- Applied cursor rule organization to remaining rules:
  - `.cursor/rules/etl_rules.mdc` → `.cursor/rules/features/etl_pipeline.mdc`
  - `.cursor/rules/etl_parser_strictness.mdc` → `.cursor/rules/standards/parser_strictness.mdc`
- Created archive directory for deprecated files
- Archived redundant documentation files with notes pointing to new locations
- Updated API reference to include all referenced endpoints
- Created documentation validation script to check for broken links
- Created `DOCUMENTATION_CLEANUP_PHASE2_COMPLETE.md` documenting the completion

### Next Steps
1. Address any remaining broken links identified by the validation script
2. Standardize API documentation with more detailed examples
3. Update cursor rules to ensure all references are valid
4. Create a concise guide for contributors on maintaining the documentation structure
5. Consider implementing automated API documentation generation

## Current Documentation Issues

1. **Duplication and Redundancy**
   - Multiple files covering the same topics (e.g., PGVECTOR_SEARCH.md, SEMANTIC_SEARCH.md, COMPREHENSIVE_SEMANTIC_SEARCH.md)
   - Duplicate information spread across markdown files and cursor rules
   - Inconsistent naming conventions making it difficult to find the correct documentation

2. **Lack of Clear Structure**
   - No clear hierarchy between documentation types
   - Missing links between related documentation
   - Unclear when to use docs/ vs. docs/rules/ vs. .cursor/rules/

3. **Documentation Usage Issues**
   - AI tends to create new files instead of updating existing ones
   - No clear guidance on when to update docs vs. rules
   - Difficulty finding the right document for a specific topic

## Documentation Structure Reorganization

### 1. Single Source of Truth Principle

For each major component/feature, we will establish:
- One primary markdown document in `docs/`
- One corresponding cursor rule in `.cursor/rules/`
- Clear cross-references between them

### 2. Hierarchical Documentation Structure

```
docs/
├── README.md                       # Main documentation index
├── CONTRIBUTING.md                 # Contribution guidelines including doc standards
├── features/                       # Feature-specific documentation
│   ├── semantic_search.md          # Single source of truth for semantic search
│   ├── theological_terms.md        # Single source of truth for theological terms
│   └── ...
├── guides/                         # How-to guides and tutorials
│   ├── vector_search_tutorial.md
│   └── ...
├── reference/                      # Reference documentation
│   ├── API_REFERENCE.md            # API endpoints
│   ├── DATABASE_SCHEMA.md          # Database schema
│   └── ...
└── rules/                          # Development rules
    ├── README.md                   # Rules index
    ├── documentation_standard.md   # Documentation standards and process
    └── ...

.cursor/rules/                      # Cursor rules
├── README.md                       # Rules index with clear usage guidance
├── features/                       # Feature-specific rules
│   ├── pgvector_semantic_search.mdc
│   └── ...
└── standards/                      # Standard rules
    ├── documentation_usage.mdc
    └── ...
```

### 3. Documentation Consolidation Plan

#### Phase 1: Semantic Search Documentation Consolidation
- Create unified `docs/features/semantic_search.md` 
- Merge content from:
  - docs/PGVECTOR_SEARCH.md
  - docs/SEMANTIC_SEARCH.md
  - docs/COMPREHENSIVE_SEMANTIC_SEARCH.md 
- Update .cursor/rules/pgvector_semantic_search.mdc to reference the new file

#### Phase 2: Theological Terms Documentation Consolidation
- Create unified `docs/features/theological_terms.md`
- Merge content from:
  - docs/theological_terms.md
  - docs/rules/theological_terms.md
- Update .cursor/rules/theological_terms.mdc to reference the new file

#### Phase 3: Continue with remaining documentation areas

## Cursor Rules Structure

### 1. Cursor Rule Types

The project uses the following cursor rule types:

- **always**: Rules that should always be included regardless of context
  - Example: `documentation_usage.mdc`

## Modification History

| Date | Author | Description |
|------|--------|-------------|
| 2025-05-01 | Documentation Team | Created initial documentation reorganization plan |
| 2025-05-06 | Documentation Team | Added overview section and modification history to comply with documentation standards |