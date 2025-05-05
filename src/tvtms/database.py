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
from contextlib import contextmanager
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, insert
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError

from src.database.connection import get_engine as get_db_engine

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
                source_tradition VARCHAR(200),
                target_tradition VARCHAR(200),
                source_book VARCHAR(20) NULL,
                source_chapter VARCHAR(10) NULL,
                source_verse INTEGER NULL,
                source_subverse VARCHAR(10) NULL,
                manuscript_marker VARCHAR(200),
                target_book VARCHAR(20),
                target_chapter VARCHAR(10) NULL,
                target_verse INTEGER,
                target_subverse VARCHAR(10),
                mapping_type VARCHAR(200),
                category VARCHAR(200),
                notes TEXT,
                source_range_note TEXT,
                target_range_note TEXT,
                note_marker VARCHAR(200),
                ancient_versions TEXT
            );
            """)
            
            # Create versification rules table (with correct columns and PK)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bible.versification_rules (
                rule_id INTEGER PRIMARY KEY,
                rule_type VARCHAR(200),
                source_tradition VARCHAR(200),
                target_tradition VARCHAR(200),
                pattern TEXT,
                description TEXT
            );
            """)
            
            # Create versification documentation table (with correct columns and PK)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bible.versification_documentation (
                doc_id INTEGER PRIMARY KEY,
                doc_type VARCHAR(200),
                content TEXT,
                notes TEXT
            );
            """)
            
            conn.commit()
            logger.info("Successfully created tables")
            
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

def store_mappings(mappings, conn=None):
    """
    Store the versification mappings in the database.
    
    Args:
        mappings (list): List of Mapping objects to store.
        conn (Connection, optional): Database connection. If not provided, a new connection will be created.
        
    Returns:
        int: Number of mappings stored.
    """
    if not mappings:
        logger.error("No mappings to store")
        return 0
        
    logger.info(f"Storing {len(mappings)} mappings in database")
    
    # If a connection was provided, use it directly (for tests)
    if conn is not None:
        try:
            # Connection could be SQLAlchemy ConnectionFairy or psycopg Connection
            if hasattr(conn, 'cursor'):  # psycopg Connection
                with conn.cursor() as cur:
                    # Clear existing mappings
                    cur.execute("DELETE FROM bible.versification_mappings")
                    
                    # Convert mappings to dictionaries
                    mapping_dicts = []
                    for mapping in mappings:
                        mapping_dict = mapping.to_dict() if hasattr(mapping, 'to_dict') else mapping
                        mapping_dicts.append(mapping_dict)
                    
                    # Get column names from the first mapping
                    if mapping_dicts:
                        columns = list(mapping_dicts[0].keys())
                        columns_str = ", ".join(columns)
                        placeholders = ", ".join(["%s"] * len(columns))
                        
                        # Insert the mappings
                        for mapping_dict in mapping_dicts:
                            # Ensure values are in the same order as columns
                            values = [mapping_dict.get(col) for col in columns]
                            try:
                                cur.execute(
                                    f"INSERT INTO bible.versification_mappings ({columns_str}) VALUES ({placeholders})",
                                    values
                                )
                            except Exception as e:
                                logger.error(f"Error inserting mapping: {e}")
                                logger.error(f"Problematic values: {values}")
                                continue
                        
                        # Commit changes explicitly for the psycopg connection
                        conn.commit()
                        
                        # Return the count
                        cur.execute("SELECT COUNT(*) FROM bible.versification_mappings")
                        count = cur.fetchone()[0]
                        logger.info(f"Total mappings in database after insertion: {count}")
                        return count
                    return 0
            else:  # SQLAlchemy ConnectionFairy
                # Use text for parameterized queries
                conn.execute(text("DELETE FROM bible.versification_mappings"))
                
                # Convert mappings to dictionaries
                mapping_dicts = []
                for mapping in mappings:
                    mapping_dict = mapping.to_dict() if hasattr(mapping, 'to_dict') else mapping
                    mapping_dicts.append(mapping_dict)
                
                # Get column names from the first mapping
                if mapping_dicts:
                    columns = list(mapping_dicts[0].keys())
                    columns_str = ", ".join(columns)
                    placeholders = ", ".join([f":{col}" for col in columns])
                    
                    # Insert the mappings
                    for mapping_dict in mapping_dicts:
                        try:
                            conn.execute(
                                text(f"INSERT INTO bible.versification_mappings ({columns_str}) VALUES ({placeholders})"),
                                mapping_dict
                            )
                        except Exception as e:
                            logger.error(f"Error inserting mapping with SQLAlchemy: {e}")
                            logger.error(f"Problematic values: {mapping_dict}")
                            continue
                    
                    # Commit the transaction
                    conn.commit()
                    
                    # Return the count
                    result = conn.execute(text("SELECT COUNT(*) FROM bible.versification_mappings"))
                    count = result.scalar()
                    logger.info(f"Total mappings in database after insertion: {count}")
                    return count
                return 0
        except Exception as e:
            logger.error(f"Error storing mappings with provided connection: {e}")
            if hasattr(conn, 'rollback'):
                conn.rollback()
            return 0
    
    # Otherwise, use SQLAlchemy (normal operation path)
    engine = get_db_engine()
    
    try:
        # Ensure tables exist
        create_tables_if_not_exist(engine)
        
        # Clear existing mappings
        with engine.connect() as conn:
            try:
                clear_result = conn.execute(text("DELETE FROM bible.versification_mappings"))
                conn.commit()
                logger.info(f"Cleared {clear_result.rowcount} existing mappings")
            except SQLAlchemyError as e:
                conn.rollback()
                logger.error(f"Error clearing existing mappings: {e}")
                return 0
        
        # Convert mappings to dictionaries for insertion
        mappings_dicts = []
        for mapping in mappings:
            mapping_dict = mapping.to_dict() if hasattr(mapping, 'to_dict') else mapping
            mappings_dicts.append(mapping_dict)
        
        # Insert mappings in batches
        batch_size = 500
        for i in range(0, len(mappings_dicts), batch_size):
            batch = mappings_dicts[i:i+batch_size]
            with engine.connect() as conn:
                try:
                    # Get column names from the first mapping
                    columns = list(batch[0].keys())
                    
                    # Build the SQL query
                    placeholders = ", ".join([f":{col}" for col in columns])
                    columns_str = ", ".join(columns)
                    query = f"INSERT INTO bible.versification_mappings ({columns_str}) VALUES ({placeholders})"
                    
                    # Log a sample query for debugging
                    if i == 0:
                        sample_values = ", ".join([f"'{batch[0][col]}'" if batch[0][col] is not None else "NULL" for col in columns])
                        logger.info(f"Sample INSERT: INSERT INTO bible.versification_mappings ({columns_str}) VALUES ({sample_values})")
                    
                    # Execute the batch
                    result = conn.execute(text(query), batch)
                    conn.commit()
                    logger.info(f"Inserted batch {i//batch_size + 1}/{(len(mappings_dicts)+batch_size-1)//batch_size} with {result.rowcount} rows")
                except SQLAlchemyError as e:
                    conn.rollback()
                    logger.error(f"Error inserting batch {i//batch_size + 1}: {e}")
                    # Try inserting one by one to isolate problematic records
                    failed_records = 0
                    for j, record in enumerate(batch):
                        try:
                            with engine.connect() as conn2:
                                result = conn2.execute(text(query), [record])
                                conn2.commit()
                                logger.info(f"Successfully inserted record {j} individually")
                        except SQLAlchemyError as e2:
                            failed_records += 1
                            if failed_records <= 5:  # Limit the number of logs
                                logger.error(f"Error inserting record {j}: {e2}")
                                logger.error(f"Problematic record: {record}")
                    
                    if failed_records > 5:
                        logger.error(f"...and {failed_records - 5} more failed records")
        
        # Verify insertion
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM bible.versification_mappings"))
            count = result.scalar()
            logger.info(f"Total mappings in database after insertion: {count}")
            return count
            
    except Exception as e:
        logger.error(f"Unexpected error storing mappings: {e}")
        return 0

def store_rules(rules: List[Dict[str, Any]], conn=None) -> None:
    """
    Store versification rules in the database.
    
    Args:
        rules (List[Dict[str, Any]]): List of Rule objects to store.
        conn (Connection, optional): Database connection. If not provided, a new connection will be created.
    """
    if not rules:
        logger.warning("No rules to store")
        return
        
    logger.info(f"Storing {len(rules)} versification rules")
    
    # If a connection was provided, use it directly
    if conn is not None:
        try:
            # Connection could be SQLAlchemy ConnectionFairy or psycopg Connection
            if hasattr(conn, 'cursor'):  # psycopg Connection
                with conn.cursor() as cur:
                    for rule in rules:
                        rule_dict = rule.to_dict() if hasattr(rule, 'to_dict') else rule
                        
                        # Check if rule already exists
                        cur.execute("""
                        SELECT 1 FROM bible.versification_rules r
                        WHERE r.rule_id = %s
                        """, (rule_dict['rule_id'],))
                        
                        rule_exists = cur.fetchone() is not None
                        
                        if rule_exists:
                            # Update existing rule
                            columns = list(rule_dict.keys())
                            set_clause = ", ".join([f"{col} = %s" for col in columns])
                            values = [rule_dict[col] for col in columns]
                            values.append(rule_dict['rule_id'])  # For the WHERE clause
                            
                            cur.execute(f"""
                            UPDATE bible.versification_rules
                            SET {set_clause}
                            WHERE rule_id = %s
                            """, values)
                        else:
                            # Insert new rule
                            columns = list(rule_dict.keys())
                            columns_str = ", ".join(columns)
                            placeholders = ", ".join(["%s"] * len(columns))
                            values = [rule_dict[col] for col in columns]
                            
                            cur.execute(f"""
                            INSERT INTO bible.versification_rules (
                                {columns_str}
                            ) VALUES (
                                {placeholders}
                            )
                            """, values)
                
                    cur.execute("ANALYZE bible.versification_rules")
                    conn.commit()
            else:  # SQLAlchemy ConnectionFairy
                for rule in rules:
                    rule_dict = rule.to_dict() if hasattr(rule, 'to_dict') else rule
                    
                    # Check if rule already exists
                    result = conn.execute(
                        text("SELECT 1 FROM bible.versification_rules r WHERE r.rule_id = :rule_id"),
                        {"rule_id": rule_dict['rule_id']}
                    )
                    rule_exists = result.scalar() is not None
                    
                    if rule_exists:
                        # Update existing rule
                        columns = list(rule_dict.keys())
                        set_clause = ", ".join([f"{col} = :{col}" for col in columns])
                        
                        conn.execute(
                            text(f"""
                            UPDATE bible.versification_rules
                            SET {set_clause}
                            WHERE rule_id = :rule_id
                            """),
                            {**rule_dict, "rule_id": rule_dict['rule_id']}
                        )
                    else:
                        # Insert new rule
                        columns = list(rule_dict.keys())
                        columns_str = ", ".join(columns)
                        placeholders = ", ".join([f":{col}" for col in columns])
                        
                        conn.execute(
                            text(f"""
                            INSERT INTO bible.versification_rules (
                                {columns_str}
                            ) VALUES (
                                {placeholders}
                            )
                            """),
                            rule_dict
                        )
                
                conn.execute(text("ANALYZE bible.versification_rules"))
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing rules with provided connection: {e}")
            if hasattr(conn, 'rollback'):
                conn.rollback()
            return
    
    # Otherwise, use SQLAlchemy (normal operation path)
    engine = get_db_engine()
    
    try:
        # Ensure tables exist
        create_tables_if_not_exist(engine)
        
        # Clear existing rules
        with engine.connect() as conn:
            try:
                clear_result = conn.execute(text("DELETE FROM bible.versification_rules"))
                conn.commit()
                logger.info(f"Cleared {clear_result.rowcount} existing rules")
            except SQLAlchemyError as e:
                conn.rollback()
                logger.error(f"Error clearing existing rules: {e}")
                return
        
        # Insert rules
        for rule in rules:
            rule_dict = rule.to_dict() if hasattr(rule, 'to_dict') else rule
            
            # Check if rule already exists
            result = conn.execute(
                text("SELECT 1 FROM bible.versification_rules r WHERE r.rule_id = :rule_id"),
                {"rule_id": rule_dict['rule_id']}
            )
            rule_exists = result.scalar() is not None
            
            if rule_exists:
                # Update existing rule
                columns = list(rule_dict.keys())
                set_clause = ", ".join([f"{col} = :{col}" for col in columns])
                
                conn.execute(
                    text(f"""
                    UPDATE bible.versification_rules
                    SET {set_clause}
                    WHERE rule_id = :rule_id
                    """),
                    {**rule_dict, "rule_id": rule_dict['rule_id']}
                )
            else:
                # Insert new rule
                columns = list(rule_dict.keys())
                columns_str = ", ".join(columns)
                placeholders = ", ".join([f":{col}" for col in columns])
                
                conn.execute(
                    text(f"""
                    INSERT INTO bible.versification_rules (
                        {columns_str}
                    ) VALUES (
                        {placeholders}
                    )
                    """),
                    rule_dict
                )
        
        conn.commit()
        logger.info(f"Successfully stored {len(rules)} rules")
        
    except Exception as e:
        logger.error(f"Error storing rules: {str(e)}")
        if hasattr(e, 'diag'):
            logger.error(f"Details: {e.diag.message_detail}")
        raise

def store_documentation(documentation: List[Dict[str, Any]], conn=None) -> None:
    """
    Store versification documentation in the database.
    
    Args:
        documentation (List[Dict[str, Any]]): List of Documentation objects to store.
        conn (Connection, optional): Database connection. If not provided, a new connection will be created.
    """
    if not documentation:
        logger.warning("No documentation to store")
        return
        
    logger.info(f"Storing {len(documentation)} versification documentation entries")
    
    # If a connection was provided, use it directly
    if conn is not None:
        try:
            # Connection could be SQLAlchemy ConnectionFairy or psycopg Connection
            if hasattr(conn, 'cursor'):  # psycopg Connection
                with conn.cursor() as cur:
                    for doc in documentation:
                        doc_dict = doc.to_dict() if hasattr(doc, 'to_dict') else doc
                        
                        # Check if documentation already exists
                        cur.execute("""
                        SELECT 1 FROM bible.versification_documentation d
                        WHERE d.doc_id = %s
                        """, (doc_dict['doc_id'],))
                        
                        doc_exists = cur.fetchone() is not None
                        
                        if doc_exists:
                            # Update existing documentation
                            columns = list(doc_dict.keys())
                            set_clause = ", ".join([f"{col} = %s" for col in columns])
                            values = [doc_dict[col] for col in columns]
                            values.append(doc_dict['doc_id'])  # For the WHERE clause
                            
                            cur.execute(f"""
                            INSERT INTO bible.versification_documentation (
                                {", ".join(columns)}
                            ) VALUES (
                                {", ".join(["%s"] * len(columns))}
                            )
                            ON CONFLICT (doc_id) DO UPDATE SET
                                {set_clause}
                            """, values + values)
                        else:
                            # Insert new documentation
                            columns = list(doc_dict.keys())
                            columns_str = ", ".join(columns)
                            placeholders = ", ".join(["%s"] * len(columns))
                            values = [doc_dict[col] for col in columns]
                            
                            cur.execute(f"""
                            INSERT INTO bible.versification_documentation (
                                {columns_str}
                            ) VALUES (
                                {placeholders}
                            )
                            """, values)
                    
                    conn.commit()
            else:  # SQLAlchemy ConnectionFairy
                for doc in documentation:
                    doc_dict = doc.to_dict() if hasattr(doc, 'to_dict') else doc
                    
                    # Check if documentation already exists
                    result = conn.execute(
                        text("SELECT 1 FROM bible.versification_documentation d WHERE d.doc_id = :doc_id"),
                        {"doc_id": doc_dict['doc_id']}
                    )
                    doc_exists = result.scalar() is not None
                    
                    if doc_exists:
                        # Update existing documentation
                        columns = list(doc_dict.keys())
                        set_clause = ", ".join([f"{col} = :{col}" for col in columns])
                        
                        conn.execute(
                            text(f"""
                            INSERT INTO bible.versification_documentation (
                                {", ".join(columns)}
                            ) VALUES (
                                {", ".join([f":{col}" for col in columns])}
                            )
                            ON CONFLICT (doc_id) DO UPDATE SET
                                {set_clause}
                            """),
                            {**doc_dict, **doc_dict}
                        )
                    else:
                        # Insert new documentation
                        columns = list(doc_dict.keys())
                        columns_str = ", ".join(columns)
                        placeholders = ", ".join([f":{col}" for col in columns])
                        
                        conn.execute(
                            text(f"""
                            INSERT INTO bible.versification_documentation (
                                {columns_str}
                            ) VALUES (
                                {placeholders}
                            )
                            """),
                            doc_dict
                        )
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing documentation with provided connection: {e}")
            if hasattr(conn, 'rollback'):
                conn.rollback()
            return
            
    # Otherwise, use SQLAlchemy (normal operation path)
    engine = get_db_engine()
    
    try:
        # Ensure tables exist
        create_tables_if_not_exist(engine)
        
        # Clear existing documentation
        with engine.connect() as conn:
            try:
                clear_result = conn.execute(text("DELETE FROM bible.versification_documentation"))
                conn.commit()
                logger.info(f"Cleared {clear_result.rowcount} existing documentation entries")
            except SQLAlchemyError as e:
                conn.rollback()
                logger.error(f"Error clearing existing documentation entries: {e}")
                return
        
        # Insert documentation
        for doc in documentation:
            doc_dict = doc.to_dict() if hasattr(doc, 'to_dict') else doc
            
            # Check if documentation already exists
            result = conn.execute(
                text("SELECT 1 FROM bible.versification_documentation d WHERE d.doc_id = :doc_id"),
                {"doc_id": doc_dict['doc_id']}
            )
            doc_exists = result.scalar() is not None
            
            if doc_exists:
                # Update existing documentation
                columns = list(doc_dict.keys())
                set_clause = ", ".join([f"{col} = :{col}" for col in columns])
                
                conn.execute(
                    text(f"""
                    UPDATE bible.versification_documentation
                    SET {set_clause}
                    WHERE doc_id = :doc_id
                    """),
                    {**doc_dict, **doc_dict}
                )
            else:
                # Insert new documentation
                columns = list(doc_dict.keys())
                columns_str = ", ".join(columns)
                placeholders = ", ".join([f":{col}" for col in columns])
                
                conn.execute(
                    text(f"""
                    INSERT INTO bible.versification_documentation (
                        {columns_str}
                    ) VALUES (
                        {placeholders}
                    )
                    """),
                    doc_dict
                )
        
        conn.commit()
        logger.info(f"Successfully stored {len(documentation)} documentation entries")
        
    except Exception as e:
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

def create_tables_if_not_exist(engine):
    """Create the required tables if they don't exist."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE SCHEMA IF NOT EXISTS bible;
            
            CREATE TABLE IF NOT EXISTS bible.versification_mappings (
                id SERIAL PRIMARY KEY,
                source_tradition VARCHAR(50),
                target_tradition VARCHAR(50),
                source_book VARCHAR(10),
                source_chapter VARCHAR(10),
                source_verse INTEGER,
                source_subverse VARCHAR(5),
                manuscript_marker VARCHAR(50),
                target_book VARCHAR(10),
                target_chapter VARCHAR(10),
                target_verse INTEGER,
                target_subverse VARCHAR(5),
                mapping_type VARCHAR(20)
            );
        """))
        conn.commit()

def store_versification_mappings(mappings):
    """Store versification mappings in the database.
    
    Args:
        mappings (list): List of Mapping objects.
    """
    engine = get_db_engine()
    create_tables_if_not_exist(engine)
    
    try:
        # Convert Mapping objects to dictionaries with explicit column names
        mapping_dicts = []
        for mapping in mappings:
            mapping_dict = {
                'source_tradition': mapping.source_tradition,
                'target_tradition': mapping.target_tradition,
                'source_book': mapping.source_book,
                'source_chapter': mapping.source_chapter,
                'source_verse': mapping.source_verse,
                'source_subverse': mapping.source_subverse,
                'manuscript_marker': mapping.manuscript_marker,
                'target_book': mapping.target_book,
                'target_chapter': mapping.target_chapter,
                'target_verse': mapping.target_verse,
                'target_subverse': mapping.target_subverse,
                'mapping_type': mapping.mapping_type
            }
            mapping_dicts.append(mapping_dict)
        
        # Use a batch insert with explicit transaction management
        with engine.begin() as conn:
            if mapping_dicts:
                conn.execute(
                    text("""
                    INSERT INTO bible.versification_mappings 
                    (source_tradition, target_tradition, source_book, source_chapter, 
                     source_verse, source_subverse, manuscript_marker, target_book, 
                     target_chapter, target_verse, target_subverse, mapping_type)
                    VALUES 
                    (:source_tradition, :target_tradition, :source_book, :source_chapter, 
                     :source_verse, :source_subverse, :manuscript_marker, :target_book, 
                     :target_chapter, :target_verse, :target_subverse, :mapping_type)
                    """),
                    mapping_dicts
                )
                # No need for explicit commit with engine.begin()
                logger.info(f"Successfully stored {len(mapping_dicts)} versification mappings")
            else:
                logger.warning("No mappings to store")
    except SQLAlchemyError as e:
        logger.error(f"Error storing versification mappings: {e}")
        raise

def clear_versification_mappings():
    """Clear all versification mappings from the database."""
    engine = get_db_engine()
    
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM bible.versification_mappings"))
            logger.info("Successfully cleared all versification mappings")
    except SQLAlchemyError as e:
        logger.error(f"Error clearing versification mappings: {e}")
        raise

# Example usage (demonstration)
# if __name__ == '__main__': 