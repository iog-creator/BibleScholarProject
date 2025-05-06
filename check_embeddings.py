#!/usr/bin/env python3
"""
Check available books and translations in the verse_embeddings table.
"""

import os
import psycopg2
import psycopg2.extras

# Database connection parameters
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "bible_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# Connect to the database
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# Check available translations
cursor.execute("SELECT DISTINCT translation_source FROM bible.verse_embeddings")
translations = [row['translation_source'] for row in cursor.fetchall()]
print(f"Available translations: {', '.join(translations)}")

# Check available books
cursor.execute("SELECT DISTINCT book_name FROM bible.verse_embeddings ORDER BY book_name")
books = [row['book_name'] for row in cursor.fetchall()]
print(f"\nAvailable books: {', '.join(books)}")

# Check total embeddings
cursor.execute("SELECT COUNT(*) FROM bible.verse_embeddings")
total_embeddings = cursor.fetchone()[0]
print(f"\nTotal embeddings: {total_embeddings}")

# Check distribution by translation
print("\nDistribution by translation:")
cursor.execute("""
    SELECT translation_source, COUNT(*) as verse_count
    FROM bible.verse_embeddings
    GROUP BY translation_source
    ORDER BY verse_count DESC
""")
for row in cursor.fetchall():
    print(f"  {row['translation_source']}: {row['verse_count']} verses")

# Check distribution by book
print("\nSample distribution by book (top 10):")
cursor.execute("""
    SELECT book_name, COUNT(*) as verse_count
    FROM bible.verse_embeddings
    GROUP BY book_name
    ORDER BY verse_count DESC
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row['book_name']}: {row['verse_count']} verses")

# Check specific verse (Psalm 23:1)
cursor.execute("""
    SELECT COUNT(*) 
    FROM bible.verse_embeddings 
    WHERE book_name = 'Psalms' AND chapter_num = 23 AND verse_num = 1
""")
psalm_count = cursor.fetchone()[0]
print(f"\nPsalm 23:1 embeddings: {psalm_count}")

cursor.execute("""
    SELECT COUNT(*) 
    FROM bible.verse_embeddings 
    WHERE book_name = 'Psalm' AND chapter_num = 23 AND verse_num = 1
""")
psalm_alt_count = cursor.fetchone()[0]
print(f"Psalm 23:1 embeddings (alternate spelling): {psalm_alt_count}")

# Close database connections
cursor.close()
conn.close() 