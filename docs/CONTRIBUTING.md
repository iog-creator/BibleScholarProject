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