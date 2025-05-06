# Documentation Cleanup Plan

This document outlines the plan for cleaning up redundant or consolidated documentation files as part of the BibleScholarProject documentation reorganization.

## Overview

After consolidating documentation into the new structure (`features/`, `guides/`, `reference/`), several files in the root docs directory are now redundant and should be archived or deleted to avoid confusion and maintain a single source of truth.

## Files to Archive/Delete

These files have been consolidated into their new locations and can be deleted:

1. `docs/TESTING_FRAMEWORK.md` → Consolidated into `docs/guides/testing_framework.md`
2. `docs/DATA_VERIFICATION.md` → Consolidated into `docs/guides/data_verification.md`
3. `docs/etl_rules.md` → Consolidated into `docs/features/etl_pipeline.md`
4. `docs/ORGANIZATION.md` → Consolidated into `docs/reference/SYSTEM_ARCHITECTURE.md`
5. `docs/CURSOR_RULES_GUIDE.md` → Superseded by `.cursor/rules/README.md`
6. `docs/database_rules.md` → Consolidated into `docs/reference/DATABASE_SCHEMA.md`
7. `docs/import_rules.md` → Consolidated into `docs/rules/import_structure.md`
8. `docs/compatibility_rules.md` → Consolidated into feature-specific documentation

## Files to Verify Before Deletion

These files should be verified to ensure all their content has been properly consolidated before deletion:

1. `docs/column_names.md` → Verify all content is in `docs/reference/DATABASE_SCHEMA.md`
2. `docs/fix_hebrew_strongs_ids_pattern.md` → Verify all content is in `docs/features/theological_terms.md`

## Files to Keep

These files should be kept in the root docs directory:

1. `docs/README.md` - Main documentation index
2. `docs/CONTRIBUTING.md` - Contribution guidelines
3. `docs/DOCUMENTATION_UPDATE_PLAN.md` - Documentation plan (this file)
4. `docs/STEPBible_Explorer_System_Build_Guide.md` - Comprehensive system build guide

## Archiving Process

Before deleting any files, we should:

1. Create an archive folder at `docs/archive/`
2. Copy all files marked for deletion to this folder
3. Add a note at the top of each archived file indicating where the content has been moved
4. After verification, the archive folder can be removed in a future cleanup

## Verification Steps

Before deletion, perform these verification steps:

1. Review each file and its consolidated counterpart to ensure no information is lost
2. Run a documentation validation script to check for broken links
3. Verify that all cross-references have been updated
4. Check that the main README.md is updated with the correct links

## Implementation Timeline

1. Complete the consolidation of all files (Completed)
2. Verify all content has been properly migrated (In Progress)
3. Create the archive folder and copy files (Next Step)
4. Update README.md and cross-references (Next Step)
5. Delete redundant files after final verification (Future)

## Modification History

| Date | Author | Description |
|------|--------|-------------|
| 2025-06-10 | Documentation Team | Created documentation cleanup plan 