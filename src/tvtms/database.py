"""
Database connection management for TVTMS ETL.
"""

import logging
import os
from typing import List, Dict, Any
import psycopg
from psycopg import errors
from psycopg.rows import dict_row
# Remove psycopg2 import if not needed elsewhere, keep if used by other functions
# from psycopg2.extras import execute_values 
from .models import Mapping, Rule, Documentation
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

def get_db_connection() -> psycopg.Connection:
    """Get a PostgreSQL connection."""
    try:
        conn = psycopg.connect(os.getenv('DATABASE_URL'))
        conn.row_factory = dict_row
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def release_connection(conn):
    """Release a database connection."""
    if conn:
        try:
            conn.close()
        except Exception as e:
            logger.error(f"Failed to close connection: {e}")

def create_tables(conn) -> None:
    """Create database tables."""
    try:
        with conn.cursor() as cursor:
            # Create schema if not exists
            cursor.execute("CREATE SCHEMA IF NOT EXISTS bible;")
            
            # Create versification mappings table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bible.versification_mappings (
                id SERIAL PRIMARY KEY,
                source_tradition VARCHAR(50),
                target_tradition VARCHAR(50),
                source_book VARCHAR(20) NULL,
                source_chapter VARCHAR(10) NULL,
                source_verse INTEGER NULL,
                source_subverse VARCHAR(10) NULL,
                manuscript_marker VARCHAR(50),
                target_book VARCHAR(20),
                target_chapter VARCHAR(10) NULL,
                target_verse INTEGER,
                target_subverse VARCHAR(10),
                mapping_type VARCHAR(50),
                category VARCHAR(50),
                notes TEXT,
                source_range_note TEXT,
                target_range_note TEXT,
                note_marker VARCHAR(50),
                ancient_versions TEXT
            );
            """)
            
            # Create rules table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bible.rules (
                id SERIAL PRIMARY KEY,
                rule_type VARCHAR(50),
                source_tradition VARCHAR(50),
                target_tradition VARCHAR(50),
                pattern TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            # Create documentation table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bible.documentation (
                id SERIAL PRIMARY KEY,
                section VARCHAR(100),
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            conn.commit()
            logger.info("Successfully created tables")
            
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

def store_mappings(conn: psycopg.Connection, mappings: List[Mapping]) -> None:
    """Store validated versification mappings in the database using executemany."""
    if not mappings:
        logger.info("No mappings provided to store.")
        return

    # Prepare data tuples from Mapping objects
    data_to_insert = [
        (
            m.source_tradition,
            m.target_tradition,
            m.source_book,
            m.source_chapter,
            m.source_verse,
            m.source_subverse,
            m.manuscript_marker,
            m.target_book,
            m.target_chapter,
            m.target_verse,
            m.target_subverse,
            m.mapping_type,
            m.category,
            m.notes,
            m.source_range_note,
            m.target_range_note,
            m.note_marker,
            m.ancient_versions
        )
        for m in mappings
    ]

    # Define the columns in the correct order for the INSERT statement
    columns = (
        "source_tradition", "target_tradition", "source_book", "source_chapter",
        "source_verse", "source_subverse", "manuscript_marker", "target_book",
        "target_chapter", "target_verse", "target_subverse", "mapping_type",
        "category", "notes", "source_range_note", "target_range_note",
        "note_marker", "ancient_versions"
    )
    
    # Construct the SQL query with placeholders for executemany
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"""
        INSERT INTO bible.versification_mappings ({', '.join(columns)})
        VALUES ({placeholders})
    """

    # --- Remove Logging BEFORE executemany ---
    # if data_to_insert:
    #    logger.info(f"[TRACE store_mappings] Preparing {len(data_to_insert)} tuples for insert. First 5 tuples:")
    #    # Find the index of 'mapping_type' in the columns tuple
    #    try:
    #        mapping_type_index = columns.index("mapping_type")
    #        logger.info(f"[TRACE store_mappings] Columns: {columns}")
    #        logger.info(f"[TRACE store_mappings] Found 'mapping_type' at index: {mapping_type_index}")
    #        for i, data_tuple in enumerate(data_to_insert[:5]): # Log first 5
    #            type_val = data_tuple[mapping_type_index] if len(data_tuple) > mapping_type_index else 'INDEX OUT OF BOUNDS'
    #            logger.info(f"  [TRACE store_mappings] Tuple {i} (len={len(data_tuple)}): type='{type_val}'")
    #            # logger.info(f"    Full Tuple {i}: {data_tuple}") # Uncomment for very verbose logging
    #    except ValueError:
    #         logger.error("[TRACE store_mappings] 'mapping_type' column not found in tuple structure!")
    #    except IndexError as e:
    #         logger.error(f"[TRACE store_mappings] Error accessing tuple index for mapping_type: {e}")
    # else:
    #    logger.info("[TRACE store_mappings] No data_to_insert list.")
    # --- End Logging ---
    
    # Execute the batch insert

    try:
        with conn.cursor() as cur:
            cur.executemany(sql, data_to_insert)
            conn.commit()
            logger.info(f"Successfully stored {len(mappings)} mappings in bible.versification_mappings")
    except Exception as e:
        logger.error(f"Failed to store mappings using executemany: {e}")
        conn.rollback() # Roll back the transaction on error
        # Optionally re-raise the exception if the caller needs to handle it
        raise

def store_rules(conn: psycopg.Connection, rules: List[Dict[str, Any]]) -> None:
    """Store versification rules in the database."""
    try:
        with conn.cursor() as cur:
            # Create temporary table for bulk insert
            cur.execute("""
                CREATE TEMP TABLE temp_rules (
                    rule_id INTEGER,
                    rule_type VARCHAR(50),
                    source_tradition VARCHAR(50),
                    target_tradition VARCHAR(50),
                    pattern TEXT,
                    description TEXT
                )
            """)
            
            # Prepare data for bulk insert
            insert_data = [(
                r['rule_id'],
                r['rule_type'],
                r['source_tradition'],
                r['target_tradition'],
                r['pattern'],
                r['description']
            ) for r in rules]
            
            # Use executemany for batch insert
            cur.executemany(
                """
                INSERT INTO temp_rules (
                    rule_id, rule_type, source_tradition, target_tradition,
                    pattern, description
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                insert_data
            )
            
            # Use INSERT ON CONFLICT for upsert
            cur.execute("""
                INSERT INTO bible.versification_rules (
                    rule_id, rule_type, source_tradition, target_tradition,
                    pattern, description
                )
                SELECT rule_id, rule_type, source_tradition, target_tradition,
                       pattern, description
                FROM temp_rules t
                WHERE NOT EXISTS (
                    SELECT 1 FROM bible.versification_rules r
                    WHERE r.rule_id = t.rule_id
                )
            """)
            
            # Cleanup
            cur.execute("DROP TABLE temp_rules")
            conn.commit()
            
            # Update statistics
            cur.execute("ANALYZE bible.versification_rules")
            logger.info(f"Successfully stored {len(rules)} rules")
            
    except psycopg.Error as e:
        conn.rollback()
        logger.error(f"Error storing rules: {str(e)}")
        if hasattr(e, 'diag'):
            logger.error(f"Details: {e.diag.message_detail}")
        raise

