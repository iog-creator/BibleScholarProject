#!/usr/bin/env python3
"""
TVTMS Processing Module

This module processes the expanded version of TVTMS.txt, extracting versification mappings,
rules, and documentation for loading into the PostgreSQL database.
"""

import os
import re
import logging
from typing import List, Dict, Optional, Tuple, Any
import psycopg
from psycopg.rows import dict_row
from .parser import TVTMSParser
from .validator import TVTMSValidator
from .models import Mapping, Rule, Documentation
from .database import (
    get_db_connection, create_tables, store_mappings as db_store_mappings, 
    store_rules, store_documentation, truncate_versification_mappings
)
from dotenv import load_dotenv
import sys

# Load environment variables from .env file
load_dotenv()

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

def setup_logging():
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/etl_versification.log', mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)

# Action priority order is defined in constants.py now

# Book abbreviation to full name mapping
BOOK_ABBREV_MAP = {
    # Old Testament
    'Gen': 'Genesis', 'Exo': 'Exodus', 'Lev': 'Leviticus', 'Num': 'Numbers', 'Deu': 'Deuteronomy',
    'Jos': 'Joshua', 'Jdg': 'Judges', 'Rut': 'Ruth', '1Sa': '1 Samuel', '2Sa': '2 Samuel',
    '1Ki': '1 Kings', '2Ki': '2 Kings', '1Ch': '1 Chronicles', '2Ch': '2 Chronicles',
    'Ezr': 'Ezra', 'Neh': 'Nehemiah', 'Est': 'Esther', 'Job': 'Job', 'Psa': 'Psalms',
    'Pro': 'Proverbs', 'Ecc': 'Ecclesiastes', 'Sng': 'Song of Solomon', 'Isa': 'Isaiah',
    'Jer': 'Jeremiah', 'Lam': 'Lamentations', 'Ezk': 'Ezekiel', 'Dan': 'Daniel',
    'Hos': 'Hosea', 'Joe': 'Joel', 'Amo': 'Amos', 'Oba': 'Obadiah', 'Jon': 'Jonah',
    'Mic': 'Micah', 'Nah': 'Nahum', 'Hab': 'Habakkuk', 'Zep': 'Zephaniah',
    'Hag': 'Haggai', 'Zec': 'Zechariah', 'Mal': 'Malachi',
    # New Testament
    'Mat': 'Matthew', 'Mar': 'Mark', 'Luk': 'Luke', 'Jhn': 'John',
    'Act': 'Acts', 'Rom': 'Romans', '1Co': '1 Corinthians', '2Co': '2 Corinthians',
    'Gal': 'Galatians', 'Eph': 'Ephesians', 'Php': 'Philippians', 'Col': 'Colossians',
    '1Th': '1 Thessalonians', '2Th': '2 Thessalonians', '1Ti': '1 Timothy',
    '2Ti': '2 Timothy', 'Tit': 'Titus', 'Phm': 'Philemon', 'Heb': 'Hebrews',
    'Jas': 'James', '1Pe': '1 Peter', '2Pe': '2 Peter', '1Jn': '1 John',
    '2Jn': '2 John', '3Jn': '3 John', 'Jud': 'Jude', 'Rev': 'Revelation'
}

def process_tvtms_file(file_path: str, parser: TVTMSParser = None) -> List[Mapping]:
    """Process TVTMS file and return a list of Mapping objects."""
    print(f"[process_tvtms_file] Called with file_path: {file_path}")
    try:
        logger.info(f"Processing TVTMS file: {file_path}")
        # Create a new parser only if one wasn't provided
        if parser is None:
            parser = TVTMSParser()
        # --- Build verse_counts lookup from hardcoded values ---
        verse_counts = parser.build_verse_counts()
        # ---
        mappings, rules, docs = parser.parse_file(file_path)  # Unpack the tuple
        logger.info(f"[process_tvtms_file] parse_file returned {len(mappings)} mappings")
        
        # --- Process section/range mapping lines starting with $ ---
        section_mappings = process_section_mappings(file_path, parser, verse_counts)
        logger.info(f"[process_tvtms_file] process_section_mappings returned {len(section_mappings)} mappings")
        
        # Combine all mappings
        all_mappings = mappings + section_mappings
        logger.info(f"[process_tvtms_file] Total combined mappings: {len(all_mappings)}")
        # ---

        return all_mappings
    except Exception as e:
        logger.error(f"Error processing TVTMS file: {e}")
        raise

