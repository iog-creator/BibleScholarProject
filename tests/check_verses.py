"""
Script to check for problematic verses in the database.
"""
from database import get_db
from sqlalchemy import text

def check_verses():
    with get_db() as db:
        # Check for verses with invalid numbers
        result = db.execute(text("""
            SELECT book_name, chapter, verse 
            FROM bible.verses 
            WHERE verse <= 0 OR chapter <= 0
            ORDER BY book_name, chapter, verse
        """))
        
        print("\nVerses with invalid numbers:")
        for row in result:
            print(f"{row.book_name} {row.chapter}:{row.verse}")
            
        # Check for verses with NULL values
        result = db.execute(text("""
            SELECT book_name, chapter, verse 
            FROM bible.verses 
            WHERE book_name IS NULL 
            OR chapter IS NULL 
            OR verse IS NULL
        """))
        
        print("\nVerses with NULL values:")
        for row in result:
            print(f"{row.book_name} {row.chapter}:{row.verse}")
            
        # Get total verse count
        total = db.execute(text("SELECT COUNT(*) FROM bible.verses")).scalar()
        print(f"\nTotal verses in database: {total}")

if __name__ == "__main__":
    check_verses() 