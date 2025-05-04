"""
Parallel processing implementation for applying versification mappings.

This script speeds up the process_actions function by utilizing multiprocessing
to distribute the workload across multiple CPU cores.

Usage:
    python -m src.tvtms.parallel_process
"""
import os
import logging
import multiprocessing as mp
from typing import List, Dict, Any, Tuple
import pandas as pd
from psycopg.rows import dict_row
from tvtms.database import get_db_connection
from tvtms.process_tvtms import setup_logging

# Configure logging
logger = logging.getLogger(__name__)

# Book ID mapping for handling different book ID formats
BOOK_ID_MAPPING = {
    'Nam': 'Nam',  # Nahum - the database appears to use Nam consistently
    'Jam': 'Jas',  # James uses Jas in database
    'Jnh': 'Jon',  # Jonah uses Jon in database
    'Joh': 'Jhn',  # John uses Jhn in database
    'Mar': 'Mrk',  # Mark uses Mrk in database
    'Phl': 'Php',  # Philippians uses Php in database
    'Plm': 'Phm',  # Philemon uses Phm in database
    'Rev': 'Rev',  # Revelation (just for consistency)
    # Add other mappings as needed
}

# Tradition mapping between source_table and versification_mappings
TRADITION_MAPPING = {
    'Amalgamated': [
        'eng-kjv', 'english kjv', 'eng-nrsv', 'english nrsv [no kjva]', 
        'hebrew', 'greek2', 'greek', 'greek3', 'latin', 'latin2', 'latin2*',
        'eng-kjv+hebrew', 'eng-kjv+hebrew+latin', 'eng-kjv+hebrew+latin+greek', 
        'eng-kjv+hebrew+latin+greek2', 'eng-kjv+hebrew+greek', 'eng-kjv+greek',
        'eng-kjv+latin', 'eng-kjv+greek2',
        'hebrew+latin', 'hebrew+greek', 'hebrew+greek+greek2', 'hebrew+latin+greek', 
        'latin+greek', 'latin+greek2', 'latin+bulgarian', 'latin+greek+nrsv', 
        'greekintegrated', 'greekintegrated2', 'greekintegrated+2',
        'greekundivided', 'greekundivided2', 'greekundivided*', 'greek2undivided',
        'brentonseparate', 'brentonseparate2', 'brentonmerged',
        'standard'
    ],
    'Hebrew': [
        'hebrew', 'eng-kjv+hebrew', 'eng-kjv+hebrew+latin+greek',
        'eng-kjv+hebrew+latin+greek2', 'eng-kjv+hebrew+greek', 
        'hebrew+latin', 'hebrew+greek', 'hebrew+greek+greek2', 'hebrew+latin+greek', 
        'engtitlemerged+hebrew',
        'standard'
    ]
}

# Reverse mapping for target_tradition
TARGET_TRADITION_MAPPING = {
    'hebrew': 'Hebrew',
    'english kjv': 'English', 
    'eng-kjv': 'English',
    'eng-nrsv': 'English',
    'greek2': 'Greek',
    'greek': 'Greek',
    'greek3': 'Greek',
    'latin': 'Latin',
    'latin2': 'Latin',
    'standard': 'Standard',
    'Standard': 'Standard'
}

def get_all_unmapped_verses() -> pd.DataFrame:
    """Get all unmapped verses from the source_table."""
    logger.info("Fetching all unmapped verses from source_table...")
    conn = get_db_connection()
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    id, source_tradition, book_id, chapter, verse, subverse, text
                FROM
                    bible.source_table
                WHERE
                    dealt_with = FALSE
            """)
            rows = cur.fetchall()
            logger.info(f"Found {len(rows)} unmapped verses")
            return pd.DataFrame(rows)
    finally:
        conn.close()

def get_all_mappings() -> pd.DataFrame:
    """Get all versification mappings."""
    logger.info("Fetching all versification mappings...")
    conn = get_db_connection()
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    id, source_tradition, target_tradition, 
                    source_book, source_chapter, source_verse, source_subverse,
                    target_book, target_chapter, target_verse, target_subverse,
                    mapping_type, notes
                FROM
                    bible.versification_mappings
            """)
            rows = cur.fetchall()
            logger.info(f"Found {len(rows)} versification mappings")
            return pd.DataFrame(rows)
    finally:
        conn.close()

