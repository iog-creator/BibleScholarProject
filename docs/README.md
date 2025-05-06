# BibleScholarProject Documentation

Welcome to the BibleScholarProject documentation. This project provides tools for advanced Bible research and analysis with a focus on computational linguistics and theological term analysis.

## Documentation Index

### Core Documentation

- [**STEPBible Explorer System Build Guide**](STEPBible_Explorer_System_Build_Guide.md) - Comprehensive guide to the system
- [**API Reference**](API_REFERENCE.md) - Complete documentation of API endpoints
- [**Database Schema**](DATABASE_SCHEMA.md) - Database structure and relationships
- [**Data Verification**](DATA_VERIFICATION.md) - Data verification processes and procedures
- [**Documentation Usage**](rules/documentation_usage.md) - Guidelines for using and maintaining documentation

### Development Guidelines

- [**Rules Overview**](rules/README.md) - Index of all development and processing rules
- [**DSPy Training Guide**](dspy_training_guide.md) - Guide for AI training data generation

### Rules Documentation

#### Theological Rules
- [**Theological Terms**](rules/theological_terms.md) - Guidelines for theological term handling
- [**Hebrew Rules**](rules/hebrew_rules.md) - Special handling rules for Hebrew text

#### ETL and Data Processing
- [**ETL Rules**](rules/etl_rules.md) - Standards for data extraction and loading
- [**TVTMS Rules**](rules/tvtms_rules.md) - Versification mapping guidelines
- [**Parser Strictness**](rules/parser_strictness.md) - Parser configuration guidelines

#### Database Rules
- [**Database Access**](rules/database_access.md) - Database access patterns
- [**Database Testing**](rules/db_test_skip.md) - Database testing guidelines

#### Development Standards
- [**Import Structure**](rules/import_structure.md) - Python import organization
- [**DataFrame Handling**](rules/dataframe_handling.md) - Pandas operations guidelines
- [**Model Validation**](rules/model_validation.md) - ML model validation standards

### AI Integration

- [**DSPy Generation**](rules/dspy_generation.md) - DSPy training data generation guidelines
- [**Cursor Rules**](./.cursor/rules/README.md) - AI-assisted development rules

## Quick Start

To get started with the BibleScholarProject:

1. Set up your database:
   ```
   python check_db_schema.py
   ```

2. Start the API server:
   ```
   python src/api/lexicon_api.py
   ```

3. Start the web interface:
   ```
   python src/web_app.py
   ```

## API Endpoints

The main API endpoints are:

- `/api/theological_terms_report` - Report on theological terms
- `/api/lexicon/hebrew/validate_critical_terms` - Validate critical Hebrew terms
- `/api/cross_language/terms` - Cross-language terms comparison

See the [API Reference](API_REFERENCE.md) for complete documentation.

## Theological Term Analysis

The project focuses on analyzing key theological terms across languages:

| Term | Hebrew | Strong's ID | Minimum Required Count |
|------|--------|-------------|------------------------|
| Elohim | אלהים | H430 | 2,600 |
| YHWH | יהוה | H3068 | 6,000 |
| Adon | אדון | H113 | 335 |
| Chesed | חסד | H2617 | 248 |
| Aman | אמן | H539 | 100 |

See [Theological Terms](rules/theological_terms.md) for more details.

## Database Access

All database access should follow the patterns in the [Database Access](rules/database_access.md) guidelines:

```python
from src.database.connection import get_connection

def example_query():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bible.verses LIMIT 10")
        return cursor.fetchall()
```

## Contributing

When contributing to this project, please follow the guidelines in the [Rules Overview](rules/README.md) document. 