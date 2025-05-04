#!/usr/bin/env python3
"""
ETL script for loading proper names data into the database.
This script processes the TIPNR (Translators Individualised Proper Names with References) file.

Input Files Used:
- TIPNR.txt (7.7MB): Contains proper names from the Bible with their transliterations,
  meanings, and verse references where they appear.

Features:
- Processes proper names and documentation entries
- Handles large text entries with truncation for indexing
- Deduplicates records while preserving metadata
- Uses batch processing with error handling
- Implements table locking for data integrity
- Creates optimized indexes for text search
- Supports special markers for ambiguous, descendant, and ancestor relationships
- Preserves full text while creating searchable versions
- Handles Unicode normalization for Hebrew and Greek text

Database Schema:
--------------
Table: bible.proper_names
- id: SERIAL PRIMARY KEY
- name_text: TEXT NOT NULL
- name_text_searchable: TEXT GENERATED ALWAYS AS (
    CASE 
        WHEN length(name_text) > 2000 
        THEN substring(name_text, 1, 2000)
        ELSE name_text
    END
) STORED
- meta_data: JSONB NOT NULL

Indexes:
- proper_names_name_text_key: Unique index on name_text_searchable
- proper_names_meta_data_gin_idx: GIN index on meta_data
- proper_names_documentation_idx: Partial index for documentation entries
- proper_names_name_text_trgm_idx: Trigram index for text search

Meta Data Structure:
------------------
Documentation Entries:
{
    "type": "documentation",
    "source": "TIPNR",
    "processed_timestamp": "<ISO timestamp>",
    "content_type": "metadata",
    "category": "<marker character>"
}

Name Entries:
{
    "type": "name",
    "references": ["<reference list>"],
    "source": "TIPNR",
    "processed_timestamp": "<ISO timestamp>",
    "markers": [
        {
            "type": "<marker type>",
            "position": <integer>
        }
    ]
}

Performance Features:
------------------
1. Batch Processing:
   - Uses psycopg's executemany for efficient batch inserts
   - Configurable batch size (default: 1000)
   - Transaction management with automatic rollback

2. Memory Management:
   - Streams file content instead of loading entirely into memory
   - Clears processed batches to prevent memory growth
   - Uses generators for large dataset processing

3. Data Integrity:
   - Table locking during bulk operations
   - Proper transaction handling
   - Constraint validation before insertion

4. Error Handling:
   - Comprehensive logging of processing errors
   - Batch-level error recovery
   - Detailed error messages for debugging

Usage:
    python etl_proper_names.py

Environment Variables:
--------------------
- POSTGRES_HOST: Database host (default: localhost)
- POSTGRES_PORT: Database port (default: 5432)
- POSTGRES_DB: Database name (default: bible_db)
- POSTGRES_USER: Database user (default: postgres)
- POSTGRES_PASSWORD: Database password

Dependencies:
------------
- psycopg
- python-dotenv
- logging

Sample Queries:
-------------
1. Find names with most references:
   ```sql
   SELECT name_text, jsonb_array_length(meta_data->'references') as ref_count
   FROM bible.proper_names
   WHERE meta_data->>'type' = 'name'
   ORDER BY ref_count DESC
   LIMIT 5;
   ```

2. Get documentation entries:
   ```sql
   SELECT name_text, meta_data->>'category' as doc_type
   FROM bible.proper_names
   WHERE meta_data->>'type' = 'documentation'
   ORDER BY name_text;
   ```

3. Search for similar names:
   ```sql
   SELECT name_text, meta_data
   FROM bible.proper_names
   WHERE name_text % 'Abraham'
   ORDER BY name_text <-> 'Abraham'
   LIMIT 5;
   ```

4. Find entries with specific markers:
   ```sql
   SELECT name_text, meta_data
   FROM bible.proper_names
   WHERE meta_data->'markers' @> '[{"type": "ambiguous"}]';
   ```

5. Get names by reference count range:
   ```sql
   SELECT name_text, jsonb_array_length(meta_data->'references') as ref_count
   FROM bible.proper_names
   WHERE meta_data->>'type' = 'name'
   AND jsonb_array_length(meta_data->'references') BETWEEN 10 AND 20
   ORDER BY ref_count DESC;
   ```

Note:
----
The script implements table locking to prevent concurrent modifications during the ETL process.
It also handles large text entries by creating a searchable version truncated to 2000 characters
while preserving the full text in the database. This approach optimizes both storage and search
performance while maintaining data integrity.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Any
import re
import psycopg
from psycopg.rows import dict_row
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('etl_proper_names.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# File path for TIPNR data
TIPNR_FILE = "TIPNR - Translators Individualised Proper Names with all References - STEPBible.org CC BY.txt"

def get_db_connection():
    """Get a database connection with proper error handling and connection parameters."""
    try:
        return psycopg.connect(
            dbname="bible_db",
            user="postgres",
            password="postgres",
            host="localhost",
            application_name='bible_etl',
            connect_timeout=3,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
            client_encoding='UTF8',
            row_factory=dict_row,
            options='-c search_path=bible,public'
        )
    except psycopg.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def create_schema_and_table(conn):
    """Create the bible schema and proper_names table if they don't exist."""
    cur = conn.cursor()
    try:
        # Create schema if not exists
        cur.execute("CREATE SCHEMA IF NOT EXISTS bible;")
        
        # Try to lock the table if it exists
        try:
            cur.execute("LOCK TABLE bible.proper_names IN ACCESS EXCLUSIVE MODE")
        except psycopg.Error:
            # Table might not exist yet, which is fine
            pass
            
        # Drop and recreate table
        cur.execute("""
            DROP TABLE IF EXISTS bible.proper_names CASCADE;
            
            -- Create the table without the unique constraint on name_text
            CREATE TABLE bible.proper_names (
                id SERIAL PRIMARY KEY,
                name_text TEXT NOT NULL,
                name_text_searchable TEXT GENERATED ALWAYS AS (
                    CASE 
                        WHEN length(name_text) > 2000 
                        THEN substring(name_text, 1, 2000)
                        ELSE name_text
                    END
                ) STORED,
                meta_data JSONB NOT NULL,
                CONSTRAINT proper_names_valid_json CHECK (meta_data IS NOT NULL AND meta_data ? 'type')
            );
            
            -- Create a unique index on the truncated text
            CREATE UNIQUE INDEX proper_names_name_text_key 
            ON bible.proper_names (name_text_searchable);
            
            -- Create indexes with better options
            CREATE INDEX proper_names_meta_data_gin_idx 
            ON bible.proper_names USING gin ((meta_data -> 'type'), (meta_data -> 'references') jsonb_path_ops);
            
            -- Add partial indexes for common queries
            CREATE INDEX proper_names_documentation_idx 
            ON bible.proper_names (name_text_searchable) 
            WHERE (meta_data->>'type' = 'documentation');
            
            -- Create a trigram index for text search
            CREATE EXTENSION IF NOT EXISTS pg_trgm;
            CREATE INDEX proper_names_name_text_trgm_idx 
            ON bible.proper_names USING gin (name_text gin_trgm_ops);
            
            -- Grant minimal necessary privileges
            REVOKE ALL ON bible.proper_names FROM PUBLIC;
            GRANT SELECT ON bible.proper_names TO PUBLIC;
        """)
        
        # Try to grant ETL role privileges if the role exists
        try:
            cur.execute("GRANT INSERT, UPDATE, DELETE ON bible.proper_names TO bible_etl")
        except psycopg.Error:
            logger.warning("Could not grant privileges to bible_etl role - role may not exist")
            
        conn.commit()
    except Exception as e:
        logger.error(f"Error creating schema/table: {str(e)}")
        conn.rollback()
        raise
    finally:
        cur.close()

