"""
Main ETL script for loading Bible text data into the database.
This is the primary script that should be used for loading the core Bible text data.

Input Files Used:
- TAHOT files (Hebrew Old Testament):
  - TAHOT Gen-Deu - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt: Genesis through Deuteronomy
  - TAHOT Jos-Est - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt: Joshua through Esther
  - TAHOT Job-Sng - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt: Job through Song of Solomon
  - TAHOT Isa-Mal - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt: Isaiah through Malachi
- TAGNT files (Greek New Testament):
  - TAGNT Mat-Jhn - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt: Matthew through John
  - TAGNT Act-Rev - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt: Acts through Revelation

Features:
- Processes verse data with word-by-word analysis
- Handles Strong's numbers and morphology codes
- Supports manuscript variations and textual traditions
- Creates structured JSONB data for efficient querying
- Implements batch processing with error handling
- Maintains data integrity with proper transaction management

Database Schema:
--------------
Core Tables:
- bible.books: Book metadata and chapter counts
- bible.verses: Core verse data with JSONB extensions

Data Processing:
--------------
1. File Processing:
   - Reads and validates input files
   - Parses verse and word records
   - Extracts linguistic metadata

2. Data Transformation:
   - Structures verse data hierarchically
   - Processes Strong's references
   - Handles morphology codes
   - Creates JSONB fields

3. Database Operations:
   - Clears existing data
   - Inserts books metadata
   - Loads verses in batches
   - Creates necessary indexes

Usage:
    python etl_bible_texts.py

Environment Variables:
--------------------
Required:
- POSTGRES_DB: Database name
- POSTGRES_USER: Database user
- POSTGRES_PASSWORD: Database password

Optional:
- POSTGRES_HOST: Database host (default: localhost)
- POSTGRES_PORT: Database port (default: 5432)
- BATCH_SIZE: Batch size for processing (default: 1000)
- LOG_LEVEL: Logging level (default: INFO)

Dependencies:
------------
Core:
- pandas
- psycopg2-binary
- sqlalchemy
- python-dotenv
- logging

Sample Queries:
-------------
1. Get verse text with Strong's numbers:
   ```sql
   SELECT book_name, chapter, verse, word,
          jsonb_array_elements_text(strongs_json) as strongs_ref
   FROM bible.verses
   WHERE book_name = 'John'
   AND chapter = 3
   AND verse = 16;
   ```

2. Find verses by morphology:
   ```sql
   SELECT book_name, chapter, verse, word
   FROM bible.verses
   WHERE morphology_json @> '["V-AAI-3S"]'
   ORDER BY book_name, chapter, verse;
   ```

3. Get book statistics:
   ```sql
   SELECT book_name, testament, chapters, verses
   FROM bible.books
   ORDER BY book_number;
   ```

Note:
----
This script is part of the STEPBible data integration project.
All data is created by Tyndale House Cambridge and curated by STEPBible.org.
Please credit "STEP Bible" and link to www.STEPBible.org.

Author: STEPBible Data Integration Team
Version: 1.0.0
License: CC BY (Creative Commons Attribution)
"""

