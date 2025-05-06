# BibleScholarProject Documentation

Welcome to the BibleScholarProject documentation! This directory contains comprehensive documentation for all aspects of the project.

## Directory Structure

- [`features/`](features/) - Feature-specific documentation
  - [`bible_translations.md`](features/bible_translations.md) - Bible translation processing and access
  - [`dspy_usage.md`](features/dspy_usage.md) - DSPy training and model usage
  - [`etl_pipeline.md`](features/etl_pipeline.md) - ETL process for Bible data
  - [`semantic_search.md`](features/semantic_search.md) - Semantic search with pgvector
  - [`theological_terms.md`](features/theological_terms.md) - Theological term handling

- [`guides/`](guides/) - How-to guides and tutorials
  - [`data_verification.md`](guides/data_verification.md) - Verifying data quality and integrity
  - [`documentation_maintenance.md`](guides/documentation_maintenance.md) - Maintaining project documentation
  - [`dspy_training_guide.md`](guides/dspy_training_guide.md) - Guide for DSPy training
  - [`system_build_guide.md`](guides/system_build_guide.md) - Building the complete system
  - [`testing_framework.md`](guides/testing_framework.md) - Using the testing framework

- [`reference/`](reference/) - Reference documentation
  - [`API_REFERENCE.md`](reference/API_REFERENCE.md) - API endpoints and usage
  - [`DATABASE_SCHEMA.md`](reference/DATABASE_SCHEMA.md) - Database schema reference
  - [`SYSTEM_ARCHITECTURE.md`](reference/SYSTEM_ARCHITECTURE.md) - System architecture overview
  - [`cursor_rules_guide.md`](reference/cursor_rules_guide.md) - Guide for cursor rules
  - [`organization_reference.md`](reference/organization_reference.md) - Project organization standards
  - [`rule_mapping.md`](reference/rule_mapping.md) - Mapping of old to new rule locations
  - [`vector_search_reference.md`](reference/vector_search_reference.md) - Vector search reference
  - [`rules/`](reference/rules/) - Standards and rules reference

- [`archive/`](archive/) - Archived documentation
  - Contains older versions of documentation for reference

## Key Documentation

- [**Contributing Guide**](CONTRIBUTING.md) - Guidelines for contributing to the project
- [**Feature Documentation**](features/) - Documentation for all major features
- [**API Reference**](reference/API_REFERENCE.md) - Complete API documentation

## Development Workflow

For details on the development workflow, please refer to the [Contributing Guide](CONTRIBUTING.md).

## Documentation Standards

The BibleScholarProject follows strict documentation standards:

1. **Single Source of Truth** - Each component/feature has one primary document
2. **Consistent Structure** - All documents follow consistent formatting and structure
3. **Cross-Referencing** - Related documents link to each other with relative links
4. **Validation** - Documentation is validated for broken links and completeness
5. **Version Control** - Documentation is versioned with the codebase

For more details, see the [Documentation Maintenance Guide](guides/documentation_maintenance.md).
