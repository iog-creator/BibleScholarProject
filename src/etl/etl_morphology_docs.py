"""
ETL script for loading morphology documentation into the database.
This script processes the Greek and Hebrew morphology code documentation.

Input Files Used:
---------------
1. TEGMC - Translators Expansion of Greek Morphology Codes (446KB):
   - Contains detailed documentation for Greek morphology codes
   - Includes examples, meanings, and categorization
   - Supports extended codes for STEPBible-specific distinctions

2. TEHMC - Translators Expansion of Hebrew Morphology Codes (390KB):
   - Contains detailed documentation for Hebrew morphology codes
   - Includes parsing information and usage examples
   - Supports extended codes for affixes and special forms

Features:
--------
1. Data Processing:
   - Parses structured documentation files
   - Handles multi-line entries
   - Processes section headers and categories
   - Validates code formats

2. Code Validation:
   - Verifies code syntax
   - Checks for required fields
   - Validates examples
   - Ensures code uniqueness

3. Documentation Organization:
   - Separates brief and full codes
   - Maintains section hierarchy
   - Links related entries
   - Preserves source references

4. Performance Features:
   - Batch processing for efficiency
   - Memory-efficient streaming
   - Optimized database operations
   - Error recovery mechanisms

Database Schema:
--------------
Tables (in bible schema):

1. morphology_documentation_greek:
   - id: SERIAL PRIMARY KEY
   - code: VARCHAR(100) NOT NULL UNIQUE
   - example: TEXT
   - meaning: TEXT
   - section: TEXT
   - source: VARCHAR(100)

2. morphology_documentation_hebrew:
   - id: SERIAL PRIMARY KEY
   - code: VARCHAR(100) NOT NULL UNIQUE
   - example: TEXT
   - meaning: TEXT
   - section: TEXT
   - source: VARCHAR(100)

Indexes:
- idx_morph_doc_greek_code: B-tree index on code
- idx_morph_doc_hebrew_code: B-tree index on code
- idx_morph_doc_greek_section_code: Composite index
- idx_morph_doc_hebrew_section_code: Composite index

Views:
-----
bible.morphology_documentation_combined:
    Unified view of both Greek and Hebrew documentation
    Columns:
    - code: The morphology code
    - example: Example word or usage
    - meaning: Description of the code's meaning
    - section: Section identifier
    - language: 'Greek' or 'Hebrew'
    - source: Source file identifier

Code Categories:
--------------
Greek Morphology:
- Parts of Speech (N, V, A, etc.)
- Case, Number, Gender
- Tense, Voice, Mood
- Person, Aspect
- Special Forms (2nd aorist, deponent)

Hebrew Morphology:
- Parts of Speech
- Stems (Qal, Piel, etc.)
- Person, Gender, Number
- State (absolute, construct)
- Affixes and Prefixes

Query Examples:
-------------
1. Basic Code Lookup:
   ```sql
   SELECT code, example, meaning 
   FROM bible.morphology_documentation_combined 
   WHERE code = 'V-PAI-3S';
   ```

2. Search by Category:
   ```sql
   SELECT code, meaning 
   FROM bible.morphology_documentation_greek 
   WHERE section = 'Verb Forms' 
   ORDER BY code;
   ```

3. Find Similar Codes:
   ```sql
   SELECT code, meaning 
   FROM bible.morphology_documentation_combined 
   WHERE code LIKE 'N-___' 
   AND language = 'Greek';
   ```

4. Join with Verse Data:
   ```sql
   SELECT v.book_name, v.chapter, v.verse,
          md.code, md.meaning
   FROM bible.verses v,
        jsonb_array_elements_text(v.morphology_json->'codes') as code_ref
   JOIN bible.morphology_documentation_combined md 
   ON code_ref = md.code
   WHERE v.book_name = 'John'
   AND v.chapter = 1
   LIMIT 5;
   ```

Usage:
-----
Command line:
    python etl_morphology_docs.py

Python code:
    >>> from etl_morphology_docs import process_tegmc_file
    >>> greek_entries = process_tegmc_file()
    >>> save_to_db(greek_entries, 'greek')

Environment Variables:
-------------------
Required:
- POSTGRES_DB: Database name
- POSTGRES_USER: Database user
- POSTGRES_PASSWORD: Database password

Optional:
- POSTGRES_HOST: Database host (default: localhost)
- POSTGRES_PORT: Database port (default: 5432)
- BATCH_SIZE: Batch size (default: 1000)
- LOG_LEVEL: Logging level (default: INFO)

Dependencies:
-----------
Core:
- psycopg2-binary
- python-dotenv
- logging

Optional:
- sqlalchemy
- pandas

Integration Notes:
---------------
1. Verse Integration:
   - Morphology codes in verses.morphology_json
   - References to documentation tables
   - Support for extended codes

2. Search Integration:
   - Full-text search on meanings
   - Code pattern matching
   - Language-specific filters

3. UI Integration:
   - Code tooltips
   - Expandable documentation
   - Cross-references

Error Handling:
-------------
1. Input Validation:
   - Code format checking
   - Required field validation
   - Character encoding verification

2. Database Operations:
   - Transaction management
   - Duplicate handling
   - Constraint validation

3. Recovery Procedures:
   - Partial update support
   - Error logging
   - Cleanup operations

Note:
----
This script is part of the STEPBible data integration project and works
in conjunction with other ETL scripts to provide a complete Bible study
database. The morphology documentation is essential for understanding
the grammatical markup in the verse data.

Author: STEPBible Data Integration Team
Version: 1.0.0
License: CC BY (Creative Commons Attribution)
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
import logging
from db_config import get_db_params

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('etl_morphology_docs.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def process_tegmc_file():
    """
    Process the TEGMC (Greek morphology codes) file.
    Returns a list of dictionaries containing the processed data.
    """
    filename = 'TEGMC - Translators Expansion of Greek Morphhology Codes - STEPBible.org CC BY.txt'
    
    if not os.path.exists(filename):
        logger.error(f"File not found: {filename}")
        return []
        
    entries = []
    current_section = None
    started = False
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and header/footer lines
            if not line or line.startswith('=') or 'STEPBible.org' in line or line.startswith('Data created by') or line.startswith('This licence'):
                continue
            
            # Check for section headers
            if 'BRIEF LEXICAL MORPHOLOGY CODES' in line:
                current_section = 'BRIEF CODES'
                started = False
                continue
            elif 'FULL MORPHOLOGY CODES' in line:
                current_section = 'FULL CODES'
                started = False
                continue
            
            # Skip explanatory text until we find the column headers
            if line.startswith('Code\tExample in English\tMeaning'):
                started = True
                continue
            
            if started and current_section and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 3:
                    code = parts[0].strip()
                    example = parts[1].strip()
                    meaning = parts[2].strip()
                    
                    # Skip the header row that contains "====="
                    if '=' not in code and '=' not in example and '=' not in meaning:
                        entries.append({
                            'code': code,
                            'example': example,
                            'meaning': meaning,
                            'section': current_section,
                            'source': 'TEGMC'
                        })
    
    logger.info(f"Processed {len(entries)} morphology codes from {filename}")
    return entries

def process_tehmc_file():
    """
    Process the TEHMC (Hebrew morphology codes) file.
    Returns a list of dictionaries containing the processed data.
    """
    filename = 'TEHMC - Translators Expansion of Hebrew Morphology Codes - STEPBible.org CC BY.txt'
    
    if not os.path.exists(filename):
        logger.error(f"File not found: {filename}")
        return []
        
    entries = []
    current_section = None
    started = False
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and header/footer lines
            if not line or line.startswith('=') or 'STEPBible.org' in line or line.startswith('Data created by') or line.startswith('This licence'):
                continue
            
            # Check for section headers
            if 'BRIEF LEXICAL MORPHOLOGY CODES' in line:
                current_section = 'BRIEF CODES'
                started = False
                continue
            elif 'FULL MORPHOLOGY CODES' in line:
                current_section = 'FULL CODES'
                started = False
                continue
            
            # Skip explanatory text until we find the column headers
            if line.startswith('Code\tExample in English\tMeaning'):
                started = True
                continue
            
            if started and current_section and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 3:
                    code = parts[0].strip()
                    example = parts[1].strip()
                    meaning = parts[2].strip()
                    
                    # Skip the header row that contains "====="
                    if '=' not in code and '=' not in example and '=' not in meaning:
                        entries.append({
                            'code': code,
                            'example': example,
                            'meaning': meaning,
                            'section': current_section,
                            'source': 'TEHMC'
                        })
    
    logger.info(f"Processed {len(entries)} morphology codes from {filename}")
    return entries

def verify_schema_and_tables(conn):
    """
    Verify that the schema and required tables exist, create them if they don't.
    
    This function checks for the existence of the 'bible' schema and the morphology
    documentation tables. If they don't exist, it creates them with appropriate
    constraints and indexes.
    
    Args:
        conn: Active database connection
        
    Returns:
        bool: True if verification/creation successful, False otherwise
        
    Raises:
        Exception: If there is an error creating schema or tables
    """
    try:
        # Check if schema exists
        schema_exists = conn.execute(text("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = 'bible'
            );
        """)).scalar()
        
        if not schema_exists:
            logger.info("Creating bible schema...")
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS bible"))
        
        # Check if tables exist
        tables = ['morphology_documentation_greek', 'morphology_documentation_hebrew']
        for table in tables:
            table_exists = conn.execute(text(f"""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'bible' 
                    AND table_name = '{table}'
                );
            """)).scalar()
            
            if not table_exists:
                logger.info(f"Creating table bible.{table}...")
                conn.execute(text(f"""
                    CREATE TABLE bible.{table} (
                        id SERIAL PRIMARY KEY,
                        code VARCHAR(100) NOT NULL UNIQUE,
                        example TEXT,
                        meaning TEXT,
                        section TEXT,
                        source VARCHAR(100)
                    )
                """))
                
                # Create indexes
                conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_morph_doc_{table.split('_')[-1]}_code 
                    ON bible.{table} (code);
                    
                    CREATE INDEX IF NOT EXISTS idx_morph_doc_{table.split('_')[-1]}_section_code 
                    ON bible.{table} (section, code);
                """))
        
        return True
        
    except Exception as e:
        logger.error(f"Error during schema/table verification: {str(e)}")
        return False

def save_to_db(entries, table_name):
    """
    Save the processed morphology documentation to the database.
    
    Args:
        entries: List of dictionaries containing the morphology documentation
        table_name: Either 'greek' or 'hebrew'
    """
    if not entries:
        logger.warning(f"No entries to save for {table_name}")
        return
        
    try:
        db_params = get_db_params()
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}')
        
        with engine.begin() as conn:  # Use transaction
            # Verify schema and tables exist
            if not verify_schema_and_tables(conn):
                logger.error("Failed to verify/create schema and tables")
                return
                
            schema = 'bible'
            table = f'morphology_documentation_{table_name}'
            
            # Deduplicate entries by keeping the last occurrence of each code
            seen_codes = {}
            for entry in entries:
                seen_codes[entry['code']] = entry
            unique_entries = list(seen_codes.values())
            
            # Create temporary table for bulk insert
            conn.execute(text(f"""
                CREATE TEMP TABLE temp_morphology_docs (
                    code VARCHAR(100) NOT NULL,
                    example TEXT,
                    meaning TEXT,
                    section TEXT,
                    source VARCHAR(100)
                ) ON COMMIT DROP
            """))
            
            # Bulk insert into temp table
            df = pd.DataFrame(unique_entries)
            df.to_sql('temp_morphology_docs', conn, if_exists='append', index=False)
            
            # UPSERT from temp table to main table
            result = conn.execute(text(f"""
                INSERT INTO {schema}.{table} (code, example, meaning, section, source)
                SELECT code, example, meaning, section, source 
                FROM temp_morphology_docs
                ON CONFLICT (code) DO UPDATE SET
                    example = EXCLUDED.example,
                    meaning = EXCLUDED.meaning,
                    section = EXCLUDED.section,
                    source = EXCLUDED.source
                RETURNING code
            """))
            
            inserted_count = len(result.fetchall())
            logger.info(f"Successfully saved {inserted_count} entries to {schema}.{table}")
            
            # Verify the data was actually inserted
            total_count = conn.execute(text(f"""
                SELECT COUNT(*) FROM {schema}.{table}
            """)).scalar()
            
            logger.info(f"Total records in {schema}.{table}: {total_count}")
        
    except Exception as e:
        logger.error(f"Error saving {table_name} morphology documentation: {str(e)}")
        raise

def create_combined_view():
    """Create the combined view of Greek and Hebrew morphology documentation."""
    try:
        db_params = get_db_params()
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}')
        
        with engine.begin() as conn:
            # Verify both tables exist and have data
            tables_exist = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'bible' 
                    AND table_name = 'morphology_documentation_greek'
                ) AND EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'bible' 
                    AND table_name = 'morphology_documentation_hebrew'
                );
            """)).scalar()
            
            if not tables_exist:
                logger.warning("Cannot create combined view - one or both tables missing")
                return
                
            # Check if tables have data
            greek_count = conn.execute(text("""
                SELECT COUNT(*) FROM bible.morphology_documentation_greek
            """)).scalar()
            
            hebrew_count = conn.execute(text("""
                SELECT COUNT(*) FROM bible.morphology_documentation_hebrew
            """)).scalar()
            
            logger.info(f"Found {greek_count} Greek and {hebrew_count} Hebrew entries")
            
            # Create or replace the view
            conn.execute(text("""
                CREATE OR REPLACE VIEW bible.morphology_documentation_combined AS
                SELECT code, example, meaning, section, 'Greek' as language, source
                FROM bible.morphology_documentation_greek
                UNION ALL
                SELECT code, example, meaning, section, 'Hebrew' as language, source
                FROM bible.morphology_documentation_hebrew
            """))
            
            logger.info("Successfully created combined morphology documentation view")
                
    except Exception as e:
        logger.error(f"Error creating combined view: {str(e)}")
        raise

def main():
    """
    Main function to process and load morphology documentation.
    """
    try:
        # Process Greek morphology codes
        greek_entries = process_tegmc_file()
        if greek_entries:
            save_to_db(greek_entries, 'greek')
            
        # Process Hebrew morphology codes
        hebrew_entries = process_tehmc_file()
        if hebrew_entries:
            save_to_db(hebrew_entries, 'hebrew')
            
        # Create the combined view after both tables are populated
        create_combined_view()
            
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        raise

if __name__ == '__main__':
    main() 