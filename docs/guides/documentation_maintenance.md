# Documentation Maintenance Guide

This guide provides concise instructions for maintaining the BibleScholarProject documentation structure. Following these guidelines will ensure that the documentation remains consistent, accurate, and easy to navigate.

## Documentation Structure Overview

The documentation is organized hierarchically:

```
docs/
├── README.md                # Main documentation index
├── features/                # Feature-specific documentation
│   ├── semantic_search.md   # Semantic search documentation
│   └── ...
├── guides/                  # How-to guides and tutorials
│   ├── testing_framework.md # Testing framework guide
│   └── ...
├── reference/               # Reference documentation
│   ├── API_REFERENCE.md     # API endpoints
│   └── ...
└── rules/                   # Development rules
    └── ...
```

## Single Source of Truth Principle

The most important documentation principle is maintaining a **single source of truth**:

1. Each major feature or component should have ONE primary documentation file
2. Documentation should be consolidated, not duplicated
3. Cross-references should point to the primary documentation

## When Making Changes to the Project

Follow these steps when making changes that affect documentation:

1. **Identify the Primary Documentation File**
   - Consult `docs/README.md` to find the appropriate file for your changes
   - If updating a feature, look in `docs/features/`
   - If updating API endpoints, look in `docs/reference/API_REFERENCE.md`

2. **Update the Primary Documentation**
   - Add your changes to the existing documentation file
   - Do NOT create new documentation files unless adding a completely new feature
   - Include examples, parameters, and return values where appropriate

3. **Update Cross-References**
   - If you rename or move a file, update all references to that file
   - Use the validation script to check for broken links after changes

4. **Update the Modification History**
   - Add an entry to the Modification History table at the end of the file
   - Include the date, a brief description of the change, and your name/team

## Cursor Rules and Documentation

When dealing with cursor rules:

1. **Rule Types and Locations**
   - Feature-specific rules go in `.cursor/rules/features/`
   - Standard rules go in `.cursor/rules/standards/`
   - All rules should have appropriate globs for auto-attachment

2. **Rule-Documentation Synchronization**
   - Each cursor rule should reference its primary documentation file
   - When updating documentation, update the corresponding cursor rule

## API Documentation

When documenting API endpoints:

1. **All endpoints must be in `docs/reference/API_REFERENCE.md`**
2. **Use consistent formatting for endpoint documentation:**
   ```
   GET /api/endpoint
   ```
3. **Include parameters, return values, and examples**
4. **If adding a new API endpoint category, add a new section**

## Validating Documentation

Use the documentation validation script to check for issues:

```bash
python scripts/validate_documentation.py
```

This script checks for:
- Broken links
- Invalid cursor rule references
- Undocumented API endpoints

Fix any issues identified by the script before considering documentation changes complete.

## Automatic Documentation Fixes

For common documentation issues, you can use the automatic fix script:

```bash
python scripts/fix_documentation.py
```

This script attempts to automatically fix:
1. **Cursor rule references** - Updates references to cursor rules with their correct paths
2. **Broken internal links** - Fixes links to other documentation files
3. **Undocumented API endpoints** - Adds endpoints referenced in documentation to the API Reference

After running the fix script, run the validation script again to check for remaining issues:

```bash
python scripts/validate_documentation.py
```

Some issues will require manual fixes, particularly example links in template files or links to files outside the repository.

## Pre-Commit Documentation Validation

A pre-commit hook is available to automatically validate documentation before each commit. To install it:

**Windows (PowerShell):**
```powershell
.\scripts\install_hooks.ps1
```

**Unix (Bash):**
```bash
bash scripts/install_hooks.sh
```

Once installed, the documentation validation script will run automatically when you attempt to commit changes to documentation files, preventing commits with broken links or other issues.

## Avoiding Common Documentation Issues

1. **Avoid Duplication**: Don't repeat information that exists elsewhere
2. **Use Relative Links**: Use relative paths for cross-references
3. **Keep README.md Updated**: Add new documents to the main README.md index
4. **Maintain Consistent Formatting**: Follow existing formatting conventions

## Getting Help

If you're unsure where to document something:

1. Check the `docs/README.md` index first
2. Look for similar features and follow their documentation pattern
3. Ask for guidance from the Documentation Team

## Modification History

| Date | Author | Description |
|------|--------|-------------|
| 2025-06-15 | Documentation Team | Created documentation maintenance guide | 