#!/usr/bin/env python3
"""
ETL script for processing proper names data from the TIPNR file.
This script extracts and loads proper names, their references, and relationships
into the database for enhanced Bible search and study.
"""

import os
import sys
import logging
import argparse
import psycopg2
from dotenv import load_dotenv
import re
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_proper_names.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('etl_proper_names')

def create_tables(conn):
    """Create the necessary tables for proper names if they don't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bible.proper_names (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL, -- Person, Place, Thing, etc.
                gender TEXT,
                title TEXT,
                description TEXT,
                short_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (name, type)
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bible.proper_name_forms (
                id SERIAL PRIMARY KEY,
                proper_name_id INTEGER NOT NULL REFERENCES bible.proper_names(id),
                language TEXT NOT NULL, -- Hebrew, Greek, etc.
                form TEXT NOT NULL,
                transliteration TEXT,
                strongs_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (proper_name_id, language, form)
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bible.proper_name_references (
                id SERIAL PRIMARY KEY,
                proper_name_form_id INTEGER NOT NULL REFERENCES bible.proper_name_forms(id),
                reference TEXT NOT NULL, -- Bible reference like Gen.1.1
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (proper_name_form_id, reference)
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bible.proper_name_relationships (
                id SERIAL PRIMARY KEY,
                source_name_id INTEGER NOT NULL REFERENCES bible.proper_names(id),
                target_name_id INTEGER NOT NULL REFERENCES bible.proper_names(id),
                relationship_type TEXT NOT NULL, -- parent, child, sibling, spouse, etc.
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (source_name_id, target_name_id, relationship_type)
            )
        """)
        
        # Create indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_proper_names_name
            ON bible.proper_names (name)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_proper_name_forms_form
            ON bible.proper_name_forms (form)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_proper_name_forms_strongs
            ON bible.proper_name_forms (strongs_id)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_proper_name_references_reference
            ON bible.proper_name_references (reference)
        """)
        
        conn.commit()
        logger.info("Proper names tables created or already exist")

def parse_proper_names_file(file_path, max_records=None):
    """
    Parse the TIPNR file to extract proper names and their references.
    
    The file has a complex format with multi-line records separated by '$' markers.
    Each record has a header line followed by multiple forms with references.
    
    Returns a list of dictionaries with the parsed data.
    
    Args:
        file_path: Path to the TIPNR file
        max_records: Optional limit on number of records to process (for testing)
    """
    names_data = []
    
    try:
        record_count = 0
        current_record = None
        
        with open(file_path, 'r', encoding='utf-8') as file:
            # Skip header until data starts
            for line in file:
                if line.startswith('$'):
                    break  # Found the first record marker
            
            # Process records
            for line in file:
                line = line.rstrip('\n')
                
                # New record starts
                if line.startswith('$'):
                    if current_record:
                        names_data.append(current_record)
                        record_count += 1
                        
                        if max_records and record_count >= max_records:
                            logger.info(f"Reached limit of {max_records} records")
                            break
                    
                    current_record = {
                        'name': '',
                        'type': '',
                        'gender': '',
                        'description': '',
                        'short_description': '',
                        'forms': [],
                        'relationships': []
                    }
                    continue
                
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Header line (first line of a record)
                if current_record and not current_record['name']:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        # Parse the name and type from the header
                        type_code = parts[0].strip()
                        name = parts[1].strip()
                        
                        # Determine type and gender from code
                        if 'N:N-M-P' in type_code:
                            current_record['type'] = 'Person'
                            current_record['gender'] = 'Male'
                        elif 'N:N-F-P' in type_code:
                            current_record['type'] = 'Person'
                            current_record['gender'] = 'Female'
                        elif 'N:N--L' in type_code:
                            current_record['type'] = 'Location'
                        elif 'N:N--T' in type_code:
                            current_record['type'] = 'Title'
                        else:
                            current_record['type'] = 'Other'
                        
                        current_record['name'] = name
                        
                        # Extract description if available
                        if len(parts) >= 3:
                            current_record['description'] = parts[2].strip()
                            # Abbreviated description for display
                            current_record['short_description'] = parts[2].strip()[:100] + '...' if len(parts[2].strip()) > 100 else parts[2].strip()
                        
                        # Extract relationships if available
                        if len(parts) >= 4 and parts[3].strip():
                            # Format is typically "father: Abraham; mother: Sarah; spouse: Rebecca"
                            rel_text = parts[3].strip()
                            rel_parts = rel_text.split(';')
                            
                            for rel_part in rel_parts:
                                rel_part = rel_part.strip()
                                if ':' in rel_part:
                                    rel_type, rel_target = rel_part.split(':', 1)
                                    current_record['relationships'].append({
                                        'type': rel_type.strip().lower(),
                                        'target': rel_target.strip()
                                    })
                    
                # Form lines (subsequent lines in a record, starting with a tab)
                elif current_record and line.startswith('\t'):
                    form_parts = line.lstrip('\t').split('\t')
                    
                    if len(form_parts) >= 3:
                        language_code = form_parts[0].strip()
                        form = form_parts[1].strip()
                        refs = form_parts[2].strip()
                        
                        # Determine language from code
                        language = 'Hebrew'
                        if language_code.startswith('G:') or language_code.startswith('A:'):
                            language = 'Greek'
                        elif language_code.startswith('A:'):
                            language = 'Aramaic'
                        
                        # Extract Strong's ID if present
                        strongs_id = None
                        strongs_match = re.search(r'[HG][0-9]{4}[a-zA-Z]?', language_code)
                        if strongs_match:
                            strongs_id = strongs_match.group(0)
                        
                        # Process references
                        references = []
                        if refs:
                            # Split references by semicolon and/or comma
                            ref_list = re.split(r'[;,]', refs)
                            for ref in ref_list:
                                ref = ref.strip()
                                if ref:
                                    references.append(ref)
                        
                        current_record['forms'].append({
                            'language': language,
                            'form': form,
                            'strongs_id': strongs_id,
                            'transliteration': form_parts[1].strip() if len(form_parts) > 1 else None,
                            'references': references
                        })
            
            # Add the last record if any
            if current_record and current_record['name']:
                names_data.append(current_record)
        
        logger.info(f"Parsed {len(names_data)} proper name records")
    
    except Exception as e:
        logger.error(f"Error parsing proper names file: {e}")
        raise
    
    return names_data

def load_proper_names_data(conn, names_data):
    """Load the parsed proper names data into the database."""
    try:
        records_loaded = 0
        forms_loaded = 0
        references_loaded = 0
        relationships_loaded = 0
        
        with conn.cursor() as cur:
            # Check if we need to clear existing data
            cur.execute("SELECT COUNT(*) FROM bible.proper_names")
            count = cur.fetchone()[0]
            if count > 0:
                logger.info(f"Found {count} existing proper names. Truncating tables to update with new data.")
                # Truncate tables in reverse order due to foreign key constraints
                cur.execute("TRUNCATE bible.proper_name_references CASCADE")
                cur.execute("TRUNCATE bible.proper_name_forms CASCADE")
                cur.execute("TRUNCATE bible.proper_name_relationships CASCADE")
                cur.execute("TRUNCATE bible.proper_names CASCADE")
                conn.commit()
            
            # First, create interim table for relationships if it doesn't exist
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS bible.proper_name_relationships_interim (
                        id SERIAL PRIMARY KEY,
                        source_name_id INTEGER NOT NULL,
                        target_name TEXT NOT NULL,
                        relationship_type TEXT NOT NULL
                    )
                """)
                conn.commit()
            except Exception as e:
                logger.error(f"Error creating interim relationships table: {e}")
            
            # Process each name record
            for name_record in names_data:
                try:
                    # Skip records with no name
                    if not name_record['name']:
                        continue
                    
                    # Check if this name+type already exists to avoid duplicates
                    cur.execute(
                        """
                        SELECT id FROM bible.proper_names
                        WHERE name = %s AND type = %s
                        """,
                        (name_record['name'], name_record['type'])
                    )
                    
                    existing_name = cur.fetchone()
                    if existing_name:
                        # Name already exists, use existing ID
                        name_id = existing_name[0]
                        logger.debug(f"Name '{name_record['name']}' already exists, using id {name_id}")
                    else:
                        # Insert the proper name
                        cur.execute(
                            """
                            INSERT INTO bible.proper_names 
                            (name, type, gender, description, short_description)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id
                            """,
                            (
                                name_record['name'],
                                name_record['type'],
                                name_record['gender'],
                                name_record['description'],
                                name_record['short_description']
                            )
                        )
                        name_id = cur.fetchone()[0]
                        records_loaded += 1
                    
                    # Insert the forms
                    for form in name_record['forms']:
                        cur.execute(
                            """
                            INSERT INTO bible.proper_name_forms 
                            (proper_name_id, language, form, transliteration, strongs_id)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id
                            """,
                            (
                                name_id,
                                form['language'],
                                form['form'],
                                form['transliteration'],
                                form['strongs_id']
                            )
                        )
                        form_id = cur.fetchone()[0]
                        forms_loaded += 1
                        
                        # Insert the references
                        for ref in form['references']:
                            cur.execute(
                                """
                                INSERT INTO bible.proper_name_references 
                                (proper_name_form_id, reference)
                                VALUES (%s, %s)
                                """,
                                (form_id, ref)
                            )
                            references_loaded += 1
                    
                    # Store relationships as an interim step before linking to actual targets
                    if name_record['relationships']:
                        for rel in name_record['relationships']:
                            # We'll need to resolve target names in a second pass
                            cur.execute(
                                """
                                INSERT INTO bible.proper_name_relationships_interim 
                                (source_name_id, target_name, relationship_type)
                                VALUES (%s, %s, %s)
                                """,
                                (name_id, rel['target'], rel['type'])
                            )
                            relationships_loaded += 1
                
                except Exception as e:
                    logger.warning(f"Error processing name '{name_record['name']}': {e}")
                    conn.rollback()
                    continue
                
                # Commit after each name to avoid losing all data on error
                conn.commit()
            
            logger.info(f"Loaded {records_loaded} proper names, {forms_loaded} forms, {references_loaded} references, {relationships_loaded} interim relationships")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading proper names data: {e}")
        raise