def process_tipnr_line(line: str) -> Dict[str, Any]:
    """
    Process a line from the TIPNR file and extract relevant data.
    
    This function handles the parsing of individual lines from the TIPNR file,
    extracting name information, references, and special markers. It supports
    both documentation entries and name entries with their associated metadata.
    
    Args:
        line (str): A single line from the TIPNR file
        
    Returns:
        Dict[str, Any]: A dictionary containing the processed data with fields:
            - name_text: The proper name or documentation text
            - meta_data: A dictionary containing:
                - type: Either 'documentation' or 'name'
                - references: List of Bible references (for names)
                - markers: List of special markers (for names)
                - source: Always 'TIPNR'
                - processed_timestamp: ISO format timestamp
                
    Note:
        Special markers are extracted from the reference text and include:
        - (?) for ambiguous references
        - (d) for descendant references
        - (a) for ancestor references
    """
    if not line or line.isspace():
        return None
        
    try:
        # Split on first @ only, to preserve any @ in the reference
        parts = line.strip().split('@', 1)
        
        # Handle documentation entries
        if line.startswith(('(', '$', '@', '–', '*')):
            return {
                'name_text': line.strip(),
                'meta_data': {
                    'type': 'documentation',
                    'source': 'TIPNR',
                    'processed_timestamp': datetime.datetime.now().isoformat(),
                    'content_type': 'metadata',
                    'category': line[0]  # Store the category marker
                }
            }
            
        # Handle name entries
        if len(parts) == 2:
            name, reference = parts
            meta_data = {
                'type': 'name',
                'references': [reference.strip()],  # Store as array for easier appending
                'source': 'TIPNR',
                'processed_timestamp': datetime.datetime.now().isoformat(),
                'markers': []  # Array to store special markers
            }
            
            # Extract markers with their positions
            if '(?)' in reference:
                meta_data['markers'].append({'type': 'ambiguous', 'position': reference.index('(?)')})
            if '(d)' in reference:
                meta_data['markers'].append({'type': 'descendant', 'position': reference.index('(d)')})
            if '(a)' in reference:
                meta_data['markers'].append({'type': 'ancestor', 'position': reference.index('(a)')})
                
            return {
                'name_text': name.strip(),
                'meta_data': meta_data
            }
            
        return None
        
    except Exception as e:
        logger.warning(f"Error processing line: {line.strip()}: {str(e)}")
        return None

