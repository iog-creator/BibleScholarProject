#!/usr/bin/env python3
"""
Fast TVTMS Processor

This script processes TVTMS data using direct multiprocessing with visible CPU usage.
It focuses on performance and shows progress in real-time and can optionally store
the processed mappings directly in the database.
"""

import os
import sys
import time
import re
import json
import traceback
import multiprocessing
from multiprocessing import Pool, cpu_count
import pandas as pd
from tqdm import tqdm
import argparse

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tvtms.models import Mapping
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure paths
TVTMS_PATH = os.path.abspath('data/raw/TVTMS_expanded.txt')
OUTPUT_PATH = os.path.abspath('data/processed/tvtms_mappings.json')
ERROR_PATH = os.path.abspath('data/processed/tvtms_processing_errors.json')

# Get CPU info
PHYSICAL_CORES = 24  # From user input
LOGICAL_CORES = 8    # From user input
DEFAULT_WORKERS = max(int(PHYSICAL_CORES * 0.75), 1)  # Use 75% of physical cores for better visibility

def parse_tvtms_file(file_path, num_workers):
    """
    Parse the TVTMS file starting at the #DataStart(Expanded) marker.
    Uses pandas for efficiency.
    """
    print(f"System has {PHYSICAL_CORES} physical cores and {LOGICAL_CORES} logical processors")
    print(f"Using {num_workers} worker processes for processing")
    print(f"Reading file: {file_path}")
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find data section
    start_marker = '#DataStart(Expanded)'
    end_marker = '#DataEnd(Expanded)'
    
    # Find start index
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith(start_marker):
            start_idx = i + 1
            break
    
    if start_idx is None:
        raise ValueError("Could not find start marker in TVTMS file")
    
    # Find header line (first non-empty line after start marker)
    header_idx = None
    for i in range(start_idx, len(lines)):
        if lines[i].strip() and not lines[i].strip().startswith("'="):
            header_idx = i
            break
    
    if header_idx is None:
        raise ValueError("Could not find header line in TVTMS file")
    
    # Parse header
    header = [h.strip() for h in lines[header_idx].split('\t')]
    print(f"Found header with {len(header)} columns")
    
    # Find end index
    end_idx = None
    for i in range(header_idx + 1, len(lines)):
        if lines[i].strip().startswith(end_marker):
            end_idx = i
            break
    
    if end_idx is None:
        end_idx = len(lines)
    
    # Extract data lines
    data_lines = lines[header_idx+1:end_idx]
    data_lines = [line for line in data_lines if line.strip() and not line.strip().startswith("'=")]
    
    print(f"Found {len(data_lines)} data lines to process")
    
    # Create unique column names (some may be empty)
    unique_header = []
    seen = {}
    for col in header:
        if col in seen:
            seen[col] += 1
            unique_header.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            unique_header.append(col)
    
    # Parse with pandas for speed
    from io import StringIO
    data_text = ''.join(data_lines)
    df = pd.read_csv(StringIO(data_text), sep='\t', names=unique_header, dtype=str)
    
    # Convert to records for processing
    records = df.to_dict('records')
    print(f"Parsed {len(records)} records in {time.time() - start_time:.2f} seconds")
    
    return records

