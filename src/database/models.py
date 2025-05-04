"""
SQLAlchemy models for Bible versification data using 2.0 style type annotations.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, ForeignKey, CheckConstraint, Index, Table, Column, Enum, Integer, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, validates, relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP, TEXT, VARCHAR, JSONB
from sqlalchemy.sql import func
import enum

class Base(DeclarativeBase):
    """Base class for all models"""
    pass

class MappingType(enum.Enum):
    """Valid mapping types"""
    STANDARD = "standard"
    RENUMBERING = "renumbering"
    MERGE = "merge"
    SPLIT = "split"
    OMIT = "omit"
    INSERT = "insert"

class RuleType(enum.Enum):
    """Valid rule types"""
    GENERAL = "general"
    SPECIFIC = "specific"
    EXCEPTION = "exception"
    CONDITIONAL = "conditional"

class VariationType(enum.Enum):
    """Valid variation types"""
    ADDITION = "addition"
    OMISSION = "omission"
    ORDER = "order"
    TEXT = "text"

class DocumentationCategory(enum.Enum):
    """Valid documentation categories"""
    OVERVIEW = "overview"
    METHODOLOGY = "methodology"
    EXAMPLES = "examples"
    NOTES = "notes"

class VersificationMapping(Base):
    """Represents a mapping between different versification traditions."""
    __tablename__ = 'versification_mappings'
    __table_args__ = (
        CheckConstraint(
            "mapping_type IN ('standard', 'renumbering', 'merge', 'split', 'omit', 'insert')",
            name='valid_mapping_type'
        ),
        Index('idx_versification_mappings_source', 'source_book', 'source_chapter', 'source_verse'),
        Index('idx_versification_mappings_target', 'target_book', 'target_chapter', 'target_verse'),
        {'schema': 'bible'}
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_tradition: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    target_tradition: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    source_book: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    source_chapter: Mapped[int] = mapped_column(CheckConstraint('source_chapter > 0'), nullable=False)
    source_verse: Mapped[int] = mapped_column(CheckConstraint('source_verse >= 0'), nullable=False)
    target_book: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    target_chapter: Mapped[int] = mapped_column(CheckConstraint('target_chapter > 0'), nullable=False)
    target_verse: Mapped[int] = mapped_column(CheckConstraint('target_verse >= 0'), nullable=False)
    mapping_type: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(TEXT)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    @validates('source_chapter', 'source_verse', 'target_chapter', 'target_verse')
    def validate_positive_number(self, key, value):
        """Validate that chapter and verse numbers are positive."""
        if value <= 0:
            raise ValueError(f"{key} must be a positive number")
        return value

    @validates('mapping_type')
    def validate_mapping_type(self, key, value):
        """Validate mapping type."""
        if isinstance(value, str):
            try:
                return MappingType(value.lower())
            except ValueError:
                raise ValueError(f"Invalid mapping type: {value}")
        return value

class VersificationRule(Base):
    """Represents rules for versification handling."""
    __tablename__ = 'versification_rules'
    __table_args__ = (
        CheckConstraint(
            "rule_type IN ('general', 'specific', 'exception', 'conditional')",
            name='valid_rule_type'
        ),
        {'schema': 'bible'}
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_type: Mapped[str] = mapped_column(Enum(RuleType), nullable=False)
    content: Mapped[str] = mapped_column(TEXT, nullable=False)
    section_title: Mapped[Optional[str]] = mapped_column(TEXT)
    applies_to: Mapped[Optional[str]] = mapped_column(TEXT)  # Consider using ARRAY type for PostgreSQL
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    @validates('rule_type')
    def validate_rule_type(self, key, value):
        """Validate rule type."""
        if isinstance(value, str):
            try:
                return RuleType(value.lower())
            except ValueError:
                raise ValueError(f"Invalid rule type: {value}")
        return value

class VersificationTradition(Base):
    """Represents different versification traditions."""
    __tablename__ = 'versification_traditions'
    __table_args__ = {'schema': 'bible'}

    id: Mapped[int] = mapped_column(primary_key=True)
    tradition_name: Mapped[str] = mapped_column(VARCHAR(50), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(TEXT, nullable=False)
    related_traditions: Mapped[Optional[str]] = mapped_column(TEXT)  # Consider using ARRAY type
    notes: Mapped[Optional[str]] = mapped_column(TEXT)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

class ManuscriptVariation(Base):
    """Represents manuscript-specific variations."""
    __tablename__ = 'manuscript_variations'
    __table_args__ = (
        CheckConstraint(
            "variation_type IN ('addition', 'omission', 'order', 'text')",
            name='valid_variation_type'
        ),
        {'schema': 'bible'}
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(TEXT, nullable=False)
    variation_type: Mapped[str] = mapped_column(Enum(VariationType), nullable=False)
    description: Mapped[str] = mapped_column(TEXT, nullable=False)
    affected_traditions: Mapped[Optional[str]] = mapped_column(TEXT)  # Consider using ARRAY type
    notes: Mapped[Optional[str]] = mapped_column(TEXT)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    @validates('variation_type')
    def validate_variation_type(self, key, value):
        """Validate variation type."""
        if isinstance(value, str):
            try:
                return VariationType(value.lower())
            except ValueError:
                raise ValueError(f"Invalid variation type: {value}")
        return value

class VersificationDocumentation(Base):
    """Represents explanatory documentation."""
    __tablename__ = 'versification_documentation'
    __table_args__ = (
        CheckConstraint(
            "category IN ('overview', 'methodology', 'examples', 'notes')",
            name='valid_category'
        ),
        {'schema': 'bible'}
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    section_title: Mapped[str] = mapped_column(TEXT, nullable=False)
    content: Mapped[str] = mapped_column(TEXT, nullable=False)
    category: Mapped[str] = mapped_column(Enum(DocumentationCategory), nullable=False)
    related_sections: Mapped[Optional[str]] = mapped_column(TEXT)  # Consider using ARRAY type
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    @validates('category')
    def validate_category(self, key, value):
        """Validate documentation category."""
        if isinstance(value, str):
            try:
                return DocumentationCategory(value.lower())
            except ValueError:
                raise ValueError(f"Invalid documentation category: {value}")
        return value

class Book(Base):
    """Model for Bible books.
    
    This model represents books of the Bible, storing their names, order,
    and other metadata. It serves as a reference for verses and maintains
    the canonical order of books.
    
    Attributes:
        book_name (str): Primary key - The name of the book
        book_number (int): The canonical order/number of the book
        testament (str): Either 'OT' or 'NT'
        chapters (int): Total number of chapters in the book
        verses (int): Total number of verses in the book
        meta_data (dict): Additional metadata stored as JSONB
    """
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("testament IN ('OT', 'NT')", name="valid_testament"),
        {"schema": "bible"}
    )

    book_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    testament: Mapped[str] = mapped_column(String(2), nullable=False)
    book_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chapters: Mapped[int] = mapped_column(Integer, nullable=False)
    verses: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    verse_list: Mapped[List["Verse"]] = relationship(back_populates="book", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Book(name='{self.book_name}', testament='{self.testament}')>"


class Verse(Base):
    """Model for Bible verses."""
    __tablename__ = "verses"
    __table_args__ = (
        {"schema": "bible"}
    )

    id = Column(Integer, primary_key=True)
    book_name = Column(String(100), ForeignKey("bible.books.book_name"), nullable=False)
    chapter = Column(Integer, nullable=False)
    verse = Column(Integer, nullable=False)
    word = Column(Text, nullable=True)
    transliteration = Column(Text, nullable=True)
    strongs = Column(Text, nullable=True)
    morphology = Column(Text, nullable=True)
    gloss = Column(Text, nullable=True)
    function = Column(Text, nullable=True)
    root = Column(Text, nullable=True)
    strongs_json = Column(JSONB, nullable=True)
    morphology_json = Column(JSONB, nullable=True)
    variant_data = Column(JSONB, nullable=True)
    
    # Relationships
    book = relationship("Book", back_populates="verse_list")

    def __repr__(self):
        return f"<Verse(book='{self.book_name}', chapter={self.chapter}, verse={self.verse})>"


class ProperName(Base):
    """Model for proper names in the Bible."""
    __tablename__ = "proper_names"
    __table_args__ = (
        Index("idx_proper_names_name", "name"),
        {"schema": "bible"}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    transliteration = Column(Text)
    language = Column(String(50))
    meaning = Column(Text)
    references_json = Column(JSONB)  # Store verse references as JSON

    def __repr__(self):
        return f"<ProperName(name='{self.name}', language='{self.language}')>"


class LexiconEntry(Base):
    """Model for lexicon entries (Hebrew and Greek)."""
    __tablename__ = "lexicon_entries"
    __table_args__ = (
        Index("idx_lexicon_strongs", "strongs_number"),
        {"schema": "lexicon"}
    )

    id = Column(Integer, primary_key=True)
    strongs_number = Column(String(10), nullable=False, unique=True)
    language = Column(String(10), CheckConstraint("language IN ('hebrew', 'greek')"), nullable=False)
    lemma = Column(Text, nullable=False)
    transliteration = Column(Text)
    pronunciation = Column(Text)
    definition = Column(Text)
    usage = Column(Text)
    etymology = Column(Text)
    references_json = Column(JSONB)  # Store verse references as JSON

    def __repr__(self):
        return f"<LexiconEntry(strongs='{self.strongs_number}', lemma='{self.lemma}')>"


class MorphologyCode(Base):
    """Model for morphology codes and their explanations."""
    __tablename__ = "morphology_codes"
    __table_args__ = (
        Index("idx_morphology_code", "code"),
        {"schema": "morphology"}
    )

    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False, unique=True)
    language = Column(String(10), CheckConstraint("language IN ('hebrew', 'greek')"), nullable=False)
    category = Column(String(50))  # e.g., 'verb', 'noun', etc.
    description = Column(Text, nullable=False)
    explanation = Column(Text)
    examples_json = Column(JSONB)  # Store example usages as JSON

    def __repr__(self):
        return f"<MorphologyCode(code='{self.code}', language='{self.language}')>"

class GreekEntry(Base):
    __tablename__ = 'greek_entries'
    __table_args__ = {'schema': 'bible'}

    id = Column(Integer, primary_key=True)
    strongs_ref = Column(String(20), unique=True, nullable=False)
    extended_strongs = Column(String(50))
    dstrongs = Column(String(50))
    ustrongs = Column(String(50))
    related_ref = Column(Text)
    word = Column(String(100))
    transliteration = Column(String(100))
    part_of_speech = Column(String(500))
    gloss = Column(Text)
    definition = Column(Text)
    morph = Column(Text)
    meta_data = Column(JSONB)

class HebrewEntry(Base):
    __tablename__ = 'hebrew_entries'
    __table_args__ = {'schema': 'bible'}

    id = Column(Integer, primary_key=True)
    strongs_ref = Column(String(20), unique=True, nullable=False)
    extended_strongs = Column(String(50))
    dstrongs = Column(String(50))
    ustrongs = Column(String(50))
    related_ref = Column(Text)
    word = Column(String(100))
    transliteration = Column(String(100))
    part_of_speech = Column(String(500))
    gloss = Column(Text)
    definition = Column(Text)
    morph = Column(Text)
    meta_data = Column(JSONB)

class WordRelationship(Base):
    __tablename__ = 'word_relationships'
    __table_args__ = {'schema': 'bible'}

    id = Column(Integer, primary_key=True)
    source_ref = Column(String(20), nullable=False)
    target_ref = Column(String(20), nullable=False)
    relationship_type = Column(String(50), nullable=False)
    meta_data = Column(JSONB)
    
    __table_args__ = (
        UniqueConstraint('source_ref', 'target_ref', 'relationship_type'),
        {'schema': 'bible'}
    ) 