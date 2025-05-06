#!/usr/bin/env python3
"""
Generate embeddings for Bible verses and store them in the database.

This script:
1. Retrieves KJV, ASV, TAHOT, TAGNT, and ESV verses from the database
2. Generates embeddings using LM Studio API with efficient batching
3. Stores embeddings in the verse_embeddings table
4. Creates indexes for similarity search

Usage:
    python -m src.utils.generate_verse_embeddings [translation_sources]

Arguments:
    translation_sources: Optional space-separated list of translation sources to process
                        (e.g., "KJV ASV TAHOT TAGNT ESV"). If not provided, all will be processed.

Environment Variables:
    POSTGRES_HOST: Database host (default: localhost)
    POSTGRES_PORT: Database port (default: 5432)
    POSTGRES_DB: Database name (default: bible_db)
    POSTGRES_USER: Database user (default: postgres)
    POSTGRES_PASSWORD: Database password
    LM_STUDIO_API_URL: LM Studio API URL (default: http://127.0.0.1:1234)
"""

import os
import sys
import time
import logging
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
import psycopg
from psycopg.rows import dict_row
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv
import concurrent.futures
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/embeddings.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# LM Studio API settings
LM_STUDIO_API_URL = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234")
EMBEDDING_MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0:2"
BATCH_SIZE = 50  # Process in larger batches for better GPU utilization
MAX_WORKERS = 4  # Number of parallel workers for processing

# All available translation sources
ALL_TRANSLATIONS = ["KJV", "ASV", "TAHOT", "TAGNT", "ESV"]

def get_db_connection():
    """Get a database connection with the appropriate configuration."""
    conn = psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "bible_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        row_factory=dict_row
    )
    return conn

