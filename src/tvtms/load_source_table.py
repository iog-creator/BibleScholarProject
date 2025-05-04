"""
ETL script to load Bible text from STEPBible-Data/Translators Amalgamated OT+NT/ into bible.source_table.

- Loads all TAHOT (OT) and TAGNT (NT) files in the directory
- Extracts: tradition, book_id, chapter, verse, subverse, text
- Inserts into bible.source_table
- Uses 'Amalgamated' as the tradition label
- Logs progress and errors

Usage:
    python -m src.tvtms.load_source_table
"""
import os
import logging
import pandas as pd
from pathlib import Path
from tvtms.database import get_db_connection
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/load_source_table.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Directory containing source files
SOURCE_DIR = Path('STEPBible-Data/Translators Amalgamated OT+NT')
FILE_PATTERNS = [
    'TAHOT*.txt',  # Old Testament
    'TAGNT*.txt',  # New Testament
]
TRADITION = 'Amalgamated'

REQUIRED_COLUMNS = ['book', 'chapter', 'verse', 'text']

# Mapping from source book IDs to database book IDs
BOOK_ID_MAPPING = {
    # Hebrew Bible (Tanakh)
    'Gen': 'Gen', 'Exo': 'Exo', 'Lev': 'Lev', 'Num': 'Num', 'Deu': 'Deu',
    'Jos': 'Jos', 'Jdg': 'Jdg', 'Rut': 'Rth', '1Sa': '1Sa', '2Sa': '2Sa',
    '1Ki': '1Ki', '2Ki': '2Ki', '1Ch': '1Ch', '2Ch': '2Ch', 'Ezr': 'Ezr',
    'Neh': 'Neh', 'Est': 'Est', 'Job': 'Job', 'Psa': 'Psa', 'Pro': 'Pro',
    'Ecc': 'Ecc', 'Sng': 'Sng', 'Isa': 'Isa', 'Jer': 'Jer', 'Lam': 'Lam',
    'Ezk': 'Ezk', 'Dan': 'Dan', 'Hos': 'Hos', 'Jol': 'Jol', 'Amo': 'Amo',
    'Oba': 'Oba', 'Jon': 'Jon', 'Mic': 'Mic', 'Nah': 'Nam', 'Nam': 'Nam', 'Hab': 'Hab',
    'Zep': 'Zep', 'Hag': 'Hag', 'Zec': 'Zec', 'Mal': 'Mal',
    
    # New Testament
    'Mat': 'Mat', 'Mrk': 'Mrk', 'Luk': 'Luk', 'Jhn': 'Jhn', 'Act': 'Act',
    'Rom': 'Rom', '1Co': '1Co', '2Co': '2Co', 'Gal': 'Gal', 'Eph': 'Eph',
    'Php': 'Php', 'Col': 'Col', '1Th': '1Th', '2Th': '2Th', '1Ti': '1Ti',
    '2Ti': '2Ti', 'Tit': 'Tit', 'Phm': 'Phm', 'Heb': 'Heb', 'Jas': 'Jas',
    '1Pe': '1Pe', '2Pe': '2Pe', '1Jn': '1Jn', '2Jn': '2Jn', '3Jn': '3Jn',
    'Jud': 'Jud', 'Rev': 'Rev',
    
    # Deuterocanonical/Apocryphal books
    'Tob': 'Tob', 'Jdt': 'Jdt', 'Wis': 'Wis', 'Sir': 'Sir', 'Bar': 'Bar',
    '1Ma': '1Ma', '2Ma': '2Ma', '3Ma': '3Ma', '4Ma': '4Ma', 'Man': 'Man',
    '1Es': '1Es', '2Es': '2Es', 'Sus': 'Sus', 'Bel': 'Bel',
    'EstA': 'EstA', 'EstB': 'EstB', 'EstC': 'EstC', 'EstD': 'EstD', 'EstE': 'EstE',
    'EstF': 'EstF', 'AddEst': 'AddEst', 'PrAzar': 'PrAzar', 'LJe': 'LJe'
}

def parse_ot_file(file_path):
    """Parse a STEPBible TAHOT (Old Testament) text file and return a DataFrame with required columns."""
    logger.info(f"Parsing OT file: {file_path}")
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()
    # Find the header row
    header_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith('Eng (Heb) Ref & Type'):
            header_idx = idx
            break
    if header_idx is None:
        logger.error(f"Header not found in {file_path}")
        return pd.DataFrame()
    # Get column names from header
    header_cols = re.split(r'\s{2,}|\t', lines[header_idx].strip())
    # Find the index of the Translation column
    try:
        translation_idx = header_cols.index('Translation')
    except ValueError:
        logger.error(f"'Translation' column not found in header for {file_path}")
        return pd.DataFrame()
    # Data starts after header
    data_rows = []
    for line in lines[header_idx+1:]:
        if not line.strip() or line.startswith('Eng (Heb) Ref & Type'):
            continue
        parts = line.strip().split('\t')
        if len(parts) <= translation_idx:
            continue
        ref = parts[0]
        # Match e.g. Deu.33.16#01=L
        m = re.match(r'([A-Za-z0-9]+)\.(\d+)\.(\d+)(?:#(\d+))?(?:=([A-Z]))?', ref)
        if not m:
            continue
        source_book_id, chapter, verse, subverse, _ = m.groups()
        
        # Map the source book ID to the database book ID
        if source_book_id in BOOK_ID_MAPPING:
            book_id = BOOK_ID_MAPPING[source_book_id]
        else:
            logger.warning(f"Unknown book ID: {source_book_id} in {file_path}")
            continue
            
        text = parts[translation_idx]
        data_rows.append({
            'source_tradition': TRADITION,
            'book_id': book_id,
            'chapter': int(chapter) if chapter else None,
            'verse': int(verse) if verse else None,
            'subverse': subverse if subverse else None,
            'text': text
        })
    if not data_rows:
        logger.warning(f"No data rows found in {file_path}")
        return pd.DataFrame()
    return pd.DataFrame(data_rows)