def process_chunk(chunk_data):
    """Process a chunk of TVTMS records"""
    chunk_id, rows = chunk_data
    mappings = []
    errors = []
    
    for row_idx, row in enumerate(rows):
        try:
            # Extract fields with safe handling
            source_type = row.get('SourceType', '').strip() if isinstance(row.get('SourceType'), str) else ''
            source_ref = row.get('SourceRef', '').strip() if isinstance(row.get('SourceRef'), str) else ''
            standard_ref = row.get('StandardRef', '').strip() if isinstance(row.get('StandardRef'), str) else ''
            action = row.get('Action', '').strip() if isinstance(row.get('Action'), str) else ''
            note_marker = row.get('NoteMarker', '').strip() if isinstance(row.get('NoteMarker'), str) else ''
            
            note_a_key = 'Reversification Note' if 'Reversification Note' in row else 'Note A'
            note_a = row.get(note_a_key, '').strip() if isinstance(row.get(note_a_key), str) else ''
            
            note_b_key = 'Versification Note' if 'Versification Note' in row else 'Note B'
            note_b = row.get(note_b_key, '').strip() if isinstance(row.get(note_b_key), str) else ''
            
            ancient_versions = row.get('Ancient Versions', '').strip() if isinstance(row.get('Ancient Versions'), str) else ''
            
            # Skip rows with no source or target reference or action
            if not source_ref or not standard_ref or not action:
                continue
            
            # Parse source reference (Book.Chapter:Verse)
            source_book, source_chapter, source_verse = None, None, None
            source_subverse = None
            if '.' in source_ref and ':' in source_ref:
                parts = source_ref.split('.')
                source_book = parts[0]
                chapter_verse = parts[1].split(':')
                source_chapter = chapter_verse[0]
                source_verse_part = chapter_verse[1]
                
                # Handle subverses with ! or letter suffix
                if '!' in source_verse_part:
                    # Format like "25!a" - extract the main verse number and subverse marker
                    subverse_match = re.match(r'(\d+)!([a-zA-Z0-9]+)', source_verse_part)
                    if subverse_match:
                        source_verse = subverse_match.group(1)
                        source_subverse = subverse_match.group(2)
                    else:
                        # If pattern doesn't match, just keep numeric part
                        source_verse = re.sub(r'[^0-9]', '', source_verse_part)
                        if not source_verse:
                            source_verse = "1"  # Default to 1 if no digits found
                        errors.append({
                            'type': 'malformed_subverse',
                            'row_idx': row_idx,
                            'source_ref': source_ref,
                            'original': source_verse_part,
                            'cleaned': source_verse,
                            'message': f"Malformed subverse notation in {source_ref}, extracted main verse '{source_verse}'"
                        })
                # Handle other special characters in verse number
                elif not source_verse_part.isdigit() and any(c in source_verse_part for c in '*abcABC'):
                    orig_verse = source_verse_part
                    # Try to extract subverse information
                    letter_match = re.match(r'(\d+)([a-zA-Z])', source_verse_part)
                    if letter_match:
                        source_verse = letter_match.group(1)
                        source_subverse = letter_match.group(2)
                    else:
                        # If no pattern match, just keep numeric part
                        source_verse = re.sub(r'[^0-9]', '', source_verse_part)
                        if not source_verse:
                            source_verse = "1"  # Default to 1 if no digits found
                    
                    if orig_verse != source_verse:
                        errors.append({
                            'type': 'non_numeric_verse',
                            'row_idx': row_idx,
                            'source_ref': source_ref,
                            'original': orig_verse,
                            'cleaned': source_verse,
                            'subverse': source_subverse,
                            'message': f"Non-numeric verse '{orig_verse}' in {source_ref}, extracted main verse '{source_verse}' and subverse '{source_subverse}'"
                        })
                else:
                    source_verse = source_verse_part
            
            # Parse target reference
            target_book, target_chapter, target_verse = None, None, None
            target_subverse = None
            if '.' in standard_ref and ':' in standard_ref:
                parts = standard_ref.split('.')
                target_book = parts[0]
                chapter_verse = parts[1].split(':')
                target_chapter = chapter_verse[0]
                target_verse_part = chapter_verse[1]
                
                # Handle subverses with ! or letter suffix
                if '!' in target_verse_part:
                    # Format like "25!a" - extract the main verse number and subverse marker
                    subverse_match = re.match(r'(\d+)!([a-zA-Z0-9]+)', target_verse_part)
                    if subverse_match:
                        target_verse = subverse_match.group(1)
                        target_subverse = subverse_match.group(2)
                    else:
                        # If pattern doesn't match, just keep numeric part
                        target_verse = re.sub(r'[^0-9]', '', target_verse_part)
                        if not target_verse:
                            target_verse = "1"  # Default to 1 if no digits found
                        errors.append({
                            'type': 'malformed_subverse',
                            'row_idx': row_idx,
                            'target_ref': standard_ref,
                            'original': target_verse_part,
                            'cleaned': target_verse,
                            'message': f"Malformed subverse notation in {standard_ref}, extracted main verse '{target_verse}'"
                        })
                # Handle other special characters in verse number
                elif not target_verse_part.isdigit() and any(c in target_verse_part for c in '*abcABC'):
                    orig_verse = target_verse_part
                    # Try to extract subverse information
                    letter_match = re.match(r'(\d+)([a-zA-Z])', target_verse_part)
                    if letter_match:
                        target_verse = letter_match.group(1)
                        target_subverse = letter_match.group(2)
                    else:
                        # If no pattern match, just keep numeric part
                        target_verse = re.sub(r'[^0-9]', '', target_verse_part)
                        if not target_verse:
                            target_verse = "1"  # Default to 1 if no digits found
                    
                    if orig_verse != target_verse:
                        errors.append({
                            'type': 'non_numeric_verse',
                            'row_idx': row_idx,
                            'target_ref': standard_ref,
                            'original': orig_verse,
                            'cleaned': target_verse,
                            'subverse': target_subverse,
                            'message': f"Non-numeric verse '{orig_verse}' in {standard_ref}, extracted main verse '{target_verse}' and subverse '{target_subverse}'"
                        })
                else:
                    target_verse = target_verse_part
            
            # Normalize mapping type
            mapping_type_map = {
                'Keep verse': 'standard',
                'Renumber verse': 'renumber',
                'Renumber title': 'renumber',
                'MergedPrev verse': 'merge_prev',
                'MergedNext verse': 'merge_next',
                'IfEmpty verse': 'conditional',
                'SubdividedVerse': 'split',
                'LongVerse': 'absent',
                'LongVerseElsewhere': 'absent',
                'LongVerseDuplicated': 'absent',
                'TextMayBeMissing': 'missing',
                'StartDifferent': 'renumber',
                'Psalm Title': 'special',
                'Empty verse': 'missing',
                'Missing verse': 'missing'
            }
            mapping_type = mapping_type_map.get(action, 'standard')
            
            # Normalize category
            category_map = {
                'Opt': 'Opt',
                'Opt.': 'Opt',
                'Optional': 'Opt',
                'Nec': 'Nec',
                'Nec.': 'Nec',
                'Necessary': 'Nec',
                'Acd': 'Acd',
                'Acd.': 'Acd',
                'Academic': 'Acd',
                'Inf': 'Inf',
                'Inf.': 'Inf',
                'Informational': 'Inf',
                'None': 'None',
                '': 'None'
            }
            normalized_category = category_map.get(note_marker, 'None')
            
            # Create mapping object for database compatibility
            mapping = Mapping(
                source_tradition=source_type.lower(),
                target_tradition='standard',
                source_book=source_book,
                source_chapter=source_chapter,
                source_verse=source_verse,
                source_subverse=source_subverse,
                manuscript_marker=None,
                target_book=target_book,
                target_chapter=target_chapter,
                target_verse=target_verse,
                target_subverse=target_subverse,
                mapping_type=mapping_type,
                category=normalized_category,
                notes=f"{note_a} {note_b}".strip(),
                source_range_note=None,
                target_range_note=None,
                note_marker=note_marker,
                ancient_versions=ancient_versions
            )
            mappings.append(mapping)
            
        except Exception as e:
            # Record error with details
            errors.append({
                'type': 'exception',
                'row_idx': row_idx,
                'error': str(e),
                'row_data': str(row),
                'traceback': traceback.format_exc(),
                'message': f"Exception processing row {row_idx}: {str(e)}"
            })
    
    return chunk_id, mappings, errors

