#!/usr/bin/env python3
"""
Final Documentation Organization Script

This script implements the final documentation organization plan by:
1. Archiving process documents
2. Moving/renaming remaining documents to their proper locations
3. Creating necessary directories
4. Running the fix documentation script to update cross-references
"""

import os
import sys
import shutil
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DOCS_DIR = Path('docs')
ARCHIVE_DIR = DOCS_DIR / 'archive'
FEATURES_DIR = DOCS_DIR / 'features'
GUIDES_DIR = DOCS_DIR / 'guides'
REFERENCE_DIR = DOCS_DIR / 'reference'
RULES_DIR = DOCS_DIR / 'rules'
REFERENCE_RULES_DIR = REFERENCE_DIR / 'rules'
CURSOR_RULES_DIR = Path('.cursor/rules')
CURSOR_FEATURES_DIR = CURSOR_RULES_DIR / 'features'
CURSOR_STANDARDS_DIR = CURSOR_RULES_DIR / 'standards'

def ensure_directories():
    """Ensure all necessary directories exist."""
    directories = [
        ARCHIVE_DIR,
        FEATURES_DIR,
        GUIDES_DIR,
        REFERENCE_DIR,
        REFERENCE_RULES_DIR,
        CURSOR_FEATURES_DIR,
        CURSOR_STANDARDS_DIR,
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

def archive_process_documents():
    """Archive documentation process files."""
    process_docs = [
        'DOCUMENTATION_CLEANUP.md',
        'DOCUMENTATION_CLEANUP_PHASE2.md',
        'DOCUMENTATION_CLEANUP_PHASE2_COMPLETE.md',
        'DOCUMENTATION_UPDATE_PLAN.md',
        'DOCUMENTATION_CLEANUP_FINAL.md',  # Also archive our plan
    ]
    
    for doc in process_docs:
        source = DOCS_DIR / doc
        destination = ARCHIVE_DIR / doc
        
        if source.exists():
            shutil.copy2(source, destination)
            logger.info(f"Archived {source} to {destination}")
        else:
            logger.warning(f"Process document not found: {source}")

def organize_root_documents():
    """Organize remaining documents in the docs root."""
    moves = [
        ('gpvectorgrokhelp.md', REFERENCE_DIR / 'vector_search_reference.md'),
        ('STEPBible_Explorer_System_Build_Guide.md', GUIDES_DIR / 'system_build_guide.md'),
        ('TESTING_FRAMEWORK.md', GUIDES_DIR / 'testing_framework.md'),
        ('ORGANIZATION.md', REFERENCE_DIR / 'organization_reference.md'),
    ]
    
    for source_name, destination in moves:
        source = DOCS_DIR / source_name
        
        if source.exists():
            add_note_header(source, destination)
            logger.info(f"Moved {source} to {destination}")
        else:
            logger.warning(f"Document not found: {source}")

def organize_rules_documents():
    """Organize rules documentation."""
    rule_moves = [
        # Rule documents to features
        ('rules/etl_rules.md', FEATURES_DIR / 'etl_rules.md'),
        ('rules/fix_hebrew_strongs_ids_pattern.md', FEATURES_DIR / 'hebrew_processing.md'),
        
        # Rule documents to reference
        ('rules/CURSOR_RULES_GUIDE.md', REFERENCE_DIR / 'cursor_rules_guide.md'),
        ('rules/column_names.md', REFERENCE_DIR / 'rules/column_naming.md'),
        ('rules/database_rules.md', REFERENCE_DIR / 'rules/database_standards.md'),
        ('rules/import_rules.md', REFERENCE_DIR / 'rules/import_standards.md'),
        ('rules/compatibility_rules.md', REFERENCE_DIR / 'rules/compatibility_standards.md'),
    ]
    
    for source_rel_path, destination in rule_moves:
        source = DOCS_DIR / source_rel_path
        
        if source.exists():
            add_note_header(source, destination)
            logger.info(f"Moved {source} to {destination}")
        else:
            logger.warning(f"Rule document not found: {source}")

def add_note_header(source, destination):
    """Copy file with a note header indicating file was moved."""
    with open(source, 'r', encoding='utf-8') as src_file:
        content = src_file.read()
    
    header = f"""# {destination.stem.replace('_', ' ').title()}

> Note: This file was relocated from `{source.relative_to(Path('.'))}` as part of the documentation reorganization.

"""
    
    with open(destination, 'w', encoding='utf-8') as dest_file:
        dest_file.write(header + content)

def generate_rule_mapping():
    """Generate a rule mapping document showing old and new locations."""
    mapping_file = REFERENCE_DIR / 'rule_mapping.md'
    
    mapping_content = """# Rule Mapping Reference

This document provides a mapping between old rule locations and their new locations in the reorganized documentation structure.

## Documentation Rules

| Old Location | New Location |
|--------------|--------------|
| `docs/rules/etl_rules.md` | `docs/features/etl_rules.md` |
| `docs/rules/fix_hebrew_strongs_ids_pattern.md` | `docs/features/hebrew_processing.md` |
| `docs/rules/CURSOR_RULES_GUIDE.md` | `docs/reference/cursor_rules_guide.md` |
| `docs/rules/column_names.md` | `docs/reference/rules/column_naming.md` |
| `docs/rules/database_rules.md` | `docs/reference/rules/database_standards.md` |
| `docs/rules/import_rules.md` | `docs/reference/rules/import_standards.md` |
| `docs/rules/compatibility_rules.md` | `docs/reference/rules/compatibility_standards.md` |

## Cursor Rules

| Old Location | New Location |
|--------------|--------------|
| `.cursor/rules/database_access.mdc` | `.cursor/rules/standards/database_access.mdc` |
| `.cursor/rules/db_test_skip.mdc` | `.cursor/rules/standards/db_test_skip.mdc` |
| `.cursor/rules/dspy_generation.mdc` | `.cursor/rules/standards/dspy_generation.mdc` |
| `.cursor/rules/esv_bible_processing.mdc` | `.cursor/rules/features/esv_bible_processing.mdc` |
| `.cursor/rules/etl_rules.mdc` | `.cursor/rules/features/etl_rules.mdc` |
| `.cursor/rules/theological_terms.mdc` | `.cursor/rules/features/theological_terms.mdc` |
| `.cursor/rules/tvtms_expected_count.mdc` | `.cursor/rules/features/tvtms_expected_count.mdc` |
| `.cursor/rules/tvtms_txt_only.mdc` | `.cursor/rules/features/tvtms_txt_only.mdc` |
| `.cursor/rules/when_to_create_rules.mdc` | `.cursor/rules/standards/rule_creation_guide.mdc` |
"""
    
    with open(mapping_file, 'w', encoding='utf-8') as f:
        f.write(mapping_content)
    
    logger.info(f"Created rule mapping document: {mapping_file}")

def organize_cursor_rules():
    """Organize cursor rules into features and standards."""
    # Feature rules
    feature_rules = [
        'esv_bible_processing.mdc',
        'etl_rules.mdc', 
        'theological_terms.mdc',
        'tvtms_expected_count.mdc',
        'tvtms_txt_only.mdc'
    ]
    
    # Standard rules
    standard_rules = [
        ('database_access.mdc', 'database_access.mdc'),
        ('db_test_skip.mdc', 'db_test_skip.mdc'),
        ('dspy_generation.mdc', 'dspy_generation.mdc'),
        ('when_to_create_rules.mdc', 'rule_creation_guide.mdc')
    ]
    
    # Move feature rules
    for rule in feature_rules:
        source = CURSOR_RULES_DIR / rule
        destination = CURSOR_FEATURES_DIR / rule
        
        if source.exists() and not destination.exists():
            shutil.copy2(source, destination)
            logger.info(f"Organized cursor rule: {source} -> {destination}")
    
    # Move standard rules
    for source_name, dest_name in standard_rules:
        source = CURSOR_RULES_DIR / source_name
        destination = CURSOR_STANDARDS_DIR / dest_name
        
        if source.exists() and not destination.exists():
            shutil.copy2(source, destination)
            logger.info(f"Organized cursor rule: {source} -> {destination}")

def update_readme():
    """Update the docs README.md to reflect final organization."""
    readme_file = DOCS_DIR / 'README.md'
    
    content = """# BibleScholarProject Documentation

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
"""
    
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Updated documentation README: {readme_file}")

def run_fix_documentation():
    """Run the fix_documentation.py script to update cross-references."""
    try:
        logger.info("Running documentation fix script...")
        subprocess.run([sys.executable, 'scripts/fix_documentation.py'], check=True)
        logger.info("Fix documentation script completed successfully")
    except subprocess.CalledProcessError:
        logger.error("Error running fix documentation script")

def main():
    """Main function to run the organization process."""
    logger.info("Starting final documentation organization...")
    
    # Create necessary directories
    ensure_directories()
    
    # Archive process documents
    archive_process_documents()
    
    # Organize remaining documents
    organize_root_documents()
    organize_rules_documents()
    
    # Generate rule mapping
    generate_rule_mapping()
    
    # Organize cursor rules
    organize_cursor_rules()
    
    # Update README
    update_readme()
    
    # Run fix documentation script
    run_fix_documentation()
    
    logger.info("Documentation organization completed!")
    logger.info("Next steps:")
    logger.info("1. Run validation: python scripts/validate_documentation.py")
    logger.info("2. Fix any remaining issues")
    logger.info("3. Commit changes: git add docs/ .cursor/rules/ && git commit -m 'Complete documentation reorganization'")

if __name__ == "__main__":
    main() 