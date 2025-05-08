# Contributing to the BibleScholarProject

This document provides guidelines for contributing to the BibleScholarProject, with a focus on documentation standards.

## Documentation Standards

### Documentation Structure

The BibleScholarProject uses a hierarchical documentation structure:

```
docs/
├── README.md                # Main documentation index
├── CONTRIBUTING.md          # This file - contribution guidelines
├── features/                # Feature-specific documentation
├── guides/                  # How-to guides and tutorials
├── reference/               # Reference documentation
└── rules/                   # Development rules
```

### Single Source of Truth Principle

For each major feature, we maintain:
1. One primary documentation file in the appropriate directory under `docs/`
2. One corresponding cursor rule in `.cursor/rules/` (when applicable)

### Documentation File Requirements

Every documentation file must include:

1. **Header** - Title and purpose of the document
2. **Overview** - Brief description of the feature/component
3. **Technical Details** - Implementation specifics
4. **Usage Examples** - Concrete examples of how to use the feature
5. **Troubleshooting** - Common issues and solutions
6. **Related Documentation** - Links to related documents
7. **Modification History** - Record of significant changes

### Cursor Rules Integration

When creating or updating documentation:

1. Reference the documentation file in the corresponding cursor rule using the format:
   ```
   For more details, see [Documentation Title](docs/path/to/file.md)
   ```

2. Reference the cursor rule in the documentation file using the format:
   ```
   This document is complemented by the [rule_name](.cursor/rules/rule_name.mdc) cursor rule.
   ```

## Where to Put Documentation

### New Features

1. Create a primary markdown document in `docs/features/`
2. Create a corresponding cursor rule in `.cursor/rules/features/` if needed
3. Update `docs/README.md` to include your new documentation

### API Documentation

All API endpoints should be documented in:
- `docs/reference/API_REFERENCE.md`

### Database Schema Changes

Database schema documentation belongs in:
- `docs/reference/DATABASE_SCHEMA.md`

### Development Rules

Development rules should be placed in:
- `docs/rules/{rule_name}.md`
- `.cursor/rules/standards/{rule_name}.mdc`

## Updating Documentation

When updating documentation:

1. **Always check for existing documentation first**:
   - Check the main documentation index at `docs/README.md`
   - Search for keywords related to your update
   - Review the directory structure for the appropriate location

2. **Update the existing document rather than creating a new one**:
   - Add your information to the appropriate section
   - Update examples if they've changed
   - Add an entry to the modification history section

3. **Maintain cross-references**:
   - Ensure links to other documents are still valid
   - Update links if document paths have changed

## Documentation Review Checklist

Before submitting documentation changes, ensure:

1. The document follows the required structure
2. Code examples are correct and tested
3. Links to other documents are valid
4. All cross-references are maintained
5. The modification history has been updated

## For AI Assistants

When working with documentation:

1. Always check `docs/README.md` first to locate the correct documentation file
2. Use search tools with specific keywords to find relevant documentation
3. Update existing documentation rather than creating new files
4. When in doubt about which document to update, check in this order:
   - docs/features/
   - docs/reference/
   - docs/guides/
   - docs/rules/

## Modification History

| Date | Description | Author |
|------|-------------|--------|
| 2025-05-06 | Initial documentation standards | BibleScholar Team |

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
  - [`dataset_validation_expansion.md`](features/dataset_validation_expansion.md) - Expanding validation datasets for model testing

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
- **[Claude API Setup**](guides/claude_api_setup.md) - Setting up Claude API integration

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