#!/usr/bin/env python3
"""
Verse Embeddings Generator

This script generates embeddings for Bible verses using LM Studio API
and stores them in the database with the pgvector extension.

Usage:
    python -m src.utils.generate_verse_embeddings [--translation TRANSLATION] [--limit LIMIT] [--batch_size BATCH_SIZE]

Options:
    --translation    Bible translation to process (default: all available)
    --limit          Maximum number of verses to process (default: all)
    --batch_size     Number of verses to process in each batch (default: 50)
"""

import os
import sys
import logging
import time
import argparse
from pathlib import Path
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Import secure connection (if available, otherwise fall back to direct connection)
try:
    from src.database.secure_connection import get_secure_connection
    USE_SECURE_CONNECTION = True
except ImportError:
    USE_SECURE_CONNECTION = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/verse_embeddings.log", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# LM Studio API settings
LM_STUDIO_API_URL = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
EMBEDDING_MODEL = os.getenv("LM_STUDIO_EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5@q8_0")

# Database connection settings
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "bible_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")

def get_db_connection():
    """Get a connection to the database."""
    try:
        # Use secure connection in write mode if available
        if USE_SECURE_CONNECTION:
            try:
                conn = get_secure_connection(mode='write')
                logger.info("Using secure database connection with WRITE permission")
                return conn
            except ValueError as e:
                logger.error(f"Error getting write permission: {e}")
                logger.warning("This operation requires write access to the database.")
                logger.warning("Please set POSTGRES_WRITE_PASSWORD in your .env file.")
                sys.exit(1)
                
        # Fall back to direct connection if secure connection not available
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        logger.warning("Using direct database connection (not secure)")
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def setup_database():
    """Set up the database schema for verse embeddings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if vector extension is installed
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        if not cursor.fetchone():
            logger.info("Creating vector extension...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
        
        # Create verse_embeddings table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bible.verse_embeddings (
            id SERIAL PRIMARY KEY,
            verse_id INTEGER NOT NULL REFERENCES bible.verses(id),
            book_name VARCHAR(50) NOT NULL,
            chapter_num INTEGER NOT NULL,
            verse_num INTEGER NOT NULL,
            translation_source VARCHAR(20) NOT NULL,
            embedding VECTOR(768) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(verse_id, translation_source)
        )
        """)
        
        # Create indexes
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_verse_embeddings_verse_id 
        ON bible.verse_embeddings(verse_id)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_verse_embeddings_translation 
        ON bible.verse_embeddings(translation_source)
        """)
        
        # Create IVFFlat index for faster similarity search
        try:
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verse_embeddings_vector 
            ON bible.verse_embeddings 
            USING ivfflat (embedding vector_cosine_ops) 
            WITH (lists = 100)
            """)
        except Exception as e:
            logger.warning(f"Could not create IVFFlat index: {e}")
            logger.info("Creating basic vector index instead")
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verse_embeddings_vector 
            ON bible.verse_embeddings 
            USING hnsw (embedding vector_cosine_ops)
            """)
        
        conn.commit()
        logger.info("Database setup completed successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error setting up database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def get_embedding(text):
    """
    Get embedding vector for text using LM Studio API.
    
    Args:
        text: Text to encode
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        response = requests.post(
            f"{LM_STUDIO_API_URL}/embeddings",
            headers={"Content-Type": "application/json"},
            json={
                "model": EMBEDDING_MODEL,
                "input": text
            },
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"Error from LM Studio API: {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        if "data" in data and len(data["data"]) > 0 and "embedding" in data["data"][0]:
            # Ensure all values in the embedding are floats
            embedding = [float(val) for val in data["data"][0]["embedding"]]
            return embedding
        else:
            logger.error(f"Unexpected response format: {data}")
            return None
    except Exception as e:
        logger.error(f"Error getting embedding from LM Studio: {e}")
        return None

def get_verses_to_process(translation=None, limit=None):
    """
    Get verses to process.
    
    Args:
        translation: Bible translation to process (optional)
        limit: Maximum number of verses to process (optional)
        
    Returns:
        List of verse dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Construct the query based on parameters
        query = """
        SELECT v.id AS verse_id, b.book_name, v.chapter_num, v.verse_num, 
               v.verse_text, v.translation_source
        FROM bible.verses v
        JOIN bible.books b ON v.book_id = b.book_id
        """
        
        params = []
        conditions = []
        
        # Add condition for translation if specified
        if translation:
            conditions.append("v.translation_source = %s")
            params.append(translation)
        
        # Add condition to exclude verses already processed
        conditions.append("""
        NOT EXISTS (
            SELECT 1 FROM bible.verse_embeddings ve 
            WHERE ve.verse_id = v.id AND ve.translation_source = v.translation_source
        )
        """)
        
        # Add WHERE clause if there are conditions
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Add LIMIT if specified
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        # Execute the query
        cursor.execute(query, params)
        verses = [dict(zip([column[0] for column in cursor.description], row)) 
                 for row in cursor.fetchall()]
        
        logger.info(f"Found {len(verses)} verses to process")
        return verses
    
    except Exception as e:
        logger.error(f"Error getting verses to process: {e}")
        return []
    
    finally:
        cursor.close()
        conn.close()

def store_embeddings(embeddings_data):
    """
    Store embeddings in the database.
    
    Args:
        embeddings_data: List of (verse_id, book_name, chapter_num, verse_num, 
                         translation_source, embedding_vector) tuples
        
    Returns:
        Number of embeddings stored
    """
    if not embeddings_data:
        return 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Prepare data with proper vector format
        formatted_data = []
        for verse_id, book_name, chapter_num, verse_num, translation_source, embedding in embeddings_data:
            # Convert embedding list to PostgreSQL vector format
            embedding_str = f"[{','.join(str(x) for x in embedding)}]"
            formatted_data.append((verse_id, book_name, chapter_num, verse_num, translation_source, embedding_str))
        
        # Use execute_values for better performance
        execute_values(
            cursor,
            """
            INSERT INTO bible.verse_embeddings 
            (verse_id, book_name, chapter_num, verse_num, translation_source, embedding)
            VALUES %s
            ON CONFLICT (verse_id, translation_source) DO UPDATE 
            SET embedding = EXCLUDED.embedding,
                created_at = CURRENT_TIMESTAMP
            """,
            formatted_data,
            template="(%s, %s, %s, %s, %s, %s::vector)"
        )
        
        conn.commit()
        return len(embeddings_data)
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing embeddings: {e}")
        return 0
    
    finally:
        cursor.close()
        conn.close()

def process_verses_in_batches(verses, batch_size=50):
    """
    Process verses in batches and generate embeddings.
    
    Args:
        verses: List of verse dictionaries
        batch_size: Number of verses to process in each batch
        
    Returns:
        Total number of embeddings generated
    """
    total_processed = 0
    total_stored = 0
    
    for i in range(0, len(verses), batch_size):
        batch = verses[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(verses) + batch_size - 1)//batch_size} "
                   f"({len(batch)} verses)")
        
        embeddings_data = []
        
        for verse in batch:
            try:
                # Get the embedding
                embedding = get_embedding(verse["verse_text"])
                
                if embedding:
                    # Add to batch data
                    embeddings_data.append((
                        verse["verse_id"],
                        verse["book_name"],
                        verse["chapter_num"],
                        verse["verse_num"],
                        verse["translation_source"],
                        embedding
                    ))
                    total_processed += 1
                else:
                    logger.warning(f"Failed to generate embedding for verse {verse['book_name']} "
                                  f"{verse['chapter_num']}:{verse['verse_num']} ({verse['translation_source']})")
            
            except Exception as e:
                logger.error(f"Error processing verse {verse['book_name']} "
                            f"{verse['chapter_num']}:{verse['verse_num']}: {e}")
        
        # Store the batch
        stored = store_embeddings(embeddings_data)
        total_stored += stored
        
        logger.info(f"Stored {stored} embeddings in this batch")
        
        # Sleep briefly to avoid overwhelming the API
        time.sleep(0.5)
    
    return total_stored

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate verse embeddings")
    parser.add_argument("--translation", help="Bible translation to process")
    parser.add_argument("--limit", type=int, help="Maximum number of verses to process")
    parser.add_argument("--batch_size", type=int, default=50, help="Batch size for processing")
    args = parser.parse_args()
    
    try:
        # Set up the database
        setup_database()
        
        # Get verses to process
        verses = get_verses_to_process(args.translation, args.limit)
        
        if not verses:
            logger.info("No verses to process")
            return
        
        # Process verses in batches
        total_stored = process_verses_in_batches(verses, args.batch_size)
        
        logger.info(f"Successfully generated and stored {total_stored} verse embeddings")
    
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 