def process_section_mappings(file_path: str, parser: TVTMSParser, verse_counts: dict) -> List[Mapping]:
    """Process the section/range mapping lines that start with $ in the TVTMS file."""
    logger.info(f"Processing section/range mappings from: {file_path}")
    section_mappings = []
    
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()
    
    # Process lines starting with $
    for line in lines:
        line = line.strip()
        if not line.startswith('$'):
            continue
        
        logger.debug(f"Processing section mapping line: {line}")
        
        # Format: $Gen.2:24--3:1    English KJV     Hebrew  Latin   Greek ...
        parts = line.split('\t')
        if len(parts) < 2:
            parts = line.split('    ')
            
        if len(parts) < 2:
            logger.warning(f"Invalid section mapping line format: {line}")
            continue
        
        ref_range = parts[0].lstrip('$').strip()
        traditions = [part.strip() for part in parts[1:] if part.strip()]
        
        try:
            # Skip complex references with alternative book notations like "4Es./2Es.7:36-105"
            if '/' in ref_range and not ref_range.startswith('Rev'):
                logger.warning(f"Skipping complex cross-book reference with alternative notation: {ref_range}")
                continue
                
            # Handle ranges with different formats
            if '--' in ref_range:
                # Format like "Gen.2:24--3:1"
                start_ref, end_ref = ref_range.split('--', 1)
                # If end_ref doesn't have book name, add it from start_ref
                if '.' not in end_ref and start_ref.count('.') > 0:
                    book_name = start_ref.split('.')[0]
                    end_ref = f"{book_name}.{end_ref}"
            elif '-' in ref_range:
                # Check if this is a format like "Psa.3:1-3:8" or "Psa.3:1-8"
                if ref_range.count(':') > 1:
                    # Format like "Psa.3:1-3:8" (chapter:verse-chapter:verse)
                    start_ref, end_ref = ref_range.split('-', 1)
                    # If end_ref doesn't have book name, add it from start_ref
                    if '.' not in end_ref and start_ref.count('.') > 0:
                        book_name = start_ref.split('.')[0]
                        end_ref = f"{book_name}.{end_ref}"
                else:
                    # Format like "Psa.3:1-8" (chapter:startVerse-endVerse)
                    book_chapter, verse_range = ref_range.split(':', 1)
                    if '-' in verse_range:
                        start_verse, end_verse = verse_range.split('-', 1)
                        start_ref = f"{book_chapter}:{start_verse}"
                        
                        # If end_verse contains a chapter reference, use it as is
                        if ':' in end_verse:
                            # If it doesn't have a book name, add it
                            if '.' not in end_verse and book_chapter.count('.') > 0:
                                book_name = book_chapter.split('.')[0]
                                end_ref = f"{book_name}.{end_verse}"
                            else:
                                end_ref = end_verse
                        else:
                            # Otherwise, use the same chapter
                            end_ref = f"{book_chapter}:{end_verse}"
                    else:
                        # Single verse, not a range
                        start_ref = ref_range
                        end_ref = ref_range
            else:
                # Simple reference, not a range
                start_ref = ref_range
                end_ref = ref_range
            
            # Parse the start and end references - handle complex verse/subverse notations
            if ':' not in start_ref and '.' in start_ref:
                # Format like "Gen.1" (whole chapter)
                book, chapter_str = start_ref.split('.', 1)
                try:
                    # Remove any suffix markers from chapter
                    if chapter_str and not chapter_str.isalnum():
                        # Just get the numeric part
                        chapter_str = ''.join(c for c in chapter_str if c.isalnum())
                    
                    if chapter_str.isalpha():
                        # Alpha-numeric chapter (A, B, C, etc.)
                        chapter = ord(chapter_str.upper()) - ord('A') + 1
                    else:
                        chapter = int(chapter_str)
                    start_book, start_chapter, start_verse = book, chapter, 1
                except ValueError:
                    logger.error(f"Error parsing chapter in reference: {start_ref}")
                    continue
            else:
                # Clean up reference before parsing
                clean_start_ref = start_ref
                # Remove suffixes like 'a', 'b' from verse numbers, just use numeric part
                if '!' in clean_start_ref or '*' in clean_start_ref:
                    parts = re.split(r'[!*]', clean_start_ref)
                    clean_start_ref = parts[0]
                
                # Normal book.chapter:verse format
                try:
                    start_book, start_chapter, start_verse = parser.parse_reference(clean_start_ref)
                except Exception as e:
                    logger.error(f"Error parsing start reference: {start_ref} - {str(e)}")
                    continue
            
            if ':' not in end_ref and '.' in end_ref:
                # Format like "Gen.1" (whole chapter)
                book, chapter_str = end_ref.split('.', 1)
                try:
                    # Remove any suffix markers from chapter
                    if chapter_str and not chapter_str.isalnum():
                        # Just get the numeric part
                        chapter_str = ''.join(c for c in chapter_str if c.isalnum())
                        
                    if chapter_str.isalpha():
                        # Alpha-numeric chapter (A, B, C, etc.)
                        chapter = ord(chapter_str.upper()) - ord('A') + 1
                    else:
                        chapter = int(chapter_str)
                    # Get the last verse of this chapter
                    max_verses = verse_counts.get(book.lower(), {}).get(chapter, 30)  # Default to 30 if unknown
                    end_book, end_chapter, end_verse = book, chapter, max_verses
                except ValueError:
                    logger.error(f"Error parsing chapter in reference: {end_ref}")
                    continue
            else:
                # Clean up reference before parsing
                clean_end_ref = end_ref
                # Remove suffixes like 'a', 'b' from verse numbers, just use numeric part
                if '!' in clean_end_ref or '*' in clean_end_ref:
                    parts = re.split(r'[!*]', clean_end_ref)
                    clean_end_ref = parts[0]
                
                # Normal book.chapter:verse format
                try:
                    end_book, end_chapter, end_verse = parser.parse_reference(clean_end_ref)
                    # If end_book is None but start_book is valid, use start_book
                    if end_book is None and start_book is not None:
                        end_book = start_book
                except Exception as e:
                    logger.error(f"Error parsing end reference: {end_ref} - {str(e)}")
                    continue
            
            # Create mappings for each tradition
            for tradition in traditions:
                if not tradition:
                    continue
                    
                # Skip invalid traditions (these are typically English names or unused meta fields)
                if tradition.lower() in ['english', 'english1', 'english2', 'english3', 'english-kjv', 
                                        'english nrsv', 'english-nrsv', 'english [no kjva]',
                                        'greek2', 'greek*', 'greek2 (eg brenton)', 'greek2 (eg.nets)',
                                        'greek (nets)', 'greek2 undivided', 'greek undivided',
                                        'latin*', 'latin2', 'latin2-dra', 'bulgarian', 'italian',
                                        'arabic', 'bangladeshi see https://www.bible.com/en-gb/bible/1681/1co.10.bengali-bsi',
                                        'german', 'tatar', 'lingala luther1545', 'nvi etc']:
                    continue
                
                # Create mappings for each verse in the range
                if start_book == end_book and start_book is not None:
                    # If same book, handle chapter and verse ranges
                    current_book = start_book
                    
                    # Ensure we have valid numeric values for chapter/verse
                    try:
                        start_chapter = int(start_chapter)
                        end_chapter = int(end_chapter)
                        start_verse = int(start_verse)
                        end_verse = int(end_verse)
                    except (TypeError, ValueError) as e:
                        logger.error(f"Invalid numeric values in range: {start_chapter}:{start_verse}-{end_chapter}:{end_verse} - {str(e)}")
                        continue
                    
                    # Map all verses in the range
                    for chapter in range(start_chapter, end_chapter + 1):
                        # Determine start and end verses for this chapter
                        if chapter == start_chapter and chapter == end_chapter:
                            # Same chapter, use start_verse to end_verse
                            verse_start, verse_end = start_verse, end_verse
                        elif chapter == start_chapter:
                            # First chapter in range, use start_verse to last verse in chapter
                            verse_start = start_verse
                            verse_end = verse_counts.get(current_book, {}).get(chapter, 30)  # Default to 30 if unknown
                        elif chapter == end_chapter:
                            # Last chapter in range, use first verse to end_verse
                            verse_start = 1
                            verse_end = end_verse
                        else:
                            # Chapter in the middle, use entire chapter
                            verse_start = 1
                            verse_end = verse_counts.get(current_book, {}).get(chapter, 30)  # Default to 30 if unknown
                            
                        for verse in range(verse_start, verse_end + 1):
                            mapping = Mapping(
                                source_tradition=tradition.lower(),
                                target_tradition='standard',
                                source_book=current_book,
                                source_chapter=chapter,
                                source_verse=verse,
                                source_subverse=None,
                                manuscript_marker=None,
                                target_book=current_book,
                                target_chapter=chapter,
                                target_verse=verse,
                                target_subverse=None,
                                mapping_type='section',
                                category=None,
                                notes=f"Auto-generated from section mapping: {ref_range}",
                                source_range_note=None,
                                target_range_note=None,
                                note_marker=None,
                                ancient_versions=None
                            )
                            section_mappings.append(mapping)
                else:
                    # Cross-book ranges are more complex - would need to know the book ordering
                    # For simplicity, we'll just warn and skip for now
                    logger.warning(f"Cross-book range not supported yet: {ref_range}")
                    
        except Exception as e:
            logger.error(f"Error processing section mapping line: {line} - {str(e)}")
            continue
    
    logger.info(f"Processed {len(section_mappings)} section mappings")
    return section_mappings