def get_verses(translation_sources: List[str], limit: int = None) -> List[Dict[str, Any]]:
    """
    Retrieve Bible verses from the database for the specified translations.
    
    Args:
        translation_sources: List of translation sources (e.g., ['KJV', 'ASV'])
        limit: Optional limit on number of verses to retrieve (for testing)
        
    Returns:
        List of verse dictionaries
    """
    placeholders = ", ".join(["%s"] * len(translation_sources))
    query = f"""
        SELECT id, book_name, chapter_num, verse_num, verse_text, translation_source
        FROM bible.verses
        WHERE translation_source IN ({placeholders})
        ORDER BY book_name, chapter_num, verse_num, translation_source
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, translation_sources)
            verses = cur.fetchall()
            logger.info(f"Retrieved {len(verses)} verses from the database")
            return verses
    except Exception as e:
        logger.error(f"Error retrieving verses: {e}")
        raise
    finally:
        conn.close()

def get_batch_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for a batch of texts using LM Studio API.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    try:
        response = requests.post(
            f"{LM_STUDIO_API_URL}/v1/embeddings",
            headers={"Content-Type": "application/json"},
            json={
                "model": EMBEDDING_MODEL,
                "input": texts
            },
            timeout=120  # Increased timeout for batch processing
        )
        
        if response.status_code != 200:
            logger.error(f"Error from LM Studio API: {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            # Extract all embeddings from the response
            embeddings = []
            for item in data["data"]:
                if "embedding" in item:
                    # Convert all values to float to ensure consistent type
                    embedding = [float(val) for val in item["embedding"]]
                    embeddings.append(embedding)
                else:
                    logger.error(f"Missing embedding in response item: {item}")
                    embeddings.append(None)
            return embeddings
        else:
            logger.error(f"Unexpected response format: {data}")
            return None
    except Exception as e:
        logger.error(f"Error getting batch embeddings from LM Studio: {e}")
        return None

def process_verse_batch(verse_batch: List[Dict[str, Any]], conn) -> Tuple[int, int]:
    """
    Process a batch of verses to generate and store embeddings.
    
    Args:
        verse_batch: List of verse dictionaries
        conn: Database connection
        
    Returns:
        Tuple of (success_count, error_count)
    """
    success_count = 0
    error_count = 0
    
    # Extract texts for batch embedding
    texts = [verse["verse_text"] for verse in verse_batch]
    
    # Get embeddings for all texts in the batch
    batch_embeddings = get_batch_embeddings(texts)
    
    if not batch_embeddings or len(batch_embeddings) != len(verse_batch):
        logger.error(f"Failed to get embeddings for batch. Expected {len(verse_batch)}, got {len(batch_embeddings) if batch_embeddings else 0}")
        return 0, len(verse_batch)
    
    # Insert embeddings into the database
    with conn.cursor() as cur:
        for i, (verse, embedding) in enumerate(zip(verse_batch, batch_embeddings)):
            if embedding:
                try:
                    cur.execute(
                        """
                        INSERT INTO bible.verse_embeddings 
                            (verse_id, book_name, chapter_num, verse_num, translation_source, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (verse_id) DO UPDATE 
                        SET embedding = EXCLUDED.embedding
                        """,
                        (
                            verse["id"], 
                            verse["book_name"],
                            verse["chapter_num"],
                            verse["verse_num"], 
                            verse["translation_source"],
                            embedding
                        )
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error inserting embedding for verse {verse['id']}: {e}")
                    error_count += 1
            else:
                logger.warning(f"Missing embedding for verse {verse['id']}")
                error_count += 1
    
    conn.commit()
    return success_count, error_count

def generate_embeddings(verses: List[Dict[str, Any]]) -> None:
    """
    Generate embeddings for verses and store them in the database.
    
    Args:
        verses: List of verse dictionaries
    """
    # Check if LM Studio API is available
    try:
        logger.info(f"Checking LM Studio API at {LM_STUDIO_API_URL}...")
        response = requests.get(f"{LM_STUDIO_API_URL}/v1/models", timeout=5)
        if response.status_code != 200:
            logger.error(f"LM Studio API is not available: {response.status_code} - {response.text}")
            raise Exception("LM Studio API is not available")
        
        logger.info(f"LM Studio API is available. Available models: {response.json()}")
    except Exception as e:
        logger.error(f"Error connecting to LM Studio API: {e}")
        raise
    
    conn = get_db_connection()
    try:
        # Group verses by translation for better logging
        translation_sources = list(set(verse["translation_source"] for verse in verses))
        logger.info(f"Processing embeddings for translations: {translation_sources}")
        
        # Process verses in batches
        total_success = 0
        total_errors = 0
        
        # Group verses into batches
        verse_batches = [verses[i:i + BATCH_SIZE] for i in range(0, len(verses), BATCH_SIZE)]
        logger.info(f"Processing {len(verses)} verses in {len(verse_batches)} batches of size {BATCH_SIZE}")
        
        for i, batch in enumerate(tqdm(verse_batches, desc="Processing batches")):
            success, errors = process_verse_batch(batch, conn)
            total_success += success
            total_errors += errors
            
            # Log progress
            if (i + 1) % 10 == 0 or (i + 1) == len(verse_batches):
                logger.info(f"Processed {i+1}/{len(verse_batches)} batches. Success: {total_success}, Errors: {total_errors}")
                logger.info(f"Progress: {((i+1)/len(verse_batches))*100:.2f}% complete")
        
        logger.info(f"Embedding generation completed. Successful: {total_success}, Errors: {total_errors}")
    
    except Exception as e:
        logger.error(f"Error in embeddings generation: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def create_index():
    """Create an index on the embeddings table for faster similarity searches."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            logger.info("Creating index on verse_embeddings table...")
            # Create an index using ivfflat for approximate nearest neighbor search
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_verse_embeddings_vector 
                ON bible.verse_embeddings 
                USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100)
                """
            )
        conn.commit()
        logger.info("Index created successfully")
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_embedding_stats():
    """Get statistics about existing embeddings in the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Get total verse count
            cur.execute("SELECT COUNT(*) FROM bible.verses")
            total_verses = cur.fetchone()["count"]
            
            # Get total embedding count
            cur.execute("SELECT COUNT(*) FROM bible.verse_embeddings")
            total_embeddings = cur.fetchone()["count"]
            
            # Get embedding count by translation
            cur.execute("""
                SELECT translation_source, COUNT(*) as count 
                FROM bible.verse_embeddings 
                GROUP BY translation_source 
                ORDER BY translation_source
            """)
            translation_counts = cur.fetchall()
            
            logger.info(f"Database has {total_verses} verses and {total_embeddings} embeddings")
            logger.info(f"Overall coverage: {(total_embeddings/total_verses)*100:.2f}%")
            
            for row in translation_counts:
                logger.info(f"  {row['translation_source']}: {row['count']} embeddings")
            
            return {
                "total_verses": total_verses,
                "total_embeddings": total_embeddings,
                "translations": {row["translation_source"]: row["count"] for row in translation_counts}
            }
    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}")
        return None
    finally:
        conn.close()

def main():
    """Main entry point."""
    try:
        start_time = time.time()
        
        # Parse command-line arguments for specific translations to process
        if len(sys.argv) > 1:
            translation_sources = sys.argv[1:] 
            for source in translation_sources:
                if source not in ALL_TRANSLATIONS:
                    logger.error(f"Unknown translation source: {source}")
                    logger.error(f"Available translations: {ALL_TRANSLATIONS}")
                    sys.exit(1)
        else:
            # Process all translations by default
            translation_sources = ALL_TRANSLATIONS
        
        logger.info(f"Starting embedding generation for translations: {translation_sources}")
        
        # Get initial stats
        logger.info("Getting initial embedding statistics...")
        initial_stats = get_embedding_stats()
        
        # Get verses for specified translations
        verses = get_verses(translation_sources)
        
        if not verses:
            logger.warning(f"No verses found for translations: {translation_sources}")
            sys.exit(0)
        
        # Generate and store embeddings
        generate_embeddings(verses)
        
        # Create index for fast similarity search
        create_index()
        
        # Get final stats
        logger.info("Getting final embedding statistics...")
        final_stats = get_embedding_stats()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Embedding generation completed in {elapsed_time:.2f} seconds")
        logger.info(f"Average time per verse: {elapsed_time/len(verses):.4f} seconds")
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise

if __name__ == "__main__":
    main() 