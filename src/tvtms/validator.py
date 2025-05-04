"""
Validation module for TVTMS data.
"""

import os
import logging
from typing import List, Dict, Set, Any, Optional
import psycopg
from .models import Mapping
from .database import get_db_connection, release_connection
import re
from .constants import (
    BOOK_VARIATIONS_MAP,
    VALID_CATEGORIES,
    MAPPING_TYPES,
    SPECIAL_MARKERS,
    SKIP_CASES,
    ACTION_PRIORITY
)
import copy

logger = logging.getLogger(__name__)

class TVTMSValidator:
    """Validator for TVTMS data."""
    
    def __init__(self):
        """Initialize the validator."""
        self.book_abbreviations = {}
        self.book_names = {}
        self.valid_book_ids = set(BOOK_VARIATIONS_MAP.values())
        self.VALID_CATEGORIES = VALID_CATEGORIES
        self.VALID_MAPPING_TYPES = set(ACTION_PRIORITY)
        self.VALID_MAPPING_TYPES.add('standard')
        self._load_book_data()
    
    def _load_book_data(self):
        """Load book data from the database."""
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                # Get book data
                cur.execute("""
                    SELECT book_id, name 
                    FROM bible.books
                """)
                for row in cur.fetchall():
                    book_id, name = row['book_id'], row['name']
                    self.book_abbreviations[book_id] = book_id  # Use book_id as both key and value
                    self.book_names[name] = book_id  # Map full name to book_id
                    self.valid_book_ids.add(book_id)
                
                # Get book abbreviations
                cur.execute("""
                    SELECT book_id, alternate_abbreviation 
                    FROM bible.book_abbreviations
                """)
                for row in cur.fetchall():
                    book_id, abbrev = row['book_id'], row['alternate_abbreviation']
                    self.book_abbreviations[abbrev] = book_id
                    
                logger.debug(f"Loaded {len(self.valid_book_ids)} book IDs")
                logger.debug(f"Loaded {len(self.book_abbreviations)} book abbreviations")

        except Exception as e:
            logger.error(f"Failed to load book data: {str(e)}")
            raise
        finally:
            if conn:
                release_connection(conn)
    
    def normalize_book_name(self, book: str) -> Optional[str]:
        """Normalize a book name."""
        if not book:
            return None

        # Clean up input
        book = book.strip().strip('*#[]').strip()
        
        # Skip special cases
        if book.lower() in SKIP_CASES:
            return None

        # Handle book names with dots by taking first part
        if '.' in book:
            book = book.split('.')[0]

        # Try direct match (case-insensitive)
        book_lower = book.lower()
        for variant, standard in BOOK_VARIATIONS_MAP.items():
            if book_lower == variant.lower():
                return standard

        # Handle numbered books (e.g., "1 Kings", "2 Samuel")
        match = re.match(r'^([1-4])\s*([A-Za-z]+)$', book)
        if match:
            number, name = match.groups()
            combined = f"{number} {name}"
            if combined in BOOK_VARIATIONS_MAP:
                return BOOK_VARIATIONS_MAP[combined]

        logger.warning(f"Could not normalize book name: {book}")
        return None
    
    def normalize_book_reference(self, book: str) -> str:
        """Normalize a book reference."""
        if not book:
            return None
        
        # Handle special cases
        if book == 'Absent':
            return None
        
        # Remove any leading/trailing whitespace
        book = book.strip()
        
        # Check if it's an abbreviation
        if book in self.book_abbreviations:
            return self.book_abbreviations[book]
        
        # Check if it's a full name
        if book in self.book_names:
            return self.book_names[book]
        
        # Try normalizing through BOOK_VARIATIONS_MAP
        normalized = self.normalize_book_name(book)
        if normalized:
            return normalized
        
        # Unknown book name
        logger.warning(f"Unknown book name: {book}")
        return None
    
    def normalize_category(self, category: str) -> str:
        """Normalize a category."""
        if not category:
            return 'None'
        category = category.strip()
        if category in self.VALID_CATEGORIES:
            return category
        if category.endswith('.'):
            category = category[:-1]
        if category in self.VALID_CATEGORIES:
            return category
        logger.warning(f"Invalid category: {category}")
        return 'None'
    
    def validate_reference(self, ref: Dict[str, Any]) -> bool:
        """Validate a Bible reference."""
        if not ref:
            return False

        book = ref.get('book')
        chapter = ref.get('chapter')
        verse = ref.get('verse')
        subverse = ref.get('subverse')

        error = self._validate_reference(book, chapter, verse, subverse)
        if error:
            logger.warning(error)
            return False
        return True

    def _validate_reference(self, book: str, chapter: str, verse: Optional[int], subverse: Optional[str]) -> Optional[str]:
        """Validate individual components of a Bible reference."""
        # Validate book
        if not book or book not in self.valid_book_ids:
            return f"Invalid book: {book}"

        # Validate chapter
        if not chapter:
            return "Missing chapter"
        
        # Handle letter chapters (A-F)
        if isinstance(chapter, str) and chapter.isalpha():
            if not re.match(r'^[A-F]$', chapter):
                return f"Invalid letter chapter: {chapter}"
        else:
            try:
                chapter_num = int(chapter)
                if chapter_num < 1:
                    return f"Invalid chapter number: {chapter}"
            except ValueError:
                return f"Invalid chapter format: {chapter}"

        # Validate verse
        if verse is not None:
            if not isinstance(verse, int):
                return f"Invalid verse format: {verse}"
            # Allow verse 0 for Psalms (titles)
            if verse < 0 or (verse == 0 and not book.startswith('Psa')):
                return f"Invalid verse number: {verse}"

        # Validate subverse
        if subverse:
            if not re.match(r'^[a-z]$|^\d+$', subverse):
                return f"Invalid subverse format: {subverse}"

        return None

    def validate_reference_fields(self, book, chapter, verse):
        """Validate reference fields for a mapping."""
        if not book or not chapter or verse is None:
            return False
        # Allow verse=0 for Psalm titles
        if book == 'Psa' and str(chapter).isdigit() and verse == 0:
            return True
        # Normal verses must be > 0
        if not str(chapter).isdigit() or not isinstance(verse, int) or verse <= 0:
            return False
        # Add further validation as needed (e.g., check if book is valid, etc.)
        return True

    def is_valid(self, mapping: Mapping) -> bool:
        """Validate a mapping, ensuring required fields are present and values are valid."""
        
        # 1. Check if mapping type is valid
        if mapping.mapping_type not in self.VALID_MAPPING_TYPES:
            logger.warning(f"Invalid mapping_type '{mapping.mapping_type}' for mapping: {mapping}")
            return False

        # 2. Check if category is valid
        if mapping.category not in self.VALID_CATEGORIES:
            logger.warning(f"Invalid category '{mapping.category}' for mapping: {mapping}")
            return False
        
        # 3. Check for required Target fields (almost always needed)
        if not mapping.target_book:
            logger.warning(f"Missing required target_book for mapping: {mapping}")
            return False
        if not mapping.target_chapter:
            logger.warning(f"Missing required target_chapter for mapping: {mapping}")
            return False
        if mapping.target_verse is None:
            logger.warning(f"Missing required target_verse for mapping: {mapping}")
            return False
        # Validate target fields if present (basic format check)
        if not self.validate_reference_fields(mapping.target_book, mapping.target_chapter, mapping.target_verse):
             logger.warning(f"Invalid target reference fields: book={mapping.target_book}, chapter={mapping.target_chapter}, verse={mapping.target_verse} in mapping: {mapping}")
             return False
        
        # 4. Check for required Source fields (depends on mapping type)
        # Absent mappings inherently lack source refs. Others generally need them.
        # Add other types that might lack source refs if identified.
        source_required = mapping.source_book is not None # True if source_book is not None (i.e., not an 'Absent' type mapping)

        if source_required:
            if not mapping.source_chapter:
                logger.warning(f"Missing required source_chapter for mapping: {mapping}")
                return False
            if mapping.source_verse is None:
                logger.warning(f"Missing required source_verse for mapping: {mapping}")
                return False
            # Validate source fields if present (basic format check)
            if not self.validate_reference_fields(mapping.source_book, mapping.source_chapter, mapping.source_verse):
                 logger.warning(f"Invalid source reference fields: book={mapping.source_book}, chapter={mapping.source_chapter}, verse={mapping.source_verse} in mapping: {mapping}")
                 return False
        # If source is not required (e.g., Absent mapping), no source field check needed.
        
        # If all checks pass
        return True

    def validate_mappings(self, mappings: List[Mapping]) -> List[Mapping]:
        """Validate a list of mappings."""
        validated_list = []
        for mapping_obj in mappings:
            if self.is_valid(mapping_obj):
                # Append a deep copy instead of the original object
                validated_list.append(copy.deepcopy(mapping_obj))
        return validated_list

# For backward compatibility
VersificationValidator = TVTMSValidator 