def store_documentation(conn: psycopg.Connection, documentation: List[Dict[str, Any]]) -> None:
    """Store versification documentation in the database."""
    try:
        with conn.cursor() as cur:
            # Create temporary table for bulk insert
            cur.execute("""
                CREATE TEMP TABLE temp_documentation (
                    doc_id INTEGER,
                    doc_type VARCHAR(50),
                    content TEXT,
                    notes TEXT
                )
            """)
            
            # Prepare data for bulk insert
            insert_data = [(
                d['doc_id'],
                d['doc_type'],
                d['content'],
                d['notes']
            ) for d in documentation]
            
            # Use executemany for bulk insert
            cur.executemany(
                """
                INSERT INTO temp_documentation (
                    doc_id, doc_type, content, notes
                ) VALUES (%s, %s, %s, %s)
                """,
                insert_data
            )
            
            # Insert into final table
            cur.execute("""
                INSERT INTO bible.versification_documentation (
                    doc_id, doc_type, content, notes
                )
                SELECT doc_id, doc_type, content, notes
                FROM temp_documentation
                ON CONFLICT (doc_id) DO NOTHING
            """)
            
            # Drop temporary table
            cur.execute("DROP TABLE temp_documentation")
            
            conn.commit()
            logger.info(f"Successfully stored {len(documentation)} documentation entries")
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing documentation: {e}")
        raise 

def truncate_versification_mappings(conn: psycopg.Connection) -> None:
    """Truncate the bible.versification_mappings table."""
    table_name = "bible.versification_mappings"
    try:
        with conn.cursor() as cur:
            sql = f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;"
            logger.info(f"Executing: {sql}")
            cur.execute(sql)
        # Removed conn.commit() as it should be handled by the caller or context manager
        logger.info(f"Successfully truncated table {table_name}")
    except errors.UndefinedTable:
        logger.warning(f"Table {table_name} does not exist, skipping truncation.")
    except Exception as e:
        logger.error(f"Failed to truncate table {table_name}: {e}")
        # conn.rollback()
        raise

def fetch_valid_book_ids(conn):
    """Fetch all valid book IDs from the books table as a set."""
    with conn.cursor() as cur:
        cur.execute("SELECT book_id FROM bible.books")
        return set(row[0] for row in cur.fetchall())

# Example usage (demonstration)
# if __name__ == '__main__': 