def parse_nt_file(file_path):
    """Parse a STEPBible TAGNT (New Testament) text file and return a DataFrame with required columns."""
    logger.info(f"Parsing NT file: {file_path}")
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()
    
    data_rows = []
    # Process line by line
    for i, line in enumerate(lines):
        # Skip headers and non-data lines
        if not line.strip() or line.startswith('#') or 'Word & Type' in line:
            continue
        
        # Look for lines with verse references like Mat.1.2#01=NKO
        if re.match(r'[A-Za-z0-9]+\.\d+\.\d+#\d+=', line):
            parts = line.strip().split('\t')
            if len(parts) < 3:  # Need at least reference, Greek, and English
                continue
                
            ref = parts[0]
            # Extract book, chapter, verse, subverse
            m = re.match(r'([A-Za-z0-9]+)\.(\d+)\.(\d+)#(\d+)=', ref)
            if not m:
                continue
                
            source_book_id, chapter, verse, subverse = m.groups()
            
            # Map the source book ID to the database book ID
            if source_book_id in BOOK_ID_MAPPING:
                book_id = BOOK_ID_MAPPING[source_book_id]
            else:
                logger.warning(f"Unknown book ID: {source_book_id} in {file_path}")
                continue
            
            english_text = parts[2]  # English translation is in the third column
            
            # Skip empty translations or special markers
            if english_text.startswith('<') and english_text.endswith('>'):
                continue
                
            data_rows.append({
                'source_tradition': TRADITION,
                'book_id': book_id,
                'chapter': int(chapter) if chapter else None,
                'verse': int(verse) if verse else None,
                'subverse': subverse if subverse else None,
                'text': english_text
            })
    
    if not data_rows:
        logger.warning(f"No data rows found in {file_path}")
        return pd.DataFrame()
        
    # Group by book, chapter, verse to combine words into full verses
    df = pd.DataFrame(data_rows)
    grouped = df.groupby(['book_id', 'chapter', 'verse', 'subverse']).agg({
        'source_tradition': 'first',
        'text': lambda x: ' '.join(x)
    }).reset_index()
    
    return grouped

def parse_file(file_path):
    """Parse a STEPBible text file based on its type (OT or NT)."""
    file_name = os.path.basename(file_path)
    if file_name.startswith('TAHOT'):
        return parse_ot_file(file_path)
    elif file_name.startswith('TAGNT'):
        return parse_nt_file(file_path)
    else:
        logger.warning(f"Unknown file type: {file_name}")
        return pd.DataFrame()

def load_to_db(df):
    """Insert DataFrame rows into bible.source_table."""
    if df.empty:
        logger.warning("No data to load.")
        return 0
    conn = get_db_connection()
    inserted = 0
    try:
        with conn.cursor() as cur:
            # First, clear existing data for the Amalgamated tradition
            cur.execute("DELETE FROM bible.source_table WHERE source_tradition = %s", (TRADITION,))
            logger.info(f"Cleared existing data for tradition: {TRADITION}")
            
            # Insert new data
            data = [
                (
                    row['source_tradition'], row['book_id'], row['chapter'],
                    row['verse'], row['subverse'], row['text'], False
                )
                for _, row in df.iterrows()
            ]
            cur.executemany("""
                INSERT INTO bible.source_table (
                    source_tradition, book_id, chapter, verse, subverse, text, dealt_with
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_tradition, book_id, chapter, verse, subverse) DO NOTHING
            """, data)
            inserted = cur.rowcount
            conn.commit()
            logger.info(f"Inserted {inserted} rows into bible.source_table.")
    except Exception as e:
        logger.error(f"Failed to insert data: {e}")
        conn.rollback()
    finally:
        conn.close()
    return inserted


def main():
    all_dfs = []
    for pattern in FILE_PATTERNS:
        for file_path in SOURCE_DIR.glob(pattern):
            df = parse_file(file_path)
            if not df.empty:
                all_dfs.append(df)
    if not all_dfs:
        logger.error("No data files loaded. Exiting.")
        return
    full_df = pd.concat(all_dfs, ignore_index=True)
    logger.info(f"Total rows to load: {len(full_df)}")
    load_to_db(full_df)

if __name__ == '__main__':
    main() 