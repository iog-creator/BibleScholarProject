#!/usr/bin/env python3
"""
Fix verse_embeddings table schema and constraints.

This script:
1. Safely adds a unique constraint on verse_id to allow ON CONFLICT to work
2. Makes minimal changes to the database structure
3. Does not alter the primary key
"""

import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "bible_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

def connect_to_db(autocommit=False):
    """Connect to the database."""
    print(f"Connecting to database: {DB_NAME} at {DB_HOST}:{DB_PORT}")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.autocommit = autocommit
    return conn

def check_constraints(conn):
    """Check the verse_embeddings table constraints."""
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'bible' 
                AND table_name = 'verse_embeddings'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("verse_embeddings table does not exist.")
            return {'table_exists': False}
        
        # Check unique constraints
        cursor.execute("""
            SELECT con.conname, con.contype
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            WHERE nsp.nspname = 'bible'
            AND rel.relname = 'verse_embeddings'
            AND con.contype = 'u'
        """)
        unique_constraints = cursor.fetchall()
        
        # Check verse_id unique constraint specifically
        has_verse_id_unique = False
        for constraint in unique_constraints:
            cursor.execute(f"""
                SELECT attname
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
                JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = ANY(con.conkey)
                WHERE con.conname = '{constraint['conname']}'
                ORDER BY att.attnum
            """)
            constrained_columns = [col[0] for col in cursor.fetchall()]
            print(f"Constraint {constraint['conname']}: {constrained_columns}")
            if 'verse_id' in constrained_columns and len(constrained_columns) == 1:
                has_verse_id_unique = True
                print(f"Found unique constraint on verse_id: {constraint['conname']}")
        
        print(f"Table exists: {table_exists}")
        print(f"Has unique constraints: {len(unique_constraints) > 0}")
        print(f"Has verse_id unique constraint: {has_verse_id_unique}")
        
        return {
            'table_exists': table_exists,
            'unique_constraints': unique_constraints,
            'has_verse_id_unique': has_verse_id_unique
        }

def create_safe_verse_id_constraint(constraint_info):
    """Safely add a unique constraint on verse_id column only if it doesn't exist."""
    # Create a new connection with autocommit=True
    conn = connect_to_db(autocommit=True)
    
    try:
        if not constraint_info['has_verse_id_unique']:
            with conn.cursor() as cursor:
                try:
                    print("Creating unique constraint on verse_id column...")
                    cursor.execute("""
                        ALTER TABLE bible.verse_embeddings
                        ADD CONSTRAINT verse_embeddings_verse_id_key UNIQUE (verse_id)
                    """)
                    print("Verse ID unique constraint created successfully.")
                    return True
                except Exception as e:
                    print(f"Error creating unique constraint: {e}")
                    return False
        else:
            print("Verse ID unique constraint already exists. No changes needed.")
            return True
    finally:
        conn.close()

def create_direct_embedding_query(translation):
    """Generate SQL query for direct embedding insertion."""
    return f"""
INSERT INTO bible.verse_embeddings (verse_id, book_name, chapter_num, verse_num, translation_source, embedding)
SELECT v.id, v.book_name, v.chapter_num, v.verse_num, v.translation_source, NULL
FROM bible.verses v
WHERE v.translation_source = '{translation}'
AND NOT EXISTS (
    SELECT 1 FROM bible.verse_embeddings e
    WHERE e.verse_id = v.id
)
ON CONFLICT (verse_id) DO NOTHING;
"""

def update_generate_verse_embeddings(constraint_added):
    """Show the user how to update their generate_verse_embeddings.py script."""
    if constraint_added:
        print("""
To update your embedding generation process, make sure your INSERT statement 
in src/utils/generate_verse_embeddings.py looks like this:

```python
INSERT INTO bible.verse_embeddings 
    (verse_id, book_name, chapter_num, verse_num, translation_source, embedding)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (verse_id) DO UPDATE 
SET embedding = EXCLUDED.embedding
```

This will update existing embeddings if they exist, or insert new ones if they don't.
        """)
    
    print("""
Now you can generate embeddings for the remaining translations:
    python -m src.utils.generate_verse_embeddings TAHOT
    python -m src.utils.generate_verse_embeddings TAGNT
    python -m src.utils.generate_verse_embeddings ESV
    
Or all at once:
    python -m src.utils.generate_verse_embeddings TAHOT TAGNT ESV
""")

def main():
    """Main function."""
    try:
        # First connection for reading only
        conn = connect_to_db()
        print("Connected to database.")
        
        # Check constraints without modifying anything
        print("\nChecking current constraints...")
        constraint_info = check_constraints(conn)
        
        # Close the first connection before making changes
        conn.close()
        
        # If verse_id unique constraint doesn't exist, create it
        constraint_added = False
        if constraint_info['table_exists'] and not constraint_info['has_verse_id_unique']:
            print("\nAdding verse_id unique constraint...")
            constraint_added = create_safe_verse_id_constraint(constraint_info)
            
            # Verify the constraint was added
            if constraint_added:
                print("\nVerifying constraint was added...")
                # New connection for verification
                verify_conn = connect_to_db()
                new_constraint_info = check_constraints(verify_conn)
                verify_conn.close()
                
                if new_constraint_info['has_verse_id_unique']:
                    print("Constraint successfully added and verified.")
                else:
                    print("Constraint may not have been added correctly. Please check manually.")
                    constraint_added = False
        elif not constraint_info['table_exists']:
            print("\nTable does not exist. Please make sure the verse_embeddings table is created first.")
        else:
            print("\nNo changes needed for constraints.")
        
        # Show update instructions
        print("\nNext steps:")
        update_generate_verse_embeddings(constraint_added)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 