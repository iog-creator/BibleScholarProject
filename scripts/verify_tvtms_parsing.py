#!/usr/bin/env python3
"""
TVTMS Verification Script

This script verifies that the TVTMS file from the secondary source can be properly parsed,
starting at line 3802 with the #DataStart(Expanded) marker.
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Path to the secondary TVTMS file
SECONDARY_TVTMS_PATH = os.path.abspath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    '../STEPBible-Datav2/STEPBible-Data/TVTMS - Translators Versification Traditions with Methodology for Standardisation for Eng+Heb+Lat+Grk+Others - STEPBible.org CC BY.txt'
))

# Path to save parsed data as JSONL for DSPy training
DSPY_TRAINING_PATH = os.path.abspath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    'data/processed/dspy_training_data/tvtms_parsing_examples.jsonl'
))

def parse_tvtms_file(file_path):
    """
    Parse the TVTMS file starting at the #DataStart(Expanded) marker.
    
    Args:
        file_path: Path to the TVTMS file
        
    Returns:
        Tuple of (data_rows, issue_rows)
    """
    start_marker = '#DataStart(Expanded)'
    end_marker = '#DataEnd(Expanded)'
    header = None
    data_started = False
    data_ended = False
    rows = []
    issues = []
    
    logger.info(f"Reading TVTMS file: {file_path}")
    with open(file_path, encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip('\n')
            
            # Check for start marker
            if not data_started:
                if line.startswith(start_marker):
                    data_started = True
                    logger.info(f"Found start marker at line {line_num}")
                    continue
                continue
                
            # Check for end marker
            if data_ended or line.startswith(end_marker):
                if not data_ended:
                    logger.info(f"Found end marker at line {line_num}")
                    data_ended = True
                continue
                
            # Skip empty lines or comment lines
            if line.strip() == '' or line.startswith("'="):
                continue
                
            # Once data starts, the first non-empty line is the header
            if header is None:
                header = [h.strip() for h in line.split('\t')]
                logger.info(f"Found header: {header}")
                continue
                
            # Parse each line as tab-separated
            fields = line.split('\t')
            
            # Handle mismatch between fields and header
            if len(fields) != len(header):
                issue = {
                    'line_num': line_num,
                    'line': line,
                    'reason': f'Field count mismatch: Expected {len(header)}, got {len(fields)}',
                    'header': header
                }
                issues.append(issue)
                continue
                
            # Create row dictionary with header->value mapping
            row = dict(zip(header, fields))
            rows.append(row)
            
            # For DSPy training, also capture example successful parses 
            if len(rows) % 1000 == 0:
                logger.info(f"Processed {len(rows)} rows")
    
    logger.info(f"Finished parsing TVTMS file. Found {len(rows)} valid rows and {len(issues)} issues.")
    return rows, issues

def save_dspy_training_data(rows, issues):
    """
    Save parsed rows and issues as JSONL for DSPy training.
    
    Args:
        rows: List of successfully parsed rows
        issues: List of parsing issues
    """
    os.makedirs(os.path.dirname(DSPY_TRAINING_PATH), exist_ok=True)
    
    # Create training examples from successful and failed parses
    training_examples = []
    
    # Add some examples of successful parses
    for i, row in enumerate(rows):
        if i % 1000 == 0 and i < 5000:  # Just take a few samples
            example = {
                'type': 'successful_parse',
                'data': row,
                'metadata': {
                    'example_number': i,
                    'parser': 'verify_tvtms_parsing.py'
                }
            }
            training_examples.append(example)
    
    # Add all examples of parsing issues
    for issue in issues:
        example = {
            'type': 'parsing_issue',
            'data': issue,
            'metadata': {
                'parser': 'verify_tvtms_parsing.py'
            }
        }
        training_examples.append(example)
    
    # Save all examples to JSONL file
    with open(DSPY_TRAINING_PATH, 'w', encoding='utf-8') as f:
        for example in training_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    logger.info(f"Saved {len(training_examples)} training examples to {DSPY_TRAINING_PATH}")

def to_database_row(row):
    """
    Convert a TVTMS row dictionary to a database row format.
    
    Args:
        row: Dictionary with TVTMS row data
        
    Returns:
        Dictionary with database column mappings
    """
    source_ref = row.get('SourceRef', '')
    standard_ref = row.get('StandardRef', '')
    action = row.get('Action', '')
    
    # Extract book, chapter, verse from source reference (e.g., "Gen.2:25")
    source_book, source_chapter, source_verse = None, None, None
    if '.' in source_ref and ':' in source_ref:
        parts = source_ref.split('.')
        source_book = parts[0]
        chapter_verse = parts[1].split(':')
        source_chapter = chapter_verse[0]
        source_verse = chapter_verse[1]
    
    # Extract book, chapter, verse from target reference
    target_book, target_chapter, target_verse = None, None, None
    if '.' in standard_ref and ':' in standard_ref:
        parts = standard_ref.split('.')
        target_book = parts[0]
        chapter_verse = parts[1].split(':')
        target_chapter = chapter_verse[0]
        target_verse = chapter_verse[1]
    
    # Map action to mapping_type
    mapping_type_map = {
        'Keep verse': 'standard',
        'Renumber verse': 'Renumber',
        'Renumber title': 'Renumber',
        'MergedPrev verse': 'Merged',
        'MergedNext verse': 'Merged',
        'IfEmpty verse': 'IfEmpty',
        'SubdividedVerse': 'Split',
        'LongVerse': 'Absent',
        'LongVerseElsewhere': 'Absent',
        'LongVerseDuplicated': 'Absent',
        'TextMayBeMissing': 'Missing',
        'StartDifferent': 'Renumber',
        'Psalm Title': 'Renumber',
        'Empty verse': 'Missing',
        'Missing verse': 'Missing'
    }
    mapping_type = mapping_type_map.get(action, 'standard')
    
    # Extract source_tradition from SourceType
    source_tradition = row.get('SourceType', '').lower()
    
    return {
        'source_tradition': source_tradition,
        'target_tradition': 'standard',
        'source_book': source_book,
        'source_chapter': source_chapter,
        'source_verse': source_verse,
        'target_book': target_book,
        'target_chapter': target_chapter,
        'target_verse': target_verse,
        'mapping_type': mapping_type,
        'notes': f"{row.get('Reversification Note', '')} {row.get('Versification Note', '')}".strip(),
        'ancient_versions': row.get('Ancient Versions', '')
    }

def main():
    """Main function to verify TVTMS parsing."""
    try:
        if not os.path.exists(SECONDARY_TVTMS_PATH):
            logger.error(f"TVTMS file not found at {SECONDARY_TVTMS_PATH}")
            sys.exit(1)
        
        # Parse the TVTMS file
        rows, issues = parse_tvtms_file(SECONDARY_TVTMS_PATH)
        
        # Save samples for DSPy training
        save_dspy_training_data(rows, issues)
        
        # Convert rows to database format and report some statistics
        db_rows = [to_database_row(row) for row in rows]
        
        # Count number of rows by mapping_type
        mapping_type_counts = {}
        for row in db_rows:
            mapping_type = row['mapping_type']
            mapping_type_counts[mapping_type] = mapping_type_counts.get(mapping_type, 0) + 1
        
        logger.info("Mapping type counts:")
        for mapping_type, count in sorted(mapping_type_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {mapping_type}: {count}")
        
        # Count number of rows by source_tradition
        tradition_counts = {}
        for row in db_rows:
            tradition = row['source_tradition']
            tradition_counts[tradition] = tradition_counts.get(tradition, 0) + 1
        
        logger.info("Source tradition counts:")
        for tradition, count in sorted(tradition_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {tradition}: {count}")
        
        logger.info(f"Successfully parsed {len(rows)} TVTMS rows")
        
    except Exception as e:
        logger.error(f"Error verifying TVTMS file: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 