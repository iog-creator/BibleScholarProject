#!/usr/bin/env python3
"""
Script to extract word relationships from the lexicons.
This script analyzes the loaded lexicon entries and extracts relationships
between Hebrew and Greek words.
"""

import os
import re
import logging
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extract_relationships.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('extract_relationships')

# Load environment variables
load_dotenv()

def get_db_connection():
    """
    Create and return a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'bible_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
        conn.autocommit = False
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def get_hebrew_entries(conn):
    """
    Retrieve Hebrew lexicon entries from the database.
    
    Args:
        conn: Database connection
        
    Returns:
        List of dictionaries containing Hebrew lexicon entries
    """
    entries = []
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                strongs_id, extended_strongs, 
                hebrew_word, gloss
            FROM bible.hebrew_entries
            ORDER BY strongs_id
        """)
        for row in cur.fetchall():
            entries.append({
                'strongs_id': row[0],
                'extended_strongs': row[1],
                'word': row[2],
                'gloss': row[3]
            })
    logger.info(f"Retrieved {len(entries)} Hebrew entries")
    return entries

def get_greek_entries(conn):
    """
    Retrieve Greek lexicon entries from the database.
    
    Args:
        conn: Database connection
        
    Returns:
        List of dictionaries containing Greek lexicon entries
    """
    entries = []
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                strongs_id, extended_strongs, 
                greek_word, gloss
            FROM bible.greek_entries
            ORDER BY strongs_id
        """)
        for row in cur.fetchall():
            entries.append({
                'strongs_id': row[0],
                'extended_strongs': row[1],
                'word': row[2],
                'gloss': row[3]
            })
    logger.info(f"Retrieved {len(entries)} Greek entries")
    return entries

def extract_relationships(hebrew_entries, greek_entries):
    """
    Extract relationships between lexicon entries.
    
    Args:
        hebrew_entries: List of Hebrew lexicon entries
        greek_entries: List of Greek lexicon entries
        
    Returns:
        List of relationship dictionaries
    """
    relationships = []
    
    # Hebrew to Greek relationships
    logger.info(f"Extracting Hebrew -> Greek relationships")
    for hebrew in hebrew_entries:
        hebrew_id = hebrew['strongs_id']
        gloss = hebrew.get('gloss', '')
        
        # Look for references to Greek strong numbers in the gloss
        # Format: ... "word" G0000) ...
        greek_refs = re.findall(r'".*?"\s+(G\d+)', gloss)
        for greek_id in greek_refs:
            if greek_id != hebrew_id:  # Avoid self-references
                relationships.append({
                    'source_id': hebrew_id,
                    'target_id': greek_id,
                    'relationship_type': 'hebrew_related_to_greek'
                })
                
        # Look for "equivalent" or "of" relationships
        if "equivalent:" in gloss.lower() or " of " in gloss.lower():
            for greek in greek_entries:
                greek_id = greek['strongs_id']
                greek_word = greek.get('word', '').lower()
                
                # Skip if empty word
                if not greek_word:
                    continue
                    
                # Check if Greek word is mentioned in Hebrew gloss
                if greek_word in gloss.lower() and len(greek_word) > 2:  # Only match substantial words
                    relationships.append({
                        'source_id': hebrew_id,
                        'target_id': greek_id,
                        'relationship_type': 'hebrew_equivalent_to_greek'
                    })
    
    # Greek to Hebrew relationships
    logger.info(f"Extracting Greek -> Hebrew relationships")
    for greek in greek_entries:
        greek_id = greek['strongs_id']
        gloss = greek.get('gloss', '')
        
        # Look for references to Hebrew strong numbers in the gloss
        # Format: ... "word" H0000) ...
        hebrew_refs = re.findall(r'".*?"\s+(H\d+)', gloss)
        for hebrew_id in hebrew_refs:
            if hebrew_id != greek_id:  # Avoid self-references
                relationships.append({
                    'source_id': greek_id,
                    'target_id': hebrew_id,
                    'relationship_type': 'greek_related_to_hebrew'
                })
                
        # Look for "(Heb. ...)" patterns in Greek lexicon
        heb_patterns = re.findall(r'\(Heb\.\s+[^)]+\)', gloss)
        if heb_patterns:
            for hebrew in hebrew_entries:
                hebrew_id = hebrew['strongs_id']
                hebrew_word = hebrew.get('word', '').lower()
                
                # Skip if empty word
                if not hebrew_word:
                    continue
                    
                # Check if Hebrew word is mentioned in Greek gloss
                if hebrew_word in gloss.lower() and len(hebrew_word) > 2:  # Only match substantial words
                    relationships.append({
                        'source_id': greek_id,
                        'target_id': hebrew_id,
                        'relationship_type': 'greek_equivalent_to_hebrew'
                    })
    
    # Remove duplicates while preserving order
    unique_relationships = []
    seen = set()
    for rel in relationships:
        key = f"{rel['source_id']}:{rel['target_id']}:{rel['relationship_type']}"
        if key not in seen:
            seen.add(key)
            unique_relationships.append(rel)
    
    logger.info(f"Extracted {len(unique_relationships)} unique word relationships")
    return unique_relationships

def save_relationships(conn, relationships):
    """
    Save extracted relationships to the database.
    
    Args:
        conn: Database connection
        relationships: List of relationship dictionaries
    """
    try:
        with conn.cursor() as cur:
            # Clear existing relationships
            cur.execute("DELETE FROM bible.word_relationships")
            
            # Insert new relationships
            if relationships:
                query = """
                INSERT INTO bible.word_relationships 
                    (source_id, target_id, relationship_type)
                VALUES 
                    (%(source_id)s, %(target_id)s, %(relationship_type)s)
                ON CONFLICT ON CONSTRAINT unique_word_relationship DO NOTHING
                """
                execute_batch(cur, query, relationships, page_size=1000)
            
        conn.commit()
        logger.info(f"Saved {len(relationships)} word relationships to the database")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving relationships to database: {e}")
        raise

def main():
    """
    Main function.
    """
    try:
        logger.info("Starting word relationship extraction")
        
        # Connect to the database
        conn = get_db_connection()
        
        try:
            # Get lexicon entries
            hebrew_entries = get_hebrew_entries(conn)
            greek_entries = get_greek_entries(conn)
            
            # Extract relationships
            relationships = extract_relationships(hebrew_entries, greek_entries)
            
            # Save relationships to the database
            save_relationships(conn, relationships)
            
            logger.info("Word relationship extraction completed successfully")
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in word relationship extraction: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main()) 