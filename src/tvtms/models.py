"""
Data models for TVTMS ETL.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import re

@dataclass
class Mapping:
    """Represents a mapping between different versification traditions."""
    source_tradition: str
    target_tradition: str
    source_book: str
    source_chapter: str
    source_verse: Optional[int]
    source_subverse: Optional[str]
    manuscript_marker: Optional[str]
    target_book: str
    target_chapter: str
    target_verse: Optional[int]
    target_subverse: Optional[str]
    mapping_type: str
    category: Optional[str]
    notes: Optional[str]
    source_range_note: Optional[str]
    target_range_note: Optional[str]
    note_marker: Optional[str]
    ancient_versions: Optional[str]

    def to_dict(self):
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
        if self.source_chapter is None or self.target_chapter is None:
            raise ValueError("Required field: source_chapter or target_chapter is missing")
        if self.source_verse is None or self.target_verse is None:
            raise ValueError("Required field: source_verse or target_verse is missing")
        # Valid mapping_type
        valid_types = {'standard', 'renumbering', 'merge', 'split', 'omit', 'insert'}
        if self.mapping_type not in valid_types:
            raise ValueError(f"Invalid mapping_type: {self.mapping_type}")
        # Valid category (allow None)
        valid_categories = {'Opt', 'Nec', 'Acd', 'Inf', 'None'}
        if self.category is not None and self.category not in valid_categories:
            raise ValueError(f"Invalid category: {self.category}")
        # Numeric checks
        if isinstance(self.source_chapter, int) and self.source_chapter <= 0:
            raise ValueError("Invalid source_chapter: must be > 0")
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