import pandas as pd
import os
import json
from typing import Dict, List, Tuple
import csv
import re
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from db_utils import batch_insert_verses
from models import Book, Verse
from db_config import get_db_params
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('etl_bible_texts.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Global variables
all_verses = []
bible_df = None

# Book order and testament information
OLD_TESTAMENT_BOOKS = {
    'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
    'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings',
    '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah',
    'Esther', 'Job', 'Psalms', 'Proverbs', 'Ecclesiastes',
    'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations',
    'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah',
    'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai',
    'Zechariah', 'Malachi'
}

BOOK_ORDER = {
    # Old Testament
    'Genesis': 1, 'Exodus': 2, 'Leviticus': 3, 'Numbers': 4,
    'Deuteronomy': 5, 'Joshua': 6, 'Judges': 7, 'Ruth': 8,
    '1 Samuel': 9, '2 Samuel': 10, '1 Kings': 11, '2 Kings': 12,
    '1 Chronicles': 13, '2 Chronicles': 14, 'Ezra': 15,
    'Nehemiah': 16, 'Esther': 17, 'Job': 18, 'Psalms': 19,
    'Proverbs': 20, 'Ecclesiastes': 21, 'Song of Solomon': 22,
    'Isaiah': 23, 'Jeremiah': 24, 'Lamentations': 25,
    'Ezekiel': 26, 'Daniel': 27, 'Hosea': 28, 'Joel': 29,
    'Amos': 30, 'Obadiah': 31, 'Jonah': 32, 'Micah': 33,
    'Nahum': 34, 'Habakkuk': 35, 'Zephaniah': 36, 'Haggai': 37,
    'Zechariah': 38, 'Malachi': 39,
    # New Testament
    'Matthew': 40, 'Mark': 41, 'Luke': 42, 'John': 43,
    'Acts': 44, 'Romans': 45, '1 Corinthians': 46,
    '2 Corinthians': 47, 'Galatians': 48, 'Ephesians': 49,
    'Philippians': 50, 'Colossians': 51, '1 Thessalonians': 52,
    '2 Thessalonians': 53, '1 Timothy': 54, '2 Timothy': 55,
    'Titus': 56, 'Philemon': 57, 'Hebrews': 58, 'James': 59,
    '1 Peter': 60, '2 Peter': 61, '1 John': 62, '2 John': 63,
    '3 John': 64, 'Jude': 65, 'Revelation': 66
}

def read_bible_file(file_path: str) -> pd.DataFrame:
    """
    Read a Bible text file and convert it to a DataFrame.
    
    The file format is tab-separated with potential multi-line records.
    Each verse starts with a # line containing the reference and full text.
    Subsequent lines contain word-by-word analysis.
    
    Args:
        file_path: Path to the Bible text file
        
    Returns:
        DataFrame containing the parsed Bible text data with one row per verse
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return pd.DataFrame()
        
    try:
        # Dictionary to store verse data
        verses = {}  # key: (book, chapter, verse), value: verse data
        current_verse_ref = None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and license/header information
                if not line or 'STEPBible.org' in line or line.startswith(('Data created by', 'This licence')):
                    continue
                
                # New verse reference line
                if line.startswith('# '):
                    # Extract reference and full text
                    parts = line[2:].split(' ', 1)
                    if len(parts) < 2:
                        continue
                        
                    ref, full_text = parts
                    match = re.match(r'([1-3]?[A-Za-z]+)\.(\d+)\.(\d+)', ref)
                    if not match:
                        continue
                        
                    book, chapter, verse = match.groups()
                    try:
                        chapter = int(chapter)
                        verse = int(verse)
                    except ValueError:
                        logging.warning(f"Invalid chapter/verse number in line: {line}")
                        continue
                        
                    current_verse_ref = (book, chapter, verse)
                    verses[current_verse_ref] = {
                        'full_text': full_text,
                        'words': [],
                        'strongs': [],
                        'morphology': [],
                        'translation': []
                    }
                    
                # Skip translation and grammar lines
                elif line.startswith('#_'):
                    continue
                    
                # Word analysis line
                elif current_verse_ref and '\t' in line:
                    fields = line.split('\t')
                    if len(fields) >= 4:
                        ref_num = fields[0]  # e.g., Mat.1.1#01
                        word_type = fields[1]  # e.g., NKO
                        greek_hebrew = fields[2]
                        translation = fields[3]
                        strongs = fields[4] if len(fields) > 4 else ''
                        morphology = fields[5] if len(fields) > 5 else ''
                        
                        verse_data = verses[current_verse_ref]
                        verse_data['words'].append(greek_hebrew)
                        if strongs:
                            verse_data['strongs'].append(strongs)
                        if morphology:
                            verse_data['morphology'].append(morphology)
                        verse_data['translation'].append(translation)
        
        # Convert verse dictionary to records
        records = []
        for (book, chapter, verse), verse_data in verses.items():
            record = {
                'book_name': book,
                'chapter': chapter,
                'verse': verse,
                'word': verse_data['full_text'],  # Full verse text
                'transliteration': ' '.join(verse_data['words']),  # Original language text
                'strongs': ' '.join(verse_data['strongs']),  # Space-separated list
                'morphology': ' '.join(verse_data['morphology']),  # Space-separated list
                'gloss': ' '.join(verse_data['translation']),  # English translation
                'strongs_json': json.dumps(verse_data['strongs']) if verse_data['strongs'] else None,
                'morphology_json': json.dumps(verse_data['morphology']) if verse_data['morphology'] else None
            }
            records.append(record)
            
        df = pd.DataFrame(records)
        logging.info(f"Successfully processed {len(df)} unique verses from {file_path}")
        return df
        
    except Exception as e:
        logging.error(f"Error processing {file_path}: {str(e)}")
        return pd.DataFrame()

def extract_books_info(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract information about books from the verse DataFrame.
    This includes the number of chapters and verses per book.
    
    Args:
        df: DataFrame containing verse data
        
    Returns:
        DataFrame containing book information
    """
    if df.empty:
        logger.error("No verses found in DataFrame")
        return pd.DataFrame()
    
    try:
        # Calculate verses and chapters per book
        book_stats = df.groupby('book_name').agg({
            'chapter': ['nunique', 'max'],
            'verse': 'count'
        }).reset_index()
        
        # Flatten column names
        book_stats.columns = ['book_name', 'chapters', 'max_chapter', 'verses']
        
        # Use max_chapter as chapter count (more accurate than nunique which might miss empty chapters)
        book_stats['chapters'] = book_stats['max_chapter']
        book_stats = book_stats.drop('max_chapter', axis=1)
        
        # Add testament and book number information
        book_stats['testament'] = book_stats['book_name'].apply(
            lambda x: 'OT' if x in OLD_TESTAMENT_BOOKS else 'NT'
        )
        
        # Create a mapping from abbreviated book names to full names
        abbrev_to_full = {
            'Gen': 'Genesis', 'Exo': 'Exodus', 'Lev': 'Leviticus', 'Num': 'Numbers',
            'Deu': 'Deuteronomy', 'Jos': 'Joshua', 'Jdg': 'Judges', 'Rut': 'Ruth',
            '1Sa': '1 Samuel', '2Sa': '2 Samuel', '1Ki': '1 Kings', '2Ki': '2 Kings',
            '1Ch': '1 Chronicles', '2Ch': '2 Chronicles', 'Ezr': 'Ezra',
            'Neh': 'Nehemiah', 'Est': 'Esther', 'Job': 'Job', 'Psa': 'Psalms',
            'Pro': 'Proverbs', 'Ecc': 'Ecclesiastes', 'Sng': 'Song of Solomon',
            'Isa': 'Isaiah', 'Jer': 'Jeremiah', 'Lam': 'Lamentations',
            'Ezk': 'Ezekiel', 'Dan': 'Daniel', 'Hos': 'Hosea', 'Jol': 'Joel',
            'Amo': 'Amos', 'Oba': 'Obadiah', 'Jon': 'Jonah', 'Mic': 'Micah',
            'Nam': 'Nahum', 'Hab': 'Habakkuk', 'Zep': 'Zephaniah', 'Hag': 'Haggai',
            'Zec': 'Zechariah', 'Mal': 'Malachi', 'Mat': 'Matthew', 'Mrk': 'Mark',
            'Luk': 'Luke', 'Jhn': 'John', 'Act': 'Acts', 'Rom': 'Romans',
            '1Co': '1 Corinthians', '2Co': '2 Corinthians', 'Gal': 'Galatians',
            'Eph': 'Ephesians', 'Php': 'Philippians', 'Col': 'Colossians',
            '1Th': '1 Thessalonians', '2Th': '2 Thessalonians', '1Ti': '1 Timothy',
            '2Ti': '2 Timothy', 'Tit': 'Titus', 'Phm': 'Philemon', 'Heb': 'Hebrews',
            'Jas': 'James', '1Pe': '1 Peter', '2Pe': '2 Peter', '1Jn': '1 John',
            '2Jn': '2 John', '3Jn': '3 John', 'Jud': 'Jude', 'Rev': 'Revelation'
        }
        
        # Map abbreviated names to full names and get book numbers
        book_stats['book_number'] = book_stats['book_name'].map(
            lambda x: BOOK_ORDER.get(abbrev_to_full.get(x, x), 0)
        ).astype(int)
        
        # Sort by book number
        book_stats = book_stats.sort_values('book_number')
        
        # Log book statistics
        logger.info("\nBook Statistics:")
        for _, row in book_stats.iterrows():
            logger.info(f"{row['book_name']}: {row['verses']} verses in {row['chapters']} chapters")
        
        logger.info(f"Processed {len(book_stats)} books")
        return book_stats
        
    except Exception as e:
        logger.error(f"Error extracting book information: {str(e)}")
        return pd.DataFrame()

def parse_strongs_field(raw_text: str) -> List[Dict[str, str]]:
    """Parse a raw Strong's field into a structured list of references.
    
    Args:
        raw_text (str): Raw Strong's field text (e.g., "dStrongs {H0376G} {H1961} H9003/{H0776G}\H9014")
        
    Returns:
        List[Dict[str, str]]: List of parsed Strong's references with their attributes
        
    Example:
        >>> parse_strongs_field("dStrongs {H0376G} {H1961} H9003/{H0776G}\H9014")
        [
            {"base": "H0376", "disamb": "G"},
            {"base": "H1961"},
            {"base": "H9003", "related": [{"base": "H0776", "disamb": "G"}, {"base": "H9014"}]}
        ]
    """
    if not raw_text or pd.isna(raw_text):
        return []
    
    # Remove any prefix like "dStrongs"
    raw_text = re.sub(r'^dStrongs\s+', '', raw_text.strip())
    
    refs = []
    # Split on whitespace to get individual references
    tokens = raw_text.split()
    
    for token in tokens:
        # Remove braces if present
        token = token.strip('{}')
        
        # Check if this is a compound reference (contains / or \)
        if '/' in token or '\\' in token:
            parts = re.split(r'[/\\]', token)
            base_ref = parts[0]
            related_refs = parts[1:]
            
            # Parse the base reference
            base_match = re.match(r'([HG]\d+)([A-Z])?', base_ref)
            if base_match:
                ref_obj = {
                    "base": base_match.group(1),
                    "related": []
                }
                if base_match.group(2):
                    ref_obj["disamb"] = base_match.group(2)
                
                # Parse related references
                for rel in related_refs:
                    rel_match = re.match(r'([HG]\d+)([A-Z])?', rel)
                    if rel_match:
                        rel_obj = {"base": rel_match.group(1)}
                        if rel_match.group(2):
                            rel_obj["disamb"] = rel_match.group(2)
                        ref_obj["related"].append(rel_obj)
                
                refs.append(ref_obj)
        else:
            # Simple reference
            match = re.match(r'([HG]\d+)([A-Z])?', token)
            if match:
                ref_obj = {"base": match.group(1)}
                if match.group(2):
                    ref_obj["disamb"] = match.group(2)
                refs.append(ref_obj)
    
    return refs

def parse_morphology_field(raw_text: str) -> List[str]:
    """Parse a raw morphology field into a list of morphology codes.
    
    Args:
        raw_text (str): Raw morphology field text
        
    Returns:
        List[str]: List of morphology codes
        
    Example:
        >>> parse_morphology_field("G:A G:N-F H:V")
        ["G:A", "G:N-F", "H:V"]
    """
    if not raw_text or pd.isna(raw_text):
        return []
    
    # Split by common delimiters (space, comma, semicolon)
    codes = re.split(r'[,;\s]+', raw_text.strip())
    
    # Filter valid codes (must contain a colon)
    valid_codes = [code for code in codes if ':' in code]
    
    return valid_codes

def process_verse_data(row: pd.Series) -> pd.Series:
    """Process a verse row to add JSONB fields for Strong's numbers and morphology.
    
    Args:
        row (pd.Series): DataFrame row containing verse data
        
    Returns:
        pd.Series: Updated row with new JSONB fields
    """
    # Parse Strong's numbers
    strongs_data = parse_strongs_field(row.get('strongs', ''))
    row['strongs_json'] = json.dumps(strongs_data, ensure_ascii=False)
    
    # Parse morphology codes
    morph_data = parse_morphology_field(row.get('morphology', ''))
    row['morphology_json'] = json.dumps(morph_data, ensure_ascii=False)
    
    return row

def extract_verses_info(df):
    """Extract verses information."""
    verses_df = df.copy()
    verses_df = verses_df.rename(columns={
        'Book': 'book_name',
        'Chapter': 'chapter',
        'Verse': 'verse',
        'Word': 'word',
        'Transliteration': 'transliteration',
        'Strongs': 'strongs',
        'Grammar': 'morphology',
        'Translation': 'gloss',
        'Meaning': 'function',
        'Root': 'root'
    })
    
    # Log original verse count
    original_count = len(verses_df)
    logger.info(f"Processing {original_count} verses")
    
    # Convert numeric columns with better error handling
    def safe_numeric_convert(value):
        try:
            if pd.isna(value):
                return None
            return int(float(str(value).strip()))
        except (ValueError, TypeError):
            return None
    
    verses_df['chapter'] = verses_df['chapter'].apply(safe_numeric_convert)
    verses_df['verse'] = verses_df['verse'].apply(safe_numeric_convert)
    
    # Log which verses are being dropped
    invalid_verses = verses_df[verses_df[['chapter', 'verse']].isna().any(axis=1)]
    if not invalid_verses.empty:
        logger.warning(f"Found {len(invalid_verses)} verses with invalid chapter/verse numbers:")
        for _, row in invalid_verses.iterrows():
            logger.warning(f"Invalid verse: {row['book_name']} {row.get('chapter', 'NA')}:{row.get('verse', 'NA')}")
            logger.warning(f"Original values - Chapter: {row.get('chapter')}, Verse: {row.get('verse')}")
    
    # Drop any rows with invalid chapter/verse numbers
    verses_df = verses_df.dropna(subset=['chapter', 'verse'])
    
    # Log how many verses were dropped
    dropped_count = original_count - len(verses_df)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} verses due to invalid chapter/verse numbers")
    
    # Process JSONB fields
    verses_df = verses_df.apply(process_verse_data, axis=1)
    
    # Sort by book, chapter, verse
    verses_df['book_number'] = verses_df['book_name'].map(BOOK_ORDER)
    verses_df = verses_df.sort_values(['book_number', 'chapter', 'verse'])
    verses_df = verses_df.drop('book_number', axis=1)
    
    # Validate final verse count
    final_count = len(verses_df)
    logger.info(f"Final verse count after processing: {final_count}")
    
    return verses_df[['book_name', 'chapter', 'verse', 'word', 'transliteration', 
                     'strongs', 'morphology', 'gloss', 'function', 'root',
                     'strongs_json', 'morphology_json']]

