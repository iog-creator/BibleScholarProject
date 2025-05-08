#!/usr/bin/env python3
"""
Check if PostgreSQL with pgvector extension is installed and working.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection settings
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "bible_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")

def main():
    """Main function."""
    print(f"Checking PostgreSQL connection to {DB_NAME} at {DB_HOST}:{DB_PORT}")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        
        print("✅ Connected to PostgreSQL database")
        
        # Check if vector extension is installed
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        has_vector = cursor.fetchone() is not None
        
        if has_vector:
            print("✅ pgvector extension is installed")
        else:
            print("❌ pgvector extension is NOT installed")
            print("   To install, run this SQL command: CREATE EXTENSION vector;")
        
        # Check if verse_embeddings table exists
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'bible' AND table_name = 'verse_embeddings'
        )
        """)
        
        has_table = cursor.fetchone()[0]
        
        if has_table:
            print("✅ verse_embeddings table exists")
            
            # Check count of embeddings
            cursor.execute("SELECT COUNT(*) FROM bible.verse_embeddings")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"✅ There are {count} embeddings in the table")
                
                # Check translations
                cursor.execute("""
                SELECT translation_source, COUNT(*) as count 
                FROM bible.verse_embeddings 
                GROUP BY translation_source
                ORDER BY translation_source
                """)
                
                translations = cursor.fetchall()
                
                if translations:
                    print("Available translations:")
                    for trans in translations:
                        print(f"  • {trans[0]}: {trans[1]} verses")
                else:
                    print("❌ No translations found in verse_embeddings")
            else:
                print("❌ No embeddings found in verse_embeddings table")
                print("   Run generate_verse_embeddings.bat to create embeddings")
        else:
            print("❌ verse_embeddings table does NOT exist")
            print("   It will be created when you run generate_verse_embeddings.bat")
        
        # Close the connection
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 