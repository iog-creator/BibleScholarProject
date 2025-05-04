"""
Parser for TVTMS TSV file format.
"""

import pandas as pd
import logging
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from .models import Mapping, Rule, Documentation

logger = logging.getLogger(__name__)

class TVTMSTSVParser:
    """Parser for TVTMS TSV format."""
    
    # Valid categories for versification mappings
    VALID_CATEGORIES = {'Opt', 'Nec', 'Acd', 'Inf', 'None'}
    
    # Mapping types
    MAPPING_TYPES = {
        'Keep verse': 'standard',
        'Renumber verse': 'renumbering',
        'Renumber title': 'renumbering',
        'MergedPrev verse': 'merge',
        'MergedNext verse': 'merge',
        'IfEmpty verse': 'omit',
        'SubdividedVerse': 'split',
        'LongVerse': 'insert',
        'LongVerseElsewhere': 'insert',
        'LongVerseDuplicated': 'insert',
        'TextMayBeMissing': 'omit',
        'StartDifferent': 'renumbering',
        'Psalm Title': 'renumbering',
        'Empty verse': 'omit',
        'Missing verse': 'omit'
    }
    
    def __init__(self):
        """Initialize the parser."""
        self.current_tradition = None
        self.current_book = None
    
    def parse_file(self, file_path: str) -> Tuple[List[Mapping], List[Rule], List[Documentation]]:
        """Parse a TVTMS TSV file.
        
        Args:
            file_path: Path to the TSV file
            
        Returns:
            Tuple of (mappings, rules, documentation)
        """
        try:
            # Read the TSV file
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
            
            # Initialize results
            mappings = []
            rules = []
            documentation = []
            
            # Process each row
            for idx, row in df.iterrows():
                try:
                    # Skip empty rows
                    if pd.isna(row).all():
                        continue
                    
                    # Extract fields
                    tradition = str(row.get('SourceType', '')).strip()
                    source_ref = str(row.get('SourceRef', '')).strip()
                    target_ref = str(row.get('StandardRef', '')).strip()
                    action = str(row.get('Action', '')).strip()
                    note_marker = str(row.get('NoteMarker', '')).strip()
                    note_a = str(row.get('Note A', '')).strip()
                    note_b = str(row.get('Note B', '')).strip()
                    ancient_versions = str(row.get('Ancient Versions', '')).strip()
                    test_conditions = str(row.get('Tests', '')).strip()
                    
                    # Skip rows without required fields
                    if not source_ref or not target_ref or not action:
                        continue
                    
                    # Update tradition context
                    if tradition:
                        self.current_tradition = tradition
                    
                    # Create mapping
                    mapping_type = self.normalize_mapping_type(action)
                    mapping = self._create_mapping({
                        'tradition': self.current_tradition or 'unknown',
                        'source_ref': source_ref,
                        'target_ref': target_ref,
                        'mapping_type': mapping_type,
                        'note_marker': note_marker,
                        'notes': ' '.join(filter(None, [note_a, note_b])),
                        'ancient_versions': ancient_versions,
                        'category': self.extract_category(note_marker)
                    })
                    
                    if mapping:
                        mappings.append(mapping)
                    
                    # Add test conditions as rules
                    if test_conditions:
                        rules.append(Rule(
                            rule_type='conditional',
                            content=test_conditions,
                            section_title=None,
                            applies_to=[self.current_tradition] if self.current_tradition else [],
                            notes=ancient_versions
                        ))
                    
                    # Add notes as documentation
                    for note in [note_a, note_b]:
                        if note:
                            documentation.append(Documentation(
                                section_title=None,
                                content=note,
                                category='notes',
                                applies_to=[self.current_tradition] if self.current_tradition else [],
                                meta_data={'note_marker': note_marker}
                            ))
                
                except Exception as e:
                    logger.warning(f"Error processing row {idx}: {e}")
                    continue
            
            # Sort mappings
            mappings.sort(key=lambda m: (m.source_book, m.source_chapter, m.source_verse))
            
            return mappings, rules, documentation
            
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            return [], [], []
    
    def normalize_mapping_type(self, mapping_type: str) -> str:
        """Normalize mapping type to standard format."""
        if not mapping_type:
            return 'standard'
        
        mapping_type = mapping_type.strip()
        
        # Direct match
        if mapping_type in self.MAPPING_TYPES:
            return self.MAPPING_TYPES[mapping_type]
        
        # Case-insensitive match
        mapping_type_lower = mapping_type.lower()
        for k, v in self.MAPPING_TYPES.items():
            if k.lower() == mapping_type_lower:
                return v
        
        logger.debug(f"Unknown mapping type '{mapping_type}', defaulting to 'standard'")
        return 'standard'
    
    def extract_category(self, note_marker: str) -> str:
        """Extract category from note marker."""
        if not note_marker:
            return 'None'
        
        # Look for category prefix (e.g., "Opt.", "Nec.", "Acd.")
        parts = note_marker.split('.')
        if parts:
            category = parts[0].strip()
            if category in self.VALID_CATEGORIES:
                return category
            
            # Try without trailing period
            if category.endswith('.'):
                category = category[:-1]
                if category in self.VALID_CATEGORIES:
                    return category
        
        return 'None'
    
    def _create_mapping(self, row: Dict[str, Any]) -> Optional[Mapping]:
        """Create a mapping from row data."""
        try:
            # Parse source reference
            source_parts = row['source_ref'].split('.')
            if len(source_parts) < 2:
                return None
            
            source_book = source_parts[0]
            source_chapter_verse = source_parts[1].split(':')
            if len(source_chapter_verse) != 2:
                return None
            
            source_chapter = int(source_chapter_verse[0])
            source_verse = int(source_chapter_verse[1])
            
            # Parse target reference
            target_parts = row['target_ref'].split('.')
            if len(target_parts) < 2:
                return None
            
            target_book = target_parts[0]
            target_chapter_verse = target_parts[1].split(':')
            if len(target_chapter_verse) != 2:
                return None
            
            target_chapter = int(target_chapter_verse[0])
            target_verse = int(target_chapter_verse[1])
            
            return Mapping(
                source_tradition=row['tradition'],
                target_tradition='standard',
                source_book=source_book,
                source_chapter=source_chapter,
                source_verse=source_verse,
                source_subverse=None,  # TODO: Handle subverses
                manuscript_marker=None,  # TODO: Handle manuscript markers
                target_book=target_book,
                target_chapter=target_chapter,
                target_verse=target_verse,
                target_subverse=None,  # TODO: Handle subverses
                mapping_type=row['mapping_type'],
                category=row['category'],
                notes=row['notes'],
                note_marker=row['note_marker'],
                ancient_versions=row['ancient_versions']
            )
            
        except Exception as e:
            logger.warning(f"Failed to create mapping: {e}")
            return None

def parse_tvtms_tsv(file_path: str) -> Dict[str, List]:
    """Parse TVTMS TSV file and return mappings, rules, and documentation.
    
    Args:
        file_path: Path to the TSV file
        
    Returns:
        Dictionary with keys 'mappings', 'rules', and 'documentation'
    """
    parser = TVTMSTSVParser()
    mappings, rules, documentation = parser.parse_file(file_path)
    return {
        'mappings': mappings,
        'rules': rules,
        'documentation': documentation
    } 