def process_verses(df: pd.DataFrame) -> pd.DataFrame:
    """Process verses data."""
    verses = df[['Book', 'Chapter', 'Verse', 'Text']]
    if 'Strongs' in df.columns:
        verses['strongs_numbers'] = df['Strongs']
    if 'Morphology' in df.columns:
        verses['morphology'] = df['Morphology']
    return verses

def main():
    """Main ETL process for loading Bible text data into database."""
    try:
        logger.info("Starting ETL process...")
        
        # Process Hebrew Old Testament
        logger.info("Processing Hebrew Old Testament...")
        hebrew_df = process_hebrew_old_testament()
        if hebrew_df.empty:
            logger.warning("No Hebrew Old Testament verses were processed")
        else:
            logger.info(f"Processed {len(hebrew_df)} Hebrew verses")
        
        # Process Greek New Testament
        logger.info("Processing Greek New Testament...")
        greek_df = process_greek_new_testament()
        if greek_df.empty:
            logger.warning("No Greek New Testament verses were processed")
        else:
            logger.info(f"Processed {len(greek_df)} Greek verses")
        
        # Combine verses
        bible_df = pd.concat([hebrew_df, greek_df], ignore_index=True)
        if bible_df.empty:
            raise ValueError("No verses were processed successfully")
        
        logger.info(f"Total verses processed: {len(bible_df)}")
        
        # Process books information
        logger.info("Processing books information...")
        books_df = extract_books_info(bible_df)
        if books_df.empty:
            raise ValueError("No books information could be extracted")
        
        logger.info(f"Processed {len(books_df)} books")
        
        # Initialize database
        logger.info("Initializing database connection...")
        db_params = get_db_params()
        engine = create_engine(
            f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}",
            echo=False
        )
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Clear existing data
            logger.info("Clearing existing data...")
            session.execute(text("TRUNCATE TABLE bible.verses CASCADE"))
            session.execute(text("TRUNCATE TABLE bible.books CASCADE"))
            session.commit()
            
            # Insert books
            logger.info("Inserting books...")
            for _, row in books_df.iterrows():
                book = Book(
                    book_name=row['book_name'],
                    testament=row['testament'],
                    book_number=row['book_number'],
                    chapters=row['chapters'],
                    verses=row['verses']
                )
                session.add(book)
            session.commit()
            
            # Insert verses in chunks
            logger.info("Inserting verses...")
            chunk_size = 1000
            for i in range(0, len(bible_df), chunk_size):
                chunk = bible_df.iloc[i:i + chunk_size]
                verses = []
                for _, row in chunk.iterrows():
                    verse = Verse(
                        book_name=row['book_name'],
                        chapter=int(row['chapter']),
                        verse=int(row['verse']),
                        word=row['word'],
                        transliteration=row.get('transliteration'),
                        strongs=row.get('strongs'),
                        morphology=row.get('morphology'),
                        gloss=row.get('gloss'),
                        strongs_json=json.dumps(parse_strongs_field(row.get('strongs', ''))),
                        morphology_json=json.dumps(parse_morphology_field(row.get('morphology', '')))
                    )
                    verses.append(verse)
                
                session.bulk_save_objects(verses)
                session.commit()
                logger.info(f"Inserted verses {i+1} to {min(i+chunk_size, len(bible_df))}")
            
            # Create indexes
            logger.info("Creating indexes...")
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_verses_book_chapter_verse 
                ON bible.verses (book_name, chapter, verse);
                
                CREATE INDEX IF NOT EXISTS idx_verses_strongs 
                ON bible.verses USING gin (strongs_json);
                
                CREATE INDEX IF NOT EXISTS idx_verses_morphology 
                ON bible.verses USING gin (morphology_json);
            """))
            session.commit()
            
            logger.info("ETL process completed successfully!")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"ETL process failed: {str(e)}")
        raise
    finally:
        logger.info("ETL process finished.")

def process_hebrew_old_testament():
    """Process Hebrew Old Testament files."""
    hebrew_files = [
        "Translators Amalgamated OT+NT/TAHOT Gen-Deu - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
        "Translators Amalgamated OT+NT/TAHOT Jos-Est - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
        "Translators Amalgamated OT+NT/TAHOT Job-Sng - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
        "Translators Amalgamated OT+NT/TAHOT Isa-Mal - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt"
    ]
    
    all_verses = []
    for file_path in hebrew_files:
        try:
            df = read_bible_file(file_path)
            if df is not None and not df.empty:
                all_verses.append(df)
                logging.info(f"Successfully processed {file_path}")
            else:
                logging.warning(f"No data loaded from {file_path}")
        except Exception as e:
            logging.error(f"Error processing {file_path}: {str(e)}")
    
    if all_verses:
        return pd.concat(all_verses, ignore_index=True)
    return pd.DataFrame()

def process_greek_new_testament():
    """Process Greek New Testament files."""
    greek_files = [
        "Translators Amalgamated OT+NT/TAGNT Mat-Jhn - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt",
        "Translators Amalgamated OT+NT/TAGNT Act-Rev - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt"
    ]
    
    all_verses = []
    for file_path in greek_files:
        try:
            df = read_bible_file(file_path)
            if df is not None and not df.empty:
                all_verses.append(df)
                logging.info(f"Successfully processed {file_path}")
            else:
                logging.warning(f"No data loaded from {file_path}")
        except Exception as e:
            logging.error(f"Error processing {file_path}: {str(e)}")
    
    if all_verses:
        return pd.concat(all_verses, ignore_index=True)
    return pd.DataFrame()

def process_books_info():
    """Process book information and save to CSV."""
    global all_verses, bible_df
    
    try:
        # Combine all verses into a single DataFrame
        if not all_verses:
            raise ValueError("No verses have been processed yet")
            
        bible_df = pd.concat(all_verses, ignore_index=True)
        logger.info(f"Total verses processed: {len(bible_df)}")
        
        # Extract book statistics
        book_stats = []
        for book_name in sorted(bible_df['book_name'].unique()):
            book_verses = bible_df[bible_df['book_name'] == book_name]
            num_verses = len(book_verses)
            num_chapters = book_verses['chapter'].nunique()
            testament = 'Old Testament' if book_name in OLD_TESTAMENT_BOOKS else 'New Testament'
            book_order = BOOK_ORDER.get(book_name, 999)  # Default to high number if not found
            
            book_stats.append({
                'book_name': book_name,
                'num_verses': num_verses,
                'num_chapters': num_chapters,
                'testament': testament,
                'book_order': book_order
            })
            logger.info(f"{book_name}: {num_verses} verses in {num_chapters} chapters")
        
        # Create books DataFrame and save to CSV
        books_df = pd.DataFrame(book_stats)
        books_df.to_csv('books.csv', index=False)
        bible_df.to_csv('verses.csv', index=False)
        logger.info("Successfully saved books.csv and verses.csv")
        
    except Exception as e:
        logger.error(f"Error in process_books_info: {str(e)}")
        raise

def process_verses_info():
    """Process verses information."""
    print("\nProcessing verses information...")
    verses_df = extract_verses_info(bible_df)
    verses_df.to_csv('verses.csv', index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)
    print("Saved verses.csv")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error in ETL process: {str(e)}")
        sys.exit(1) 