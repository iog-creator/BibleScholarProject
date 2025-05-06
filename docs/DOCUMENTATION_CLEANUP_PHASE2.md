# Documentation Cleanup Phase 2

## Overview

This document outlines the plan for addressing documentation issues identified by the `validate_documentation.py` script. Phase 1 of the documentation cleanup focused on consolidating files into a clear directory structure. Phase 2 will focus on fixing structural issues, ensuring consistency, and making the documentation fully compliant with project standards.

## Issues to Address

The validation script identified several categories of issues:

1. **Missing Required Sections**
   - Many files missing "## Overview" sections
   - Many files missing "Modification History" tables

2. **Incorrect Cross-References**
   - Links between documents using incorrect relative paths
   - Links to cursor rules using incorrect paths

3. **Missing Documentation References in Cursor Rules**
   - Many cursor rules don't reference their related documentation files

4. **README.md Issues**
   - Main README.md doesn't link to all documentation files

5. **Loose Documentation Files**
   - Documentation files scattered in various directories need to be migrated

## Action Plan

### 1. Fix Missing Required Sections

For each file missing required sections, add:

- **Overview Section**: After the title, add a clear "## Overview" section that summarizes the purpose and content of the document.
- **Modification History Table**: At the end of each document, add a standardized table:
  ```markdown
  ## Modification History

  | Date | Author | Description |
  |------|--------|-------------|
  | YYYY-MM-DD | Documentation Team | Created document |
  | YYYY-MM-DD | Documentation Team | Added required sections |
  ```

Priority order for fixing files:
1. Feature documentation files (`docs/features/`)
2. Reference documentation files (`docs/reference/`)
3. Guide documentation files (`docs/guides/`)
4. Rules documentation files (`docs/rules/`)
5. Root documentation files (`docs/`)

### 2. Fix Cross-References

Update all cross-references to use consistent and correct relative paths:

- Between sibling files (files in the same directory): `./filename.md`
- From one directory to another: `../directory/filename.md`
- References to cursor rules: `../../.cursor/rules/rulename.mdc`

Create a cross-reference guide with examples for common references:
```markdown
# References from features/ to reference/
../reference/DATABASE_SCHEMA.md

# References from features/ to guides/
../guides/testing_framework.md

# References from features/ to other features/
./other_feature.md

# References from reference/ to features/
../features/feature_name.md
```

### 3. Update Cursor Rules

For each cursor rule file:
1. Add proper YAML frontmatter with:
   - `type`: "always" or appropriate type
   - `title`: Clear, descriptive title
   - `description`: Brief description
   - `globs`: Appropriate file patterns
   - `alwaysApply`: true/false as appropriate

2. Add a reference to the corresponding documentation file:
   ```markdown
   For complete documentation, see [Feature Name](../docs/features/feature_name.md).
   ```

### 4. Update README.md

Update the main `docs/README.md` to:
1. Link to all documentation files in all subdirectories
2. Group links by category (features, guides, reference, rules)
3. Include brief descriptions of each document

### 5. Migrate Loose Documentation

For each loose documentation file:
1. Determine the appropriate location in the new structure
2. Move and rename as needed to fit the structure
3. Update with required sections and cross-references
4. Archive original location if needed

## Implementation Steps

1. Create a script to add required sections to documentation files
2. Create a script to fix cross-references
3. Update cursor rules manually, starting with the most important ones
4. Update the main README.md
5. Migrate loose documentation files

## Priority Files

The following files should be fixed first:

1. `docs/features/semantic_search.md` (Fix cursor rule reference)
2. `.cursor/rules/pgvector_semantic_search.mdc` (Add documentation reference)
3. `docs/reference/API_REFERENCE.md` (Add Overview section)
4. `docs/reference/DATABASE_SCHEMA.md` (Fix cross-references)
5. `docs/reference/SYSTEM_ARCHITECTURE.md` (Fix cross-references)

## Script Approach

Create a Python script that:
1. Scans all markdown files in the `docs/` directory
2. Adds missing required sections
3. Identifies and suggests fixes for cross-references
4. Generates a report of remaining issues

This will automate the most tedious parts of the cleanup process.

## Validation

After each batch of fixes:
1. Run the validation script to check progress
2. Commit changes with descriptive messages
3. Document remaining issues for the next batch

## Modification History

| Date | Author | Description |
|------|--------|-------------|
| 2025-05-06 | Documentation Team | Created Phase 2 documentation cleanup plan | 