def process_actions(conn):
    """Process the actions defined in versification_mappings table in priority order."""
    logger.info("Starting to process versification actions.")
    # Import ACTION_PRIORITY here as it's only used in this function
    from .constants import ACTION_PRIORITY 
    with conn.cursor(row_factory=dict_row) as cur:
        for action_type in ACTION_PRIORITY:
            logger.info(f"Processing action type: {action_type}")
            cur.execute("""
                SELECT * FROM bible.versification_mappings
                WHERE mapping_type = %s
                ORDER BY source_tradition, source_book, source_chapter, source_verse, source_subverse; 
            """, (action_type,))
            mappings_for_action = cur.fetchall()
            
            # --- Remove IMMEDIATE print after fetch --- 
            # print(f"$$$ DEBUG: Fetched {len(mappings_for_action)} mappings for action '{action_type}'. First 5 types:")
            # for i, m_debug in enumerate(mappings_for_action[:5]):
            #      print(f"  $$$ DEBUG mapping {i}: type='{m_debug.get('mapping_type')}'") # Use .get() for safety
            # --- End IMMEDIATE print ---

            if not mappings_for_action:
                logger.info(f"No mappings found for action type: {action_type}")
                continue

            logger.info(f"Found {len(mappings_for_action)} mappings for action type: {action_type}. Processing..." )    

            # Placeholder for action-specific logic
            # Example for 'Keep':
            if action_type == 'Keep':
                keep_processed_count = 0
                keep_skipped_count = 0
                for mapping in mappings_for_action:
                    try:
                        # 1. Query source_table for text using source refs
                        # Use IS NOT DISTINCT FROM for NULL-safe comparison
                        cur.execute("""
                            SELECT text, id FROM bible.source_table 
                            WHERE source_tradition IS NOT DISTINCT FROM %s
                              AND book_id IS NOT DISTINCT FROM %s
                              AND chapter IS NOT DISTINCT FROM %s
                              AND verse IS NOT DISTINCT FROM %s
                              AND COALESCE(subverse, '') IS NOT DISTINCT FROM COALESCE(%s, '') -- Handle NULL subverse
                              AND dealt_with = FALSE; 
                        """, (
                            mapping['source_tradition'], mapping['source_book'], mapping['source_chapter'], 
                            mapping['source_verse'], mapping['source_subverse']
                        ))
                        source_rows = cur.fetchall()

                        if not source_rows:
                            # logger.warning(f"Keep Action: No undealt source text found for mapping ID {mapping['id']} - {mapping['source_tradition']}:{mapping['source_book']}.{mapping['source_chapter']}:{mapping['source_verse']}{'.' + mapping['source_subverse'] if mapping['source_subverse'] else ''}. Skipping.")
                            keep_skipped_count += 1
                            continue
                        
                        if len(source_rows) > 1:
                            logger.warning(f"Keep Action: Found multiple ({len(source_rows)}) undealt source texts for mapping ID {mapping['id']} - {mapping['source_tradition']}:{mapping['source_book']}.{mapping['source_chapter']}:{mapping['source_verse']}{'.' + mapping['source_subverse'] if mapping['source_subverse'] else ''}. Processing first one.")
                        
                        source_row = source_rows[0]
                        source_text = source_row['text']
                        source_id = source_row['id']

                        # 2. Insert into standard_table using target refs
                        cur.execute("""
                            INSERT INTO bible.standard_table 
                                (target_tradition, book_id, chapter, verse, subverse, text, mapping_id, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (target_tradition, book_id, chapter, verse, subverse) 
                            DO UPDATE SET text = EXCLUDED.text, mapping_id = EXCLUDED.mapping_id, notes = EXCLUDED.notes;
                         """, (
                            mapping['target_tradition'], mapping['target_book'], mapping['target_chapter'], 
                            mapping['target_verse'], mapping['target_subverse'], source_text,
                            mapping['id'], mapping['notes'] # Use combined notes field
                        ))

                        # 3. Update source_table row to dealt_with = TRUE
                        cur.execute("""
                            UPDATE bible.source_table 
                            SET dealt_with = TRUE 
                            WHERE id = %s;
                        """, (source_id,))
                        keep_processed_count += 1

                    except Exception as e:
                        logger.error(f"Error processing Keep action for mapping ID {mapping.get('id', 'N/A')}: {e}")
                        keep_skipped_count += 1
                        # Decide if we should rollback or continue? For now, log and continue.
                
                logger.info(f"Keep Action: Processed {keep_processed_count} mappings, skipped {keep_skipped_count}.")

            elif action_type == 'Renumber':
                renumber_processed_count = 0
                renumber_skipped_count = 0
                for mapping in mappings_for_action:
                    try:
                        # 1. Query source_table for text using source refs
                        cur.execute("""
                            SELECT text, id FROM bible.source_table 
                            WHERE source_tradition IS NOT DISTINCT FROM %s
                              AND book_id IS NOT DISTINCT FROM %s
                              AND chapter IS NOT DISTINCT FROM %s
                              AND verse IS NOT DISTINCT FROM %s
                              AND COALESCE(subverse, '') IS NOT DISTINCT FROM COALESCE(%s, '')
                              AND dealt_with = FALSE;
                        """, (
                            mapping['source_tradition'], mapping['source_book'], mapping['source_chapter'], 
                            mapping['source_verse'], mapping['source_subverse']
                        ))
                        source_rows = cur.fetchall()

                        if not source_rows:
                            # logger.warning(f"Renumber Action: No undealt source text found for mapping ID {mapping['id']} - {mapping['source_tradition']}:{mapping['source_book']}.{mapping['source_chapter']}:{mapping['source_verse']}{mapping['source_subverse']}. Skipping.")
                            renumber_skipped_count += 1
                            continue
                        
                        if len(source_rows) > 1:
                             logger.warning(f"Renumber Action: Found multiple ({len(source_rows)}) undealt source texts for mapping ID {mapping['id']} - {mapping['source_tradition']}:{mapping['source_book']}.{mapping['source_chapter']}:{mapping['source_verse']}{mapping['source_subverse']}. Processing first one.")
                        
                        source_row = source_rows[0]
                        source_text = source_row['text']
                        source_id = source_row['id']

                        # 2. Insert into standard_table using TARGET refs
                        cur.execute("""
                            INSERT INTO bible.standard_table 
                                (target_tradition, book_id, chapter, verse, subverse, text, mapping_id, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (target_tradition, book_id, chapter, verse, subverse) 
                            DO UPDATE SET text = EXCLUDED.text, mapping_id = EXCLUDED.mapping_id, notes = EXCLUDED.notes;
                         """, (
                            mapping['target_tradition'], mapping['target_book'], mapping['target_chapter'], 
                            mapping['target_verse'], mapping['target_subverse'], source_text,
                            mapping['id'], mapping['notes'] # Use combined notes field
                        ))

                        # 3. Update source_table row to dealt_with = TRUE
                        cur.execute("""
                            UPDATE bible.source_table 
                            SET dealt_with = TRUE 
                            WHERE id = %s;
                        """, (source_id,))
                        renumber_processed_count += 1

                    except Exception as e:
                        logger.error(f"Error processing Renumber action for mapping ID {mapping.get('id', 'N/A')}: {e}")
                        renumber_skipped_count += 1
                
                logger.info(f"Renumber Action: Processed {renumber_processed_count} mappings, skipped {renumber_skipped_count}.")

            elif action_type == 'Merged':
                merged_processed_count = 0
                merged_skipped_count = 0
                # TODO: Implement grouping logic to handle multiple source verses merging into one target.
                # Initial simple approach: Process each mapping row individually.
                for mapping in mappings_for_action:
                    try:
                        # 1. Query source_table for text using source refs
                        cur.execute("""
                            SELECT text, id FROM bible.source_table
                            WHERE source_tradition IS NOT DISTINCT FROM %s
                              AND book_id IS NOT DISTINCT FROM %s
                              AND chapter IS NOT DISTINCT FROM %s
                              AND verse IS NOT DISTINCT FROM %s
                              AND COALESCE(subverse, '') IS NOT DISTINCT FROM COALESCE(%s, '')
                              AND dealt_with = FALSE;
                        """, (
                            mapping['source_tradition'], mapping['source_book'],
                            mapping['source_chapter'], mapping['source_verse'],
                            mapping['source_subverse']
                        ))
                        source_rows = cur.fetchall()

                        if not source_rows:
                            logger.warning(f"Merged Action: No undealt source text found for mapping ID {mapping['id']} (Source: {mapping['source_book']} {mapping['source_chapter']}:{mapping['source_verse']}). Skipping.")
                            merged_skipped_count += 1
                            continue
                        
                        if len(source_rows) > 1:
                             logger.warning(f"Merged Action: Found multiple ({len(source_rows)}) undealt source rows for mapping ID {mapping['id']} ({mapping['source_book']} {mapping['source_chapter']}:{mapping['source_verse']}). Using first row found. Implement grouping logic.")
                             # TODO: This highlights the need for grouping. For now, we just take the first.
                             
                        source_text = source_rows[0]['text']
                        source_id = source_rows[0]['id']

                        # 2. Insert/Update standard_table with target refs, using source text
                        cur.execute("""
                            INSERT INTO bible.standard_table (
                                source_table_id, target_tradition,
                                book_id, chapter, verse, subverse,
                                text, tvtms_mapping_id
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (target_tradition, book_id, chapter, verse, subverse)
                            DO UPDATE SET
                                text = bible.standard_table.text || ' ' || EXCLUDED.text, -- Append text for merges (Needs refinement)
                                source_table_id = EXCLUDED.source_table_id, -- Keep latest source_id for tracking?
                                tvtms_mapping_id = EXCLUDED.tvtms_mapping_id;
                        """, (
                            source_id, mapping['target_tradition'],
                            mapping['target_book'], mapping['target_chapter'],
                            mapping['target_verse'], mapping['target_subverse'],
                            source_text, mapping['id']
                        ))

                        # 3. Mark source row as dealt_with
                        cur.execute("""
                            UPDATE bible.source_table SET dealt_with = TRUE WHERE id = %s;
                        """, (source_id,))
                        merged_processed_count += 1

                    except Exception as e:
                        conn.rollback() # Rollback on error for this specific mapping
                        logger.exception(f"Error processing Merged mapping ID {mapping.get('id', 'N/A')}: {e}")
                        merged_skipped_count += 1
                    else:
                        conn.commit() # Commit after each successful mapping process
                        
                logger.info(f"Merged Action: Processed {merged_processed_count} mappings, skipped {merged_skipped_count} (using simple approach).")

            # TODO: Implement logic for each action type
            # Merged, Renumber, Keep, IfEmpty, Psalm Title, Renumber Title

            logger.info(f"Finished processing action type: {action_type}")

    logger.info("Finished processing all versification actions.")

