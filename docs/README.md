# BibleScholarProject Documentation

Welcome to the BibleScholarProject documentation. This repository contains comprehensive documentation for all aspects of the project.

## Documentation Structure

The documentation is organized into the following sections:

- **[Features](features/)**: Detailed documentation of project features and capabilities
  - [Vector Search Web Integration](features/vector_search_web_integration.md)
  - [ETL Pipeline](features/etl_pipeline.md)
  - [Theological Terms](features/theological_terms.md)

- **[Guides](guides/)**: How-to guides and tutorials for common tasks
  - Installation guides
  - Deployment guides
  - User guides

- **[Reference](reference/)**: Reference documentation for APIs, schemas, and configurations
  - API documentation
  - Database schema
  - Configuration options

- **[Rules](rules/)**: Development rules and guidelines
  - [Database Access Patterns](rules/database_access.md)
  - [Documentation Usage](rules/documentation_usage.md)
  - [Parser Strictness](rules/parser_strictness.md)

## Key Documentation Files

### Vector Search

- [README_VECTOR_SEARCH.md](../README_VECTOR_SEARCH.md): Core implementation of pgvector semantic search
- [Vector Search Web Integration](features/vector_search_web_integration.md): Integration with web applications

### Bible Processing

- [README_BIBLE_CORPUS.md](../README_BIBLE_CORPUS.md): Bible corpus processing documentation
- [README_BIBLE_QA.md](../README_BIBLE_QA.md): Bible question-answering system documentation

### AI Integration

- [README_DSPY.md](../README_DSPY.md): DSPy integration for language model training
- [README_DSPY_SEMANTIC_SEARCH.md](../README_DSPY_SEMANTIC_SEARCH.md): DSPy enhanced semantic search

## Contributing to Documentation

When contributing to the documentation:

1. Follow the established structure
2. Update the appropriate README files to include links to new documentation
3. Use consistent formatting and style
4. Include examples where appropriate
5. Cross-reference related documentation

## Cursor Rules

The project uses Cursor AI assistance with specialized rules. See the [rule creation guide](rules/rule_creation_guide.md) for more information on creating and maintaining rules.

## Directory Structure

- [`features/`](features/) - Feature-specific documentation
  - [`bible_translations.md`](features/bible_translations.md) - Bible translation processing and access
  - [`dspy_usage.md`](features/dspy_usage.md) - DSPy training and model usage
  - [`etl_pipeline.md`](features/etl_pipeline.md) - ETL process for Bible data
  - [`semantic_search.md`](features/semantic_search.md) - Semantic search with pgvector
  - [`theological_terms.md`](features/theological_terms.md) - Theological term handling
  - [`HUGGINGFACE_DSPY_INTEGRATION.md`](features/HUGGINGFACE_DSPY_INTEGRATION.md) - HuggingFace integration with DSPy
  - [`MLFLOW_DSPY_INTEGRATION.md`](features/MLFLOW_DSPY_INTEGRATION.md) - MLflow experiment tracking with DSPy
  - [`etl_rules.md`](features/etl_rules.md) - Standards for ETL processes

- [`guides/`](guides/) - How-to guides and tutorials
  - [`claude_api_setup.md`](guides/claude_api_setup.md) - Setting up Claude API integration
  - [`data_verification.md`](guides/data_verification.md) - Verifying data quality and integrity
  - [`documentation_maintenance.md`](guides/documentation_maintenance.md) - Maintaining project documentation
  - [`dspy_training_guide.md`](guides/dspy_training_guide.md) - Guide for DSPy training
  - [`dspy_mlflow_integration.md`](guides/dspy_mlflow_integration.md) - Tracking DSPy models with MLflow
  - [`dspy_model_management.md`](guides/dspy_model_management.md) - Managing DSPy models in LM Studio
  - [`system_build_guide.md`](guides/system_build_guide.md) - Building the complete system
  - [`testing_framework.md`](guides/testing_framework.md) - Using the testing framework

- [`reference/`](reference/) - Reference documentation
  - [`API_REFERENCE.md`](reference/API_REFERENCE.md) - API endpoints and usage
  - [`claude_api_integration.md`](reference/claude_api_integration.md) - Claude API integration reference
  - [`DATABASE_SCHEMA.md`](reference/DATABASE_SCHEMA.md) - Database schema reference
  - [`SYSTEM_ARCHITECTURE.md`](reference/SYSTEM_ARCHITECTURE.md) - System architecture overview
  - [`cursor_rules_guide.md`](reference/cursor_rules_guide.md) - Guide for cursor rules
  - [`lm_studio_integration.md`](reference/lm_studio_integration.md) - LM Studio integration details
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
- [**DSPy Model Management**](guides/dspy_model_management.md) - Managing models in LM Studio
- [**Claude API Setup**](guides/claude_api_setup.md) - Setting up Claude API integration

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
