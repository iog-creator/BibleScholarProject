"""
Data models for TVTMS ETL.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import re

@dataclass
class Mapping:
    """Class representing a versification mapping between traditions."""
    def __init__(self, 
                 source_tradition=None, 
                 target_tradition=None,
                 source_book=None, 
                 source_chapter=None, 
                 source_verse=None, 
                 source_subverse=None,
                 manuscript_marker=None,
                 target_book=None, 
                 target_chapter=None, 
                 target_verse=None, 
                 target_subverse=None,
                 mapping_type=None, 
                 category=None, 
                 notes=None, 
                 source_range_note=None, 
                 target_range_note=None,
                 note_marker=None,
                 ancient_versions=None):
        """Initialize a mapping with the given attributes."""
        self.source_tradition = source_tradition
        self.target_tradition = target_tradition
        self.source_book = source_book
        self.source_chapter = source_chapter
        self.source_verse = source_verse
        self.source_subverse = source_subverse
        self.manuscript_marker = manuscript_marker
        self.target_book = target_book
        self.target_chapter = target_chapter
        self.target_verse = target_verse
        self.target_subverse = target_subverse
        self.mapping_type = mapping_type
        self.category = category
        self.notes = notes
        self.source_range_note = source_range_note
        self.target_range_note = target_range_note
        self.note_marker = note_marker
        self.ancient_versions = ancient_versions
        
    def __repr__(self):
        """Return a string representation of the mapping."""
        return (f"Mapping({self.source_tradition}, {self.target_tradition}, "
                f"{self.source_book} {self.source_chapter}:{self.source_verse}, "
                f"{self.target_book} {self.target_chapter}:{self.target_verse}, "
                f"{self.mapping_type})")

    def to_dict(self):
        """Convert the Mapping object to a dictionary suitable for database insertion."""
        return {
            'source_tradition': self.source_tradition,
            'target_tradition': self.target_tradition,
            'source_book': self.source_book,
            'source_chapter': self.source_chapter,
            'source_verse': self.source_verse,
            'source_subverse': self.source_subverse,
            'manuscript_marker': self.manuscript_marker,
            'target_book': self.target_book,
            'target_chapter': self.target_chapter,
            'target_verse': self.target_verse,
            'target_subverse': self.target_subverse,
            'mapping_type': self.mapping_type,
            'category': self.category,
            'notes': self.notes,
            'source_range_note': self.source_range_note,
            'target_range_note': self.target_range_note,
            'note_marker': self.note_marker,
            'ancient_versions': self.ancient_versions
        }

    def is_valid(self) -> bool:
        """Validate the mapping object."""
        # Required fields
        if not self.source_tradition or not self.target_tradition:
            raise ValueError("Required field: source_tradition or target_tradition is missing")
        if not self.source_book or not self.target_book:
            raise ValueError("Required field: source_book or target_book is missing")
        if self.mapping_type and self.mapping_type.startswith('range_'):
            # For range mappings, chapter and verse can be None
            pass
        elif self.source_chapter is None or self.target_chapter is None:
            raise ValueError("Required field: source_chapter or target_chapter is missing")
        elif self.source_verse is None or self.target_verse is None:
            raise ValueError("Required field: source_verse or target_verse is missing")
        
        # Valid mapping_type
        valid_types = {
            'standard', 'renumber', 'merge_prev', 'merge_next', 'split', 
            'absent', 'missing', 'conditional', 'special',
            'range_start', 'range_end', 'section_range'
        }
        if self.mapping_type not in valid_types:
            raise ValueError(f"Invalid mapping_type: {self.mapping_type}")
        
        # Valid category (allow None)
        valid_categories = {'Opt', 'Nec', 'Acd', 'Inf', 'None'}
        if self.category is not None and self.category not in valid_categories:
            raise ValueError(f"Invalid category: {self.category}")
        
        # Numeric checks - skip for range mappings
        if not self.mapping_type.startswith('range_') and not self.mapping_type == 'section_range':
            if self.source_chapter is not None:
                try:
                    chapter_value = int(self.source_chapter)
                    if chapter_value <= 0:
                        raise ValueError("Invalid source_chapter: must be > 0")
                except ValueError:
                    # If not numeric, let it pass (could be special format)
                    pass
        
        return True

@dataclass
class Rule:
    """Represents a versification rule."""
    rule_id: Optional[int]
    rule_type: str
    source_tradition: str
    target_tradition: str
    pattern: str
    description: Optional[str] = None

    def is_valid(self) -> bool:
        """Validate the rule object."""
        if not self.rule_type or not self.pattern:
            raise ValueError("Required field: rule_type or pattern is missing")
        if not self.source_tradition or not self.target_tradition:
            raise ValueError("Required field: source_tradition or target_tradition is missing")
        valid_types = {'conditional', 'procedural', 'structural', 'semantic'}
        if self.rule_type.lower() not in valid_types:
            raise ValueError(f"Invalid rule_type: {self.rule_type}")
        return True

@dataclass
class Documentation:
    """Represents versification documentation."""
    section_title: Optional[str]
    content: str
    category: Optional[str] = None
    related_sections: Optional[str] = None
    notes: Optional[str] = None

    def is_valid(self) -> bool:
        """Validate the documentation object."""
        if not self.content:
            raise ValueError("Required field: content is missing")
        if self.category is not None:
            valid_categories = {'overview', 'methodology', 'examples', 'notes'}
            if self.category not in valid_categories:
                raise ValueError(f"Invalid category: {self.category}")
        return True 