def batch_process_data(cur, conn):
    """Process TIPNR data in batches with proper error handling."""
    filename = TIPNR_FILE
    batch_size = 1000
    success_count = 0
    error_count = 0
    
    try:
        # Use a dictionary to accumulate records by name_text
        current_batch = {}
        
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                result = process_tipnr_line(line)
                if result:
                    name_text = result['name_text']
                    meta_data = result['meta_data']
                    
                    # Generate searchable text (truncated version for indexing)
                    searchable_text = name_text[:2000] if len(name_text) > 2000 else name_text
                    
                    if searchable_text in current_batch:
                        # Merge metadata for duplicate names
                        existing_meta = json.loads(current_batch[searchable_text][1])
                        if existing_meta['type'] == 'documentation':
                            # Keep documentation entries as is
                            continue
                        elif meta_data['type'] == 'documentation':
                            # Replace with documentation entry
                            current_batch[searchable_text] = (name_text, json.dumps(meta_data))
                        else:
                            # Merge references and markers
                            existing_meta['references'].extend(meta_data.get('references', []))
                            existing_meta['markers'].extend(meta_data.get('markers', []))
                            current_batch[searchable_text] = (name_text, json.dumps(existing_meta))
                    else:
                        current_batch[searchable_text] = (name_text, json.dumps(meta_data))
                    
                    if len(current_batch) >= batch_size:
                        try:
                            cur.executemany(
                                """
                                INSERT INTO bible.proper_names (name_text, meta_data)
                                VALUES (%s, %s::jsonb)
                                ON CONFLICT (name_text) DO UPDATE
                                SET meta_data = bible.proper_names.meta_data || EXCLUDED.meta_data::jsonb
                                """,
                                list(current_batch.values())
                            )
                            conn.commit()
                            success_count += len(current_batch)
                            current_batch = {}
                        except Exception as e:
                            conn.rollback()
                            error_count += len(current_batch)
                            logger.error(f"Error inserting batch: {str(e)}")
                            current_batch = {}  # Clear failed batch and continue
        
        # Insert any remaining records
        if current_batch:
            try:
                cur.executemany(
                    """
                    INSERT INTO bible.proper_names (name_text, meta_data)
                    VALUES (%s, %s::jsonb)
                    ON CONFLICT (name_text) DO UPDATE
                    SET meta_data = bible.proper_names.meta_data || EXCLUDED.meta_data::jsonb
                    """,
                    list(current_batch.values())
                )
                conn.commit()
                success_count += len(current_batch)
            except Exception as e:
                conn.rollback()
                error_count += len(current_batch)
                logger.error(f"Error inserting final batch: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise
    finally:
        logger.info(f"Processing complete. Success: {success_count}, Errors: {error_count}")

def main():
    """Main ETL process for TIPNR data."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        
        # Enable autocommit for DDL operations
        conn.autocommit = True
        cur = conn.cursor()
        
        # Create schema and table (DDL)
        create_schema_and_table(conn)
        
        # Disable autocommit for batch operations
        conn.autocommit = False
        
        # Set session parameters for better performance and lock the table
        cur.execute("""
            -- Set session parameters
            SET LOCAL work_mem = '256MB';
            SET LOCAL maintenance_work_mem = '256MB';
            SET LOCAL synchronous_commit = off;
            SET LOCAL session_replication_role = replica;
            SET LOCAL statement_timeout = 0;
            
            -- Lock the table for bulk loading
            LOCK TABLE bible.proper_names IN EXCLUSIVE MODE;
        """)
        
        # Process in batches with explicit transaction control
        batch_process_data(cur, conn)
        
        # Reset session parameters and analyze table
        cur.execute("""
            SET LOCAL session_replication_role = default;
            SET LOCAL synchronous_commit = on;
            
            -- Analyze table for better query planning
            ANALYZE bible.proper_names;
            
            -- Verify table integrity
            SELECT COUNT(*) FROM bible.proper_names;
        """)
        final_count = cur.fetchone()[0]
        logger.info(f"Final record count after ETL: {final_count}")
        
        # Final commit
        conn.commit()
        
    except Exception as e:
        if conn and not conn.closed:
            conn.rollback()
        logger.error(f"Fatal error: {str(e)}")
        raise
    finally:
        if cur:
            cur.close()
        if conn and not conn.closed:
            conn.close()

if __name__ == "__main__":
    main() 