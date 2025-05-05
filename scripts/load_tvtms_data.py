#!/usr/bin/env python3
"""
Script to load TVTMS data from the secondary source.
This script is used to populate the versification_mappings table.
"""

import os
import sys
import logging
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tvtms.parser import TVTMSParser
from src.tvtms.database import store_mappings, store_rules, store_documentation
from src.database.connection import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/load_tvtms_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('load_tvtms_data')

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
    
    logger.info(f"Parsing TVTMS file: {file_path}")
    
    # First pass - identify data section positions and header
    with open(file_path, encoding='utf-8') as f:
        content = f.readlines()
    
    start_idx = None
    end_idx = None
    header_idx = None
    for idx, line in enumerate(content):
        if line.strip().startswith(start_marker):
            start_idx = idx + 1  # +1 to skip the marker line
            continue
        
        if start_idx is not None and header is None and line.strip() and not line.strip().startswith("'="):
            header = [h.strip() for h in line.split('\t')]
            header_idx = idx
            logger.info(f"Found header: {header}")
            continue
            
        if line.strip().startswith(end_marker):
            end_idx = idx
            break
    
    if start_idx is None:
        raise ValueError("#DataStart(Expanded) not found in TVTMS file")
    
    if end_idx is None:
        end_idx = len(content)
    
    if header_idx is None:
        raise ValueError("Header line not found in TVTMS file")
    
    # Set start_idx to after the header line
    start_idx = header_idx + 1
    
    logger.info(f"Found start marker at line {start_idx}")
    if end_idx < len(content):
        logger.info(f"Found end marker at line {end_idx}")
    
    # Extract the data section (skip the header line)
    data_lines = content[start_idx:end_idx]
    
    # Filter empty lines and comments
    filtered_lines = [line for line in data_lines if line.strip() and not line.strip().startswith("'=")]
    
    # Parse each line as tab-separated data
    for line_num, line in enumerate(filtered_lines, start=start_idx+1):
        try:
            fields = line.strip().split('\t')
            
            # Ensure we have at least as many fields as header items
            if len(fields) >= len(header):
                # Create a dictionary with header keys and field values
                row_data = {}
                for i, col_name in enumerate(header):
                    if i < len(fields) and col_name:  # Make sure the column has a name
                        row_data[col_name] = fields[i]
                
                rows.append(row_data)
            else:
                # Record as an issue for DSPy training
                issue = {
                    'line_num': line_num,
                    'content': line.strip(),
                    'error': f"Not enough fields (expected {len(header)}, got {len(fields)})",
                    'fields': fields
                }
                issues.append(issue)
        except Exception as e:
            # Record parsing errors for DSPy training
            issue = {
                'line_num': line_num,
                'content': line.strip(),
                'error': str(e)
            }
            issues.append(issue)
    
    logger.info(f"Parsed {len(rows)} rows, found {len(issues)} issues")
    return rows, issues

def process_tvtms_data(rows):
    """
    Process TVTMS rows and create mapping objects.
    
    Args:
        rows: List of dictionaries representing TVTMS rows
        
    Returns:
        Tuple of (mappings, rules, documentation)
    """
    parser = TVTMSParser()
    
    mappings = []
    rules = []
    documentation = []
    
    for row in rows:
        try:
            # Extract fields using the actual header names from the file
            source_type = row.get('SourceType', '').strip()
            source_ref = row.get('SourceRef', '').strip()
            standard_ref = row.get('StandardRef', '').strip()
            action = row.get('Action', '').strip()
            note_marker = row.get('NoteMarker', '').strip()
            
            # Handle different note column names that might be present
            note_a = (row.get('Reversification Note', '') or row.get('NoteA', '') or '').strip()
            note_b = (row.get('Versification Note', '') or row.get('NoteB', '') or '').strip()
            
            ancient_versions = row.get('Ancient Versions', '').strip()
            tests = row.get('Tests', '').strip()
            
            # Skip rows with missing essential data
            if not source_ref or not standard_ref or not action:
                continue
                
            new_mappings = parser._create_mappings_from_row(
                source_type, source_ref, standard_ref, action,
                note_marker, note_a, note_b, ancient_versions, tests
            )
            
            if new_mappings:
                mappings.extend(new_mappings)
                
        except Exception as e:
            logger.error(f"Error processing row: {e}")
            logger.error(f"Problematic row: {row}")
    
    logger.info(f"Created {len(mappings)} mapping objects")
    return mappings, rules, documentation

def main():
    """Main function to load TVTMS data."""
    parser = argparse.ArgumentParser(description='Load TVTMS data into the database')
    parser.add_argument('--file', help='Path to TVTMS file', default='../STEPBible-Datav2/STEPBible-Data/TVTMS - Translators Versification Traditions with Methodology for Standardisation for Eng+Heb+Lat+Grk+Others - STEPBible.org CC BY.txt')
    args = parser.parse_args()
    
    try:
        # Ensure file exists
        if not os.path.isfile(args.file):
            logger.error(f"TVTMS file not found: {args.file}")
            return
        
        # Parse the TVTMS file
        rows, issues = parse_tvtms_file(args.file)
        
        # Process the rows to create mapping objects
        mappings, rules, documentation = process_tvtms_data(rows)
        
        # Connect to the database
        conn = get_db_connection()
        
        # Store the data
        try:
            # Clear existing data
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE bible.versification_mappings RESTART IDENTITY CASCADE;")
                cur.execute("TRUNCATE TABLE bible.versification_rules RESTART IDENTITY CASCADE;")
                cur.execute("TRUNCATE TABLE bible.versification_documentation RESTART IDENTITY CASCADE;")
                conn.commit()
                logger.info("Truncated existing versification tables")
                
            # Store mappings, rules, and documentation
            mapping_count = store_mappings(mappings, conn)
            logger.info(f"Stored {mapping_count} mappings")
            
            if rules:
                store_rules(rules, conn)
                logger.info(f"Stored {len(rules)} rules")
                
            if documentation:
                store_documentation(documentation, conn)
                logger.info(f"Stored {len(documentation)} documentation items")
                
            logger.info("TVTMS data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error storing TVTMS data: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error loading TVTMS data: {e}")
        raise

if __name__ == "__main__":
    main() 