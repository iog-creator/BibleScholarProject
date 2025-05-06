# Final Documentation Organization Plan

This document outlines the plan for organizing remaining documentation files in the BibleScholarProject.

## Current Documentation Structure

We've already implemented the main documentation structure:

```
docs/
├── features/          # Feature-specific documentation
├── guides/            # How-to guides for various tasks
├── reference/         # API references and system specs
├── archive/           # Old documentation (kept for reference)
└── rules/             # Documentation about rules (to be organized)
```

## Remaining Unorganized Documents

1. **Files in root `docs/` directory:**
   - `DOCUMENTATION_CLEANUP.md`, `DOCUMENTATION_CLEANUP_PHASE2.md`, `DOCUMENTATION_CLEANUP_PHASE2_COMPLETE.md` - Process documents
   - `DOCUMENTATION_UPDATE_PLAN.md` - Planning document
   - `gpvectorgrokhelp.md` - Vector search documentation
   - `STEPBible_Explorer_System_Build_Guide.md` - System build guide
   - `TESTING_FRAMEWORK.md` - Testing documentation
   - `ORGANIZATION.md` - Organization guidelines
   - Various rule documents still in the root

2. **Files in `docs/rules/` directory:**
   - Various rule documents that need to be organized based on their purpose

3. **Cursor rule files:**
   - `.cursor/rules/*.mdc` files that should be organized into features and standards directories

## Organization Plan

### 1. Archiving Process Documents

Move to `docs/archive/`:
- `DOCUMENTATION_CLEANUP.md`
- `DOCUMENTATION_CLEANUP_PHASE2.md`
- `DOCUMENTATION_CLEANUP_PHASE2_COMPLETE.md`
- `DOCUMENTATION_UPDATE_PLAN.md`

### 2. Organize Remaining Root Docs

Move to appropriate directories:
- `gpvectorgrokhelp.md` → `docs/reference/vector_search_reference.md` (cleaned up version)
- `STEPBible_Explorer_System_Build_Guide.md` → `docs/guides/system_build_guide.md`
- `TESTING_FRAMEWORK.md` → `docs/guides/testing_framework.md` (update as needed)
- `ORGANIZATION.md` → `docs/reference/organization_reference.md`

### 3. Organize Rules Documentation

Current rule documents should be moved to:
- `docs/features/` for feature-specific rules
- `docs/reference/rules/` for general rule documentation

Create a rule mapping document showing old → new locations.

### 4. Organize Cursor Rules

Continue organizing cursor rules into:
- `.cursor/rules/features/` for feature-specific rules
- `.cursor/rules/standards/` for standard/process rules

### 5. Fix Cross-References

Run the `fix_documentation.py` script to update all cross-references after moving files.

### 6. Documentation README Updates

Update the main `docs/README.md` to reflect the completed organization.

## Implementation Steps

1. Run the archiving script for process documents
2. Move and rename remaining documents according to plan
3. Update cross-references and links
4. Run validation script
5. Fix any broken links
6. Commit the changes

## Timeline

This final documentation clean-up should be completed before beginning the DSPy model training work to ensure all relevant documentation is properly organized. 