def fetch_valid_book_ids(conn, parser=None):
    """Fetch valid book IDs from the books table and combine with parser's normalized abbreviations."""
    book_ids = set()
    
    # Fetch from database
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""
            SELECT book_id FROM bible.books;
        """)
        db_book_ids = [row['book_id'] for row in cur.fetchall()]
        book_ids.update(db_book_ids)
    
    # Add normalized abbreviations from parser if provided
    if parser:
        # Get all valid book IDs from the parser's normalization dictionary
        standard_books = {
            'gen': 'gen', 'exod': 'exod', 'exo': 'exod', 'lev': 'lev', 'num': 'num', 'deut': 'deut', 'deu': 'deut',
            'josh': 'josh', 'jos': 'josh', 'judg': 'judg', 'jdg': 'judg', 'ruth': 'ruth', 'rut': 'ruth',
            '1sam': '1sam', '1sa': '1sam', '2sam': '2sam', '2sa': '2sam',
            '1kgs': '1kgs', '1ki': '1kgs', '2kgs': '2kgs', '2ki': '2kgs',
            '1chr': '1chr', '1ch': '1chr', '2chr': '2chr', '2ch': '2chr',
            'ezra': 'ezra', 'ezr': 'ezra', 'neh': 'neh', 'est': 'est', 'esth': 'est',
            'job': 'job', 'jb': 'job', 'ps': 'ps', 'psa': 'ps', 'psalm': 'ps', 'psalms': 'ps',
            'prov': 'prov', 'pro': 'prov', 'prv': 'prov', 'eccl': 'eccl', 'ecc': 'eccl', 'song': 'song', 'sng': 'song', 'sos': 'song',
            'isa': 'isa', 'is': 'isa', 'jer': 'jer', 'lam': 'lam', 'ezek': 'ezek', 'ezk': 'ezek', 'eze': 'ezek',
            'dan': 'dan', 'hos': 'hos', 'joel': 'joel', 'jol': 'joel', 'amos': 'amos', 'amo': 'amos', 'obad': 'obad', 'oba': 'obad',
            'jonah': 'jonah', 'jon': 'jonah', 'mic': 'mic', 'nah': 'nah', 'nam': 'nah', 'hab': 'hab', 'zeph': 'zeph', 'zep': 'zeph',
            'hag': 'hag', 'zech': 'zech', 'zec': 'zech', 'mal': 'mal',
            'matt': 'matt', 'mat': 'matt', 'mrk': 'mark', 'mark': 'mark', 'mar': 'mark', 'mk': 'mark',
            'luke': 'luke', 'luk': 'luke', 'lk': 'luke', 'john': 'john', 'jhn': 'john', 'jn': 'john',
            'acts': 'acts', 'act': 'acts', 'rom': 'rom', 'ro': 'rom',
            '1cor': '1cor', '1co': '1cor', '2cor': '2cor', '2co': '2cor',
            'gal': 'gal', 'eph': 'eph', 'phil': 'phil', 'php': 'phil',
            'col': 'col', '1thess': '1thess', '1th': '1thess', '2thess': '2thess', '2th': '2thess',
            '1tim': '1tim', '1ti': '1tim', '2tim': '2tim', '2ti': '2tim',
            'titus': 'titus', 'tit': 'titus', 'phlm': 'phlm', 'phm': 'phlm',
            'heb': 'heb', 'jas': 'jas', 'jam': 'jas',
            '1pet': '1pet', '1pe': '1pet', '2pet': '2pet', '2pe': '2pet',
            '1john': '1john', '1jn': '1john', '2john': '2john', '2jn': '2john', '3john': '3john', '3jn': '3john',
            'jude': 'jude', 'jud': 'jude', 'rev': 'rev', 're': 'rev',
            
            # Deuterocanonical/Apocryphal books
            'tob': 'tob', 'tobit': 'tob', 'jdt': 'jdt', 'judith': 'jdt',
            'wis': 'wis', 'wisdom': 'wis', 'wisd': 'wis', 'wisdom of solomon': 'wis',
            'sir': 'sir', 'sirach': 'sir', 'ecclesiasticus': 'sir', 'ecclus': 'sir', 
            'bar': 'bar', 'baruch': 'bar',
            '1ma': '1ma', '1mac': '1ma', '1macc': '1ma', '1maccabees': '1ma',
            '2ma': '2ma', '2mac': '2ma', '2macc': '2ma', '2maccabees': '2ma',
            '3ma': '3ma', '3mac': '3ma', '3macc': '3ma', '3maccabees': '3ma',
            '4ma': '4ma', '4mac': '4ma', '4macc': '4ma', '4maccabees': '4ma',
            '1es': '1es', '1esd': '1es', '1esdras': '1es',
            '2es': '2es', '2esd': '2es', '2esdras': '2es',
            '4es': '4es', '4esd': '4es', '4esdras': '4es',
            'man': 'man', 'pray man': 'man', 'prayer of manasseh': 'man'
        }
        
        # Add both the keys and values to our valid book IDs set
        book_ids.update(standard_books.keys())
        book_ids.update(standard_books.values())
    
    return list(book_ids)

def main():
    """Main function to orchestrate the ETL process."""
    setup_logging()
    logger.info("Starting TVTMS ETL process")
    
    try:
        # Use the correct default file path
        file_path = os.environ.get('TVTMS_FILE_PATH', 'data/raw/TVTMS_expanded.txt')
        # Create the parser once and reuse it
        parser = TVTMSParser()
        # Correctly handle the returned list of mappings
        validated_mappings = process_tvtms_file(file_path, parser) # Changed variable name
        logger.info(f"Processor returned {len(validated_mappings)} validated mappings") # Updated log

        # --- ADD CHECK FOR EMPTY LIST --- 
        if not validated_mappings:
            logger.error("No mappings returned from process_tvtms_file. Exiting.")
            sys.exit(0) # Exit gracefully, as the reason was logged earlier
        # --- END CHECK ---

        # --- Fetch valid book IDs and filter mappings ---
        conn = None
        try:
            conn = get_db_connection()
            if conn:
                # Fetch database book IDs to get the proper case format
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("SELECT book_id FROM bible.books")
                    db_book_ids = {row['book_id'] for row in cur.fetchall()}
                    # Also create a lowercase to proper case mapping
                    book_id_case_map = {book_id.lower(): book_id for book_id in db_book_ids}
                
                # Pass the parser to get expanded book IDs
                valid_book_ids = fetch_valid_book_ids(conn, parser)
                # Convert to lowercase for case-insensitive matching
                valid_book_ids_lower = [book_id.lower() for book_id in valid_book_ids]
                
                db_ready_mappings = []
                filtered_mappings_details = []
                for m in validated_mappings:
                    # Convert book IDs to lowercase for comparison
                    source_book_lower = m.source_book.lower() if m.source_book else None
                    target_book_lower = m.target_book.lower() if m.target_book else None
                    
                    if (
                        target_book_lower in valid_book_ids_lower and
                        source_book_lower in valid_book_ids_lower and
                        m.target_chapter is not None and
                        m.target_verse is not None
                    ):
                        # Standardize book IDs to match database case format
                        if source_book_lower in book_id_case_map:
                            m.source_book = book_id_case_map[source_book_lower]
                        if target_book_lower in book_id_case_map:
                            m.target_book = book_id_case_map[target_book_lower]
                        
                        db_ready_mappings.append(m)
                    else:
                        filtered_mappings_details.append(m)
                filtered_count = len(filtered_mappings_details)
                if filtered_count > 0:
                    logger.warning(f"Filtered out {filtered_count} mappings with invalid or missing book IDs (source or target) or required TARGET fields (chapter, verse).")
                    for i, fm in enumerate(filtered_mappings_details[:15]):
                        logger.warning(f"  Filtered Mapping Detail [{i+1}/{filtered_count}]: {fm}")
                create_tables(conn) # Ensure tables exist
                truncate_versification_mappings(conn)
                db_store_mappings(conn, db_ready_mappings) # Pass filtered list
                logger.info("Successfully stored mappings in database")
                process_actions(conn)
                conn.commit() # Commit transaction after all operations
            else:
                logger.error("Failed to create database connection.")
        except Exception as e:
            logger.error(f"Error storing mappings in database: {e}")
            if conn:
                conn.rollback() # Rollback on error
            raise e # Propagate error to stop execution
        finally:
            if conn:
                conn.close()
                logger.debug("Database connection closed.")

    except Exception as e:
        logger.error(f"ETL process failed: {e}")
        sys.exit(1) # Exit with error code

    logger.info("TVTMS ETL process completed successfully")

if __name__ == '__main__':
    main() 