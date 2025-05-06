#!/usr/bin/env python3
"""
Test pgvector search functionality directly against the database.
This script doesn't depend on LM Studio for generating new embeddings.
It uses existing embeddings in the database to find similar verses.
"""

import os
import sys
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "bible_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")  # Updated default password

print(f"Connecting to database: {DB_NAME} at {DB_HOST}:{DB_PORT}")

try:
    # Connect to the database
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=psycopg2.extras.DictCursor
    )
    print("Connected to database")

    # Check database schema and current embedding stats
    with conn.cursor() as cur:
        # Get embedding statistics
        cur.execute("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'bible' AND table_name = 'verse_embeddings'
        """)
        columns = cur.fetchall()
        print("\nVerse Embeddings Table Schema:")
        for col in columns:
            print(f"  {col['column_name']} ({col['data_type']})")
        
        # Count total verses
        cur.execute("SELECT COUNT(*) FROM bible.verses")
        total_verses = cur.fetchone()[0]
        
        # Count total embeddings
        cur.execute("SELECT COUNT(*) FROM bible.verse_embeddings")
        total_embeddings = cur.fetchone()[0]
        
        # Count embeddings per translation
        cur.execute("""
            SELECT v.translation_source, COUNT(*) as count 
            FROM bible.verse_embeddings e
            JOIN bible.verses v ON e.verse_id = v.id
            GROUP BY v.translation_source 
            ORDER BY v.translation_source
        """)
        translation_counts = cur.fetchall()
        
        print(f"\nDatabase Statistics:")
        print(f"  Total verses: {total_verses}")
        print(f"  Total verse embeddings: {total_embeddings}")
        print(f"  Overall coverage: {(total_embeddings/total_verses)*100:.2f}%")
        
        print("\nEmbeddings by Translation:")
        for row in translation_counts:
            print(f"  {row['translation_source']}: {row['count']} embeddings")
            
        print("\n=== Testing KJV Search ===")
        try:
            # Test similarity search with a KJV verse looking for "creation"
            cur.execute("""
            WITH sample_verse AS (
                SELECT e.embedding
                FROM bible.verse_embeddings e
                JOIN bible.verses v ON e.verse_id = v.id
                WHERE v.translation_source = 'KJV' 
                AND v.book_name = 'Genesis' 
                AND v.chapter_num = 1 
                AND v.verse_num = 1
                LIMIT 1
            )
            SELECT 
                v.book_name, 
                v.chapter_num, 
                v.verse_num, 
                v.verse_text, 
                v.translation_source, 
                1 - (e.embedding <=> (SELECT embedding FROM sample_verse)) AS similarity
            FROM 
                bible.verse_embeddings e
                JOIN bible.verses v ON e.verse_id = v.id
            WHERE 
                v.translation_source = 'KJV'
                AND NOT (v.book_name = 'Genesis' AND v.chapter_num = 1 AND v.verse_num = 1)
            ORDER BY 
                e.embedding <=> (SELECT embedding FROM sample_verse)
            LIMIT 3
            """)
            similar_verses = cur.fetchall()
            
            print("\nVerses similar to Genesis 1:1 in KJV:")
            for v in similar_verses:
                print(f"  {v['book_name']} {v['chapter_num']}:{v['verse_num']} - Similarity: {v['similarity']*100:.2f}%")
                print(f"  Text: {v['verse_text']}")
                print()
        except Exception as e:
            print(f"  Error testing KJV embeddings: {e}")
            
        print("\n=== Testing TAHOT Search ===")
        try:
            # Test similarity search with a TAHOT verse
            cur.execute("""
            WITH sample_verse AS (
                SELECT e.embedding
                FROM bible.verse_embeddings e
                JOIN bible.verses v ON e.verse_id = v.id
                WHERE v.translation_source = 'TAHOT' 
                AND v.book_name = 'Gen' 
                AND v.chapter_num = 1 
                AND v.verse_num = 1
                LIMIT 1
            )
            SELECT 
                v.book_name, 
                v.chapter_num, 
                v.verse_num, 
                v.verse_text, 
                v.translation_source, 
                1 - (e.embedding <=> (SELECT embedding FROM sample_verse)) AS similarity
            FROM 
                bible.verse_embeddings e
                JOIN bible.verses v ON e.verse_id = v.id
            WHERE 
                v.translation_source = 'TAHOT'
                AND NOT (v.book_name = 'Gen' AND v.chapter_num = 1 AND v.verse_num = 1)
            ORDER BY 
                e.embedding <=> (SELECT embedding FROM sample_verse)
            LIMIT 3
            """)
            similar_verses = cur.fetchall()
            
            print("\nVerses similar to Genesis 1:1 in TAHOT:")
            for v in similar_verses:
                print(f"  {v['book_name']} {v['chapter_num']}:{v['verse_num']} - Similarity: {v['similarity']*100:.2f}%")
                print(f"  Text: {v['verse_text']}")
                print()
        except Exception as e:
            print(f"  Error testing TAHOT embeddings: {e}")
            
        print("\n=== Testing Cross-Language Search ===")
        try:
            # Test cross-language similarity search (Genesis 1:1 in KJV vs TAHOT)
            cur.execute("""
            WITH kjv_verse AS (
                SELECT e.embedding
                FROM bible.verse_embeddings e
                JOIN bible.verses v ON e.verse_id = v.id
                WHERE v.translation_source = 'KJV' 
                AND v.book_name = 'Genesis' 
                AND v.chapter_num = 1 
                AND v.verse_num = 1
                LIMIT 1
            )
            SELECT 
                v.book_name, 
                v.chapter_num, 
                v.verse_num, 
                v.verse_text, 
                v.translation_source, 
                1 - (e.embedding <=> (SELECT embedding FROM kjv_verse)) AS similarity
            FROM 
                bible.verse_embeddings e
                JOIN bible.verses v ON e.verse_id = v.id
            WHERE 
                v.translation_source = 'TAHOT'
            ORDER BY 
                e.embedding <=> (SELECT embedding FROM kjv_verse)
            LIMIT 3
            """)
            similar_verses = cur.fetchall()
            
            print("\nTAHOT verses most similar to Genesis 1:1 in KJV:")
            for v in similar_verses:
                print(f"  {v['book_name']} {v['chapter_num']}:{v['verse_num']} - Similarity: {v['similarity']*100:.2f}%")
                print(f"  Text: {v['verse_text']}")
                print()
        except Exception as e:
            print(f"  Error in cross-language search: {e}")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()
        print("\nDatabase connection closed") 