def resolve_name_relationships(conn):
    """Resolve the interim relationships to actual name IDs."""
    try:
        relationships_resolved = 0
        
        with conn.cursor() as cur:
            # Check if the interim table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'bible' 
                    AND table_name = 'proper_name_relationships_interim'
                )
            """)
            
            if not cur.fetchone()[0]:
                logger.warning("No interim relationships table found. Skipping relationship resolution.")
                return
            
            # Get all interim relationships
            cur.execute("""
                SELECT id, source_name_id, target_name, relationship_type 
                FROM bible.proper_name_relationships_interim
            """)
            
            interim_relationships = cur.fetchall()
            logger.info(f"Found {len(interim_relationships)} interim relationships to resolve")
            
            # Process each interim relationship
            for rel_id, source_id, target_name, rel_type in interim_relationships:
                # Try to find the target by name
                cur.execute("""
                    SELECT id FROM bible.proper_names
                    WHERE name = %s
                """, (target_name,))
                
                target_row = cur.fetchone()
                if target_row:
                    target_id = target_row[0]
                    
                    # Insert the resolved relationship
                    try:
                        cur.execute("""
                            INSERT INTO bible.proper_name_relationships
                            (source_name_id, target_name_id, relationship_type)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (source_name_id, target_name_id, relationship_type) DO NOTHING
                        """, (source_id, target_id, rel_type))
                        relationships_resolved += 1
                    except Exception as e:
                        logger.warning(f"Could not insert relationship {rel_id}: {e}")
            
            # Clean up the interim table
            cur.execute("DROP TABLE bible.proper_name_relationships_interim")
            
            conn.commit()
            logger.info(f"Resolved {relationships_resolved} relationships")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error resolving name relationships: {e}")
        raise

def main(file_path, max_records=None):
    """Main ETL process for proper names."""
    logger.info(f"Starting proper names ETL process with file: {file_path}")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return
        
        # Create tables
        create_tables(conn)
        
        # Parse the proper names file
        names_data = parse_proper_names_file(file_path, max_records)
        
        # Load data into database
        load_proper_names_data(conn, names_data)
        
        # Resolve name relationships
        resolve_name_relationships(conn)
        
        logger.info("Proper names ETL process completed successfully")
    
    except Exception as e:
        logger.error(f"Error in proper names ETL process: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process proper names data')
    parser.add_argument('--file', required=True, help='Path to the TIPNR file')
    parser.add_argument('--max', type=int, help='Maximum number of records to process (for testing)')
    args = parser.parse_args()
    
    main(args.file, args.max) 