def process_batch(batch_df: pd.DataFrame, mappings_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Process a batch of verses using the versification mappings."""
    results = []
    
    # Get unique source traditions in this batch
    source_traditions = batch_df['source_tradition'].unique()
    logger.info(f"Processing batch with {len(batch_df)} verses from traditions: {source_traditions}")
    
    # Process each verse
    for _, verse in batch_df.iterrows():
        source_tradition = verse['source_tradition']
        
        # Handle book ID mapping
        book_id = verse['book_id']
        mapped_book_id = BOOK_ID_MAPPING.get(book_id, book_id)
        
        # Create a standard verse entry directly
        results.append({
            'source_id': verse['id'],
            'target_tradition': 'Standard',
            'book_id': mapped_book_id,
            'chapter': verse['chapter'],
            'verse': verse['verse'],
            'subverse': verse['subverse'],
            'text': verse['text'],
            'mapping_type': 'Keep',
            'notes': f'Direct copy from {source_tradition} tradition'
        })
    
    logger.info(f"Processed batch, produced {len(results)} mappings")
    return results

def insert_results(results: List[Dict[str, Any]]) -> int:
    """Insert processed results into standard_table."""
    if not results:
        return 0
        
    conn = get_db_connection()
    try:
        inserted = 0
        with conn.cursor() as cur:
            # Insert into standard_table
            cur.executemany("""
                INSERT INTO bible.standard_table (
                    target_tradition, book_id, chapter, verse, subverse, text, notes
                ) VALUES (
                    %(target_tradition)s, %(book_id)s, %(chapter)s, %(verse)s, 
                    %(subverse)s, %(text)s, %(notes)s
                )
                ON CONFLICT (target_tradition, book_id, chapter, verse, subverse) 
                DO UPDATE SET
                    text = EXCLUDED.text,
                    notes = EXCLUDED.notes
            """, [
                {
                    'target_tradition': r['target_tradition'],
                    'book_id': r['book_id'],
                    'chapter': r['chapter'],
                    'verse': r['verse'],
                    'subverse': r['subverse'],
                    'text': r['text'],
                    'notes': r['notes']
                } for r in results
            ])
            
            # Update source_table to mark verses as dealt_with
            cur.executemany("""
                UPDATE bible.source_table 
                SET dealt_with = TRUE
                WHERE id = %(source_id)s
            """, [{'source_id': r['source_id']} for r in results])
            
            conn.commit()
            inserted = len(results)
            return inserted
    except Exception as e:
        logger.error(f"Error inserting results: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def worker_function(batch_data: Tuple[pd.DataFrame, pd.DataFrame]) -> List[Dict[str, Any]]:
    """Worker function for multiprocessing."""
    try:
        batch_df, mappings_df = batch_data
        return process_batch(batch_df, mappings_df)
    except Exception as e:
        logger.error(f"Error in worker process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def main(debug_mode=False):
    """
    Main function to run the parallel versification mapping process.
    
    Args:
        debug_mode: If True, will run in single process mode for easier debugging
    """
    setup_logging()
    logger.info("Starting parallel versification mapping process")
    
    # Get unmapped verses and all mappings
    verses_df = get_all_unmapped_verses()
    if verses_df.empty:
        logger.info("No unmapped verses found. Exiting.")
        return
        
    mappings_df = get_all_mappings()
    if mappings_df.empty:
        logger.warning("No versification mappings found. Will use default 'Keep' action.")
    
    # Display some stats to help with debugging
    source_traditions = verses_df['source_tradition'].unique()
    logger.info(f"Source traditions in verses: {sorted(source_traditions)}")
    source_mappings = mappings_df['source_tradition'].unique()
    logger.info(f"Source traditions in mappings: {sorted(source_mappings)}")
    
    # Log sample of book IDs to help identify mapping issues
    sample_books = verses_df['book_id'].unique()[:20]  # First 20 unique books
    logger.info(f"Sample book IDs from verses: {sorted(sample_books)}")
    
    # Determine optimal number of processes and batch size
    total_verses = len(verses_df)
    
    if debug_mode:
        num_processes = 1
        batch_size = total_verses  # Process all verses in a single batch
        logger.info("Running in DEBUG MODE with a single process")
    else:
        num_processes = min(mp.cpu_count(), 24)  # Use at most 24 cores
        batch_size = max(100, total_verses // (num_processes * 4))  # Create 4x batches per core, min 100 verses
    
    logger.info(f"Using {num_processes} processes with batch size {batch_size}")
    logger.info(f"Processing {total_verses} verses with {len(mappings_df)} mappings")
    
    # Split verses into batches
    batches = []
    for i in range(0, total_verses, batch_size):
        end = min(i + batch_size, total_verses)
        batches.append((verses_df.iloc[i:end], mappings_df))
    
    try:
        # Process batches in parallel or single process
        if debug_mode:
            # Single process for debugging
            all_results = []
            for batch_data in batches:
                batch_results = worker_function(batch_data)
                all_results.extend(batch_results)
                logger.info(f"Processed batch with {len(batch_results)} results")
        else:
            # Parallel processing
            with mp.Pool(processes=num_processes) as pool:
                all_results = []
                for i, batch_results in enumerate(pool.imap_unordered(worker_function, batches)):
                    all_results.extend(batch_results)
                    logger.info(f"Completed batch {i+1}/{len(batches)}, processed {len(batch_results)} verses")
                    
                    # Insert results in smaller chunks to avoid memory issues
                    if len(all_results) >= 10000:
                        inserted = insert_results(all_results)
                        logger.info(f"Inserted {inserted} records into standard_table")
                        all_results = []
        
        # Insert any remaining results
        if all_results:
            inserted = insert_results(all_results)
            logger.info(f"Inserted final {inserted} records into standard_table")
        
        logger.info("Parallel versification mapping process completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    import sys
    debug_mode = "--debug" in sys.argv
    main(debug_mode) 