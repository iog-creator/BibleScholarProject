from sqlalchemy import create_engine, text
from db_config import get_db_params

def check_table_schema():
    """Check the schema of the versification_mappings table."""
    try:
        db_params = get_db_params()
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}')
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'bible' 
                AND table_name = 'versification_mappings'
                ORDER BY ordinal_position;
            """))
            
            print("\nTable structure for bible.versification_mappings:")
            print("=" * 80)
            print(f"{'Column Name':<20} {'Data Type':<15} {'Default':<25} {'Nullable':<8}")
            print("-" * 80)
            
            for row in result:
                print(f"{row[0]:<20} {row[1]:<15} {str(row[2] or 'None'):<25} {row[3]:<8}")
    except Exception as e:
        print(f"Error checking schema: {str(e)}")
        raise

if __name__ == "__main__":
    check_table_schema() 