# Documentation Usage Guidelines

This document outlines the standards for documenting, referencing, and updating documentation in the BibleScholarProject.

## Finding Documentation

All project documentation is centralized in the `docs/` directory:

1. Start with `docs/README.md` for a comprehensive index of all documentation
2. For specific topics, consult the relevant documentation file:
   - API endpoints: `docs/API_REFERENCE.md`
   - Database schema: `docs/DATABASE_SCHEMA.md`
   - Development rules: `docs/rules/README.md`
   - Data verification: `docs/DATA_VERIFICATION.md`
   - Complete build guide: `docs/STEPBible_Explorer_System_Build_Guide.md`

## Documenting Code

When writing or modifying code, follow these documentation guidelines:

### Module Documentation

All modules should include:

```python
"""
Module for handling theological term processing.

This module provides functions to extract and validate theological terms,
with a focus on ensuring proper Strong's ID mapping.

Key functions:
- extract_strongs_id: Extract Strong's ID from grammar code
- validate_critical_terms: Validate minimum counts for critical terms
- get_theological_term_report: Generate term occurrence report
"""
```

### Function Documentation

All functions should include:

```python
def extract_strongs_id(grammar_code):
    """
    Extract Strong's ID from grammar_code field.
    
    Args:
        grammar_code (str): The grammar code containing Strong's ID
        
    Returns:
        str or None: The extracted Strong's ID in format H1234 or None if not found
        
    Raises:
        ValueError: If grammar_code format is invalid
        
    Example:
        >>> extract_strongs_id("{H1234}")
        "H1234"
    """
```

### Class Documentation

All classes should include:

```python
class TheologicalTermProcessor:
    """
    Process and validate theological terms.
    
    This class provides methods to extract, validate, and report on
    theological terms in biblical texts.
    
    Attributes:
        min_counts (dict): Dictionary of minimum required counts for terms
        connection (Connection): Database connection
    """
```

## Documentation Formats

### Markdown Conventions

* Use headers (`#`, `##`, `###`) for section organization
* Use code blocks (```) for code examples
* Use tables for structured data 
* Use bullet points and numbered lists for sequential instructions

### Code Examples

Always include complete, runnable examples:

```python
from src.database.connection import get_connection

def example_query():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bible.verses LIMIT 10")
        return cursor.fetchall()
```

## Referencing Documentation

When referencing documentation in code comments:

1. Use absolute paths from the project root:
   ```python
   # See docs/rules/theological_terms.md for term definitions
   ```

2. Reference specific sections when applicable:
   ```python
   # See "Database Access Patterns" in docs/rules/database_access.md
   ```

3. For critical rules, include the specific requirement:
   ```python
   # Per docs/rules/theological_terms.md, YHWH (H3068) must have ≥6,000 occurrences
   ```

## Updating Documentation

When making changes to code that affect functionality:

1. Update relevant documentation files
2. Add an entry to the change history section if present
3. Ensure examples in documentation match the updated code
4. Update any related .cursor/rules/*.mdc files

### When to Update Documentation

Documentation should be updated when:

* Adding new features or API endpoints
* Changing function signatures or behavior
* Modifying database schema
* Implementing new development patterns
* Fixing bugs in the documented behavior

### Documentation Review Process

Before submitting changes:

1. Ensure that documentation accuracy matches implementation
2. Check for broken links or references
3. Verify that code examples work as expected
4. Update any version numbers or dates

## Theological Term Documentation

Always consult `docs/rules/theological_terms.md` when working with Hebrew or Greek theological terms to ensure:

1. Proper Strong's ID mapping
2. Correct minimum occurrence requirements
3. Appropriate handling of term variants

Example of proper theological term documentation in code:

```python
# Critical terms from docs/rules/theological_terms.md
CRITICAL_TERMS = {
    "H430": {"name": "Elohim", "min_count": 2600},
    "H3068": {"name": "YHWH", "min_count": 6000},
    "H113": {"name": "Adon", "min_count": 335},
    "H2617": {"name": "Chesed", "min_count": 248},
    "H539": {"name": "Aman", "min_count": 100}
}
```

## API Documentation

When adding or modifying API endpoints:

1. Update `docs/API_REFERENCE.md` with the new endpoint details
2. Include:
   - HTTP method (GET, POST, etc.)
   - URL path
   - Parameters
   - Response format
   - Example request and response

## Database Documentation

When modifying the database schema:

1. Update `docs/DATABASE_SCHEMA.md` with new tables or columns
2. Document:
   - Column names and types
   - Foreign key relationships
   - Constraints and indexes
   - Expected data patterns

## Update History

| Date | Change | Author |
|------|--------|--------|
| 2025-05-05 | Initial documentation guideline creation | BibleScholar Team | 