def extract_section_mappings(file_path, num_workers):
    """Extract and process section mappings ($ prefixed lines)"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Filter lines starting with $
    section_lines = [line.strip() for line in lines if line.strip().startswith('$')]
    print(f"Found {len(section_lines)} section mapping lines to process")
    
    # Process in parallel
    chunks = []
    chunk_size = max(len(section_lines) // num_workers, 1)
    for i in range(0, len(section_lines), chunk_size):
        chunk_data = (i // chunk_size, section_lines[i:i+chunk_size])
        chunks.append(chunk_data)
    
    with Pool(processes=num_workers) as pool:
        section_results = list(tqdm(
            pool.imap_unordered(process_section_chunk, chunks),
            total=len(chunks),
            desc="Processing section mappings"
        ))
    
    # Combine results
    section_mappings = []
    section_errors = []
    for _, mappings, errors in section_results:
        section_mappings.extend(mappings)
        section_errors.extend(errors)
    
    print(f"Processed {len(section_mappings)} section mappings in {time.time() - start_time:.2f} seconds")
    return section_mappings, section_errors

def process_section_chunk(chunk_data):
    """Process a chunk of section mapping lines"""
    chunk_id, lines = chunk_data
    mappings = []
    errors = []
    
    for line_idx, line in enumerate(lines):
        try:
            # Format: $Gen.2:24--3:1    English KJV     Hebrew  Latin   Greek ...
            parts = line.split('\t')
            if len(parts) < 2:
                parts = line.split('    ')
            
            if len(parts) < 2:
                errors.append({
                    'type': 'parse_error',
                    'line_idx': line_idx,
                    'line': line,
                    'message': f"Line {line_idx}: Could not parse tabs or spaces in line: {line[:50]}..."
                })
                continue
            
            ref_range = parts[0].lstrip('$').strip()
            traditions = [part.strip() for part in parts[1:] if part.strip()]
            
            # Skip complex references for this fast version
            if '/' in ref_range:
                continue
            
            # Handle range formats
            start_ref, end_ref = None, None
            
            if '--' in ref_range:
                # Format like "Gen.2:24--3:1"
                start_ref, end_ref = ref_range.split('--', 1)
            elif '-' in ref_range:
                # Format like "Gen.2:24-3:1"
                start_ref, end_ref = ref_range.split('-', 1)
            else:
                # Simple reference
                start_ref = end_ref = ref_range
            
            # Skip if couldn't parse
            if not start_ref or not end_ref:
                errors.append({
                    'type': 'reference_parse_error',
                    'line_idx': line_idx,
                    'line': line,
                    'ref_range': ref_range,
                    'message': f"Line {line_idx}: Could not parse start and end references from: {ref_range}"
                })
                continue
                
            # Convert to standard format if needed
            if '.' not in end_ref and '.' in start_ref:
                book_name = start_ref.split('.')[0]
                end_ref = f"{book_name}.{end_ref}"
            
            # Parse start reference
            start_book, start_chapter, start_verse, start_subverse = None, None, None, None
            if '.' in start_ref and ':' in start_ref:
                start_parts = start_ref.split('.')
                start_book = start_parts[0]
                
                # Parse chapter:verse
                chapter_verse = start_parts[1].split(':')
                if len(chapter_verse) == 2:
                    start_chapter = chapter_verse[0]
                    start_verse_part = chapter_verse[1]
                    
                    # Handle subverses and special characters
                    if '!' in start_verse_part:
                        # Extract main verse and subverse
                        match = re.match(r'(\d+)!([a-zA-Z0-9]+)', start_verse_part)
                        if match:
                            start_verse = match.group(1)
                            start_subverse = match.group(2)
                        else:
                            # Fall back to numeric only
                            start_verse = re.sub(r'[^0-9]', '', start_verse_part)
                    elif not start_verse_part.isdigit() and any(c in start_verse_part for c in '*abcABC'):
                        # Try to extract letter suffixes
                        match = re.match(r'(\d+)([a-zA-Z])', start_verse_part)
                        if match:
                            start_verse = match.group(1)
                            start_subverse = match.group(2)
                        else:
                            # Fall back to numeric only
                            start_verse = re.sub(r'[^0-9]', '', start_verse_part)
                    else:
                        start_verse = start_verse_part
            
            # Parse end reference
            end_book, end_chapter, end_verse, end_subverse = None, None, None, None
            if '.' in end_ref and ':' in end_ref:
                end_parts = end_ref.split('.')
                end_book = end_parts[0]
                
                # Parse chapter:verse
                chapter_verse = end_parts[1].split(':')
                if len(chapter_verse) == 2:
                    end_chapter = chapter_verse[0]
                    end_verse_part = chapter_verse[1]
                    
                    # Handle subverses and special characters
                    if '!' in end_verse_part:
                        # Extract main verse and subverse
                        match = re.match(r'(\d+)!([a-zA-Z0-9]+)', end_verse_part)
                        if match:
                            end_verse = match.group(1)
                            end_subverse = match.group(2)
                        else:
                            # Fall back to numeric only
                            end_verse = re.sub(r'[^0-9]', '', end_verse_part)
                    elif not end_verse_part.isdigit() and any(c in end_verse_part for c in '*abcABC'):
                        # Try to extract letter suffixes
                        match = re.match(r'(\d+)([a-zA-Z])', end_verse_part)
                        if match:
                            end_verse = match.group(1)
                            end_subverse = match.group(2)
                        else:
                            # Fall back to numeric only
                            end_verse = re.sub(r'[^0-9]', '', end_verse_part)
                    else:
                        end_verse = end_verse_part
            
            if start_book:
                # Process each valid tradition
                for tradition in traditions:
                    # Skip known invalid traditions
                    if tradition.lower() in ['english', 'english1', 'english2', 'english-kjv']:
                        continue
                        
                    # Create mapping object for start reference
                    start_mapping = Mapping(
                        source_tradition=tradition.lower(),
                        target_tradition='standard',
                        source_book=start_book,
                        source_chapter=start_chapter,
                        source_verse=start_verse,
                        source_subverse=start_subverse,
                        manuscript_marker=None,
                        target_book=start_book,
                        target_chapter=start_chapter,
                        target_verse=start_verse,
                        target_subverse=start_subverse,
                        mapping_type='range_start',
                        category='None',
                        notes=f"Range start: {ref_range}",
                        source_range_note=ref_range,
                        target_range_note=ref_range,
                        note_marker=None,
                        ancient_versions=None
                    )
                    mappings.append(start_mapping)
                    
                    # If there's an end reference different from start, create mapping for it too
                    if end_ref != start_ref:
                        end_mapping = Mapping(
                            source_tradition=tradition.lower(),
                            target_tradition='standard',
                            source_book=end_book or start_book,
                            source_chapter=end_chapter,
                            source_verse=end_verse,
                            source_subverse=end_subverse,
                            manuscript_marker=None,
                            target_book=end_book or start_book,
                            target_chapter=end_chapter,
                            target_verse=end_verse,
                            target_subverse=end_subverse,
                            mapping_type='range_end',
                            category='None',
                            notes=f"Range end: {ref_range}",
                            source_range_note=ref_range,
                            target_range_note=ref_range,
                            note_marker=None,
                            ancient_versions=None
                        )
                        mappings.append(end_mapping)
            
        except Exception as e:
            errors.append({
                'type': 'exception',
                'line_idx': line_idx,
                'line': line,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'message': f"Exception processing section line {line_idx}: {str(e)}"
            })
    
    return chunk_id, mappings, errors

def store_in_database(mappings):
    """Store the processed mappings in the database"""
    start_time = time.time()
    print(f"Storing {len(mappings)} mappings in the database...")
    
    try:
        # Calculate optimal batch size based on number of mappings
        if len(mappings) > 10000:
            batch_size = 2000  # Very large batch size for >10k mappings
        elif len(mappings) > 5000:
            batch_size = 1000  # Large batch size for >5k mappings
        else:
            batch_size = 500   # Moderate batch size for smaller datasets
        
        print(f"Using batch size of {batch_size} for {len(mappings)} mappings")
        
        # Use custom batch processing with larger batch sizes
        from sqlalchemy import create_engine, text
        from src.database.connection import get_connection_string
        import psycopg2.extras
        
        # Create engine with better connection pool settings
        engine = create_engine(
            get_connection_string(),
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            connect_args={"application_name": "fast_tvtms_processor_batch_insert"}
        )
        
        # Convert mappings to dictionaries for batch insertion
        mappings_dicts = []
        range_skipped = 0
        
        for mapping in mappings:
            mapping_dict = mapping.to_dict()
            
            # Validate source_verse and target_verse for integer compatibility
            # These must be integers for the database schema
            if isinstance(mapping_dict['source_verse'], str) and '-' in mapping_dict['source_verse']:
                # This is a verse range, extract the first number
                try:
                    mapping_dict['source_verse'] = mapping_dict['source_verse'].split('-')[0]
                    mapping_dict['source_range_note'] = f"Range in original: {mapping_dict['source_verse']}"
                except Exception:
                    # Skip this mapping if we can't fix it
                    range_skipped += 1
                    continue
            
            if isinstance(mapping_dict['target_verse'], str) and '-' in mapping_dict['target_verse']:
                # This is a verse range, extract the first number
                try:
                    original_range = mapping_dict['target_verse']
                    mapping_dict['target_verse'] = original_range.split('-')[0]
                    mapping_dict['target_range_note'] = f"Range in original: {original_range}"
                except Exception:
                    # Skip this mapping if we can't fix it
                    range_skipped += 1
                    continue
            
            # Final integer validation - ensure verses are integers
            try:
                # Use int() to validate but keep as string for insertion
                if mapping_dict['source_verse']:
                    int(mapping_dict['source_verse'])
                if mapping_dict['target_verse']:
                    int(mapping_dict['target_verse'])
                
                # If we get here, validation passed
                mappings_dicts.append(mapping_dict)
            except (ValueError, TypeError):
                # Skip mappings with non-integer verse values
                range_skipped += 1
                continue
        
        if range_skipped > 0:
            print(f"⚠️ Skipped {range_skipped} mappings with invalid verse ranges")
        
        print(f"Validated {len(mappings_dicts)} mappings for database insertion")
        
        # Clear existing mappings first
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM bible.versification_mappings"))
            conn.commit()
            print("Cleared existing mappings")
        
        # Insert in batches with progress display
        total_batches = (len(mappings_dicts) + batch_size - 1) // batch_size
        batches_processed = 0
        rows_inserted = 0
        
        for i in range(0, len(mappings_dicts), batch_size):
            batch = mappings_dicts[i:i+batch_size]
            if not batch:
                continue
                
            batch_start_time = time.time()
            
            with engine.connect() as conn:
                # Get column names from the first mapping
                columns = list(batch[0].keys())
                
                # Build optimized insert query with explicit column list
                columns_str = ", ".join(columns)
                placeholders = ", ".join([f":{col}" for col in columns])
                query = f"INSERT INTO bible.versification_mappings ({columns_str}) VALUES ({placeholders})"
                
                # Execute batch insert
                result = conn.execute(text(query), batch)
                conn.commit()
                
                rows_inserted += result.rowcount
                batches_processed += 1
                batch_duration = time.time() - batch_start_time
                
                # Progress report
                print(f"Batch {batches_processed}/{total_batches}: Inserted {result.rowcount} rows in {batch_duration:.2f} seconds ({result.rowcount/batch_duration:.1f} rows/sec)")
        
        # Final stats
        total_duration = time.time() - start_time
        print(f"Successfully stored {rows_inserted} mappings in {total_duration:.2f} seconds ({rows_inserted/total_duration:.1f} rows/sec average)")
        return rows_inserted
    except Exception as e:
        print(f"Error storing mappings in database: {str(e)}")
        traceback.print_exc()
        return 0

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fast TVTMS Processor with parallel processing")
    parser.add_argument("--file", type=str, default=TVTMS_PATH, help="Path to the TVTMS file")
    parser.add_argument("--output", type=str, default=OUTPUT_PATH, help="Path to save the processed mappings")
    parser.add_argument("--errors", type=str, default=ERROR_PATH, help="Path to save the error report")
    parser.add_argument("--database", action="store_true", help="Store mappings in the database")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Number of worker processes to use")
    args = parser.parse_args()
    
    # Get the number of workers from args
    num_workers = args.workers
    
    start_time = time.time()
    print(f"Starting Fast TVTMS Processor at {time.strftime('%H:%M:%S')}")
    
    try:
        # Parse TVTMS file
        rows = parse_tvtms_file(args.file, num_workers)
        
        # Process in parallel chunks
        chunks = []
        chunk_size = max(len(rows) // num_workers, 1)
        for i in range(0, len(rows), chunk_size):
            chunk_data = (i // chunk_size, rows[i:i+chunk_size])
            chunks.append(chunk_data)
        
        print(f"Processing data in {len(chunks)} chunks with {num_workers} workers")
        
        all_errors = []
        with Pool(processes=num_workers) as pool:
            results = list(tqdm(
                pool.imap_unordered(process_chunk, chunks),
                total=len(chunks),
                desc="Processing TVTMS data"
            ))
        
        # Combine results and collect errors
        mappings = []
        for chunk_id, chunk_mappings, chunk_errors in results:
            mappings.extend(chunk_mappings)
            if chunk_errors:
                all_errors.extend(chunk_errors)
        
        print(f"Processed {len(mappings)} mappings")
        
        # Process section mappings
        section_mappings = []
        section_errors = []
        try:
            section_mappings, section_errors = extract_section_mappings(args.file, num_workers)
            all_errors.extend(section_errors)
        except Exception as e:
            print(f"Error processing section mappings: {str(e)}")
            traceback.print_exc()
        
        # Combine all mappings
        all_mappings = mappings + section_mappings
        print(f"Total combined mappings: {len(all_mappings)}")
        
        # Save results
        with open(args.output, 'w', encoding='utf-8') as f:
            # Convert Mapping objects to dictionaries for JSON serialization
            mappings_dict = [m.to_dict() for m in all_mappings]
            json.dump(mappings_dict, f, indent=2)
        
        print(f"Saved output to {args.output}")
        
        # Check if we have errors to report
        if all_errors:
            print(f"⚠️ Found {len(all_errors)} errors during processing")
            print(f"Writing detailed error report to {args.errors}")
            
            with open(args.errors, 'w', encoding='utf-8') as f:
                json.dump(all_errors, f, indent=2)
                
            # Print summary of error types
            error_types = {}
            for error in all_errors:
                error_type = error.get('type', 'unknown')
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
            print("Error summary by type:")
            for error_type, count in error_types.items():
                print(f"  - {error_type}: {count} occurrences")
                
            # Print a few examples of each error type
            print("\nError examples:")
            examples_shown = set()
            for error in all_errors:
                error_type = error.get('type', 'unknown')
                if error_type not in examples_shown and len(examples_shown) < 5:
                    examples_shown.add(error_type)
                    print(f"  Example of '{error_type}': {error.get('message', 'No message')}")
        
        # Store in database if requested
        if args.database:
            db_count = store_in_database(all_mappings)
            if db_count:
                print(f"Successfully stored {db_count} mappings in the database")
            else:
                print("Failed to store mappings in the database")
        
        print(f"Total processing time: {time.time() - start_time:.2f} seconds")
        
        # If there were errors, exit with error code
        if all_errors:
            print("Processing completed with errors. Check the error report for details.")
            return 1
        
    except Exception as e:
        print(f"Error in processing: {str(e)}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 