import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_url():
    """Create database URL from environment variables."""
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    dbname = os.getenv('POSTGRES_DB', 'bible_db')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

def check_db_state():
    """Check the current state of the database."""
    try:
        # Create engine
        engine = create_engine(get_db_url())
        
        with engine.connect() as conn:
            # Check schemas
            logger.info("\nChecking schemas:")
            schemas = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            """)).fetchall()
            
            for schema in schemas:
                schema_name = schema[0]
                logger.info(f"\nSchema: {schema_name}")
                
                # Get tables in schema
                tables = conn.execute(text(f"""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = '{schema_name}'
                    AND table_type = 'BASE TABLE'
                """)).fetchall()
                
                if not tables:
                    logger.info("  No tables found")
                    continue
                
                for table in tables:
                    table_name = table[0]
                    logger.info(f"\n  Table: {table_name}")
                    
                    # Get column information
                    columns = conn.execute(text(f"""
                        SELECT 
                            column_name, 
                            data_type, 
                            is_nullable,
                            column_default
                        FROM information_schema.columns
                        WHERE table_schema = '{schema_name}'
                        AND table_name = '{table_name}'
                        ORDER BY ordinal_position
                    """)).fetchall()
                    
                    for col in columns:
                        nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                        default = f"DEFAULT {col[3]}" if col[3] else ""
                        logger.info(f"    {col[0]}: {col[1]} {nullable} {default}")
                    
                    # Get primary key
                    pk = conn.execute(text(f"""
                        SELECT c.column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
                        JOIN information_schema.columns AS c 
                            ON c.table_schema = tc.constraint_schema
                            AND tc.table_name = c.table_name 
                            AND ccu.column_name = c.column_name
                        WHERE constraint_type = 'PRIMARY KEY'
                            AND tc.table_schema = '{schema_name}'
                            AND tc.table_name = '{table_name}';
                    """)).fetchall()
                    
                    if pk:
                        logger.info(f"    Primary Key: {', '.join(p[0] for p in pk)}")
                    
                    # Get foreign keys
                    fks = conn.execute(text(f"""
                        SELECT
                            kcu.column_name,
                            ccu.table_schema AS foreign_table_schema,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name
                        FROM information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                            ON tc.constraint_name = kcu.constraint_name
                            AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu
                            ON ccu.constraint_name = tc.constraint_name
                            AND ccu.table_schema = tc.table_schema
                        WHERE tc.constraint_type = 'FOREIGN KEY'
                            AND tc.table_schema = '{schema_name}'
                            AND tc.table_name = '{table_name}';
                    """)).fetchall()
                    
                    if fks:
                        logger.info("    Foreign Keys:")
                        for fk in fks:
                            logger.info(f"      {fk[0]} -> {fk[1]}.{fk[2]}.{fk[3]}")

    except Exception as e:
        logger.error(f"Error checking database state: {str(e)}")
        raise

if __name__ == "__main__":
    check_db_state() 