"""
SQLAlchemy utilities for enhanced database operations.
This module provides optional SQLAlchemy functionality that can be used alongside
the existing database operations.
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional, List, Dict, Any, Tuple
from sqlalchemy import create_engine, text, func, and_, or_, Text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import select
from dotenv import load_dotenv
import logging
import json
from sqlalchemy.exc import SQLAlchemyError
from database import get_db, BATCH_SIZE
from models import (
    Base, VersificationMapping, VersificationRule,
    VersificationTradition, ManuscriptVariation,
    VersificationDocumentation, Book, Verse, ProperName, LexiconEntry, MorphologyCode
)

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
    'dbname': os.getenv('DB_NAME', 'bible_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

# Create engine
engine = create_engine(
    f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['dbname']}",
    pool_size=5,
    max_overflow=10
)

# Session factory
SessionLocal = sessionmaker(bind=engine)

logger = logging.getLogger(__name__)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_models():
    """Initialize SQLAlchemy models."""
    # Create schema if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bible"))
        conn.commit()
    
    # Create tables
    Base.metadata.create_all(engine)

# Enhanced utility functions for ETL pipeline
def batch_validate_mappings(mappings: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate a batch of mappings before insertion.
    Returns tuple of (valid_mappings, invalid_mappings).
    """
    valid = []
    invalid = []
    
    for mapping in mappings:
        try:
            # Try to create a model instance to validate
            VersificationMapping(**mapping)
            valid.append(mapping)
        except Exception as e:
            mapping['error'] = str(e)
            invalid.append(mapping)
    
    return valid, invalid

def get_mapping_statistics() -> Dict[str, Any]:
    """Get statistics about versification mappings."""
    with get_db() as db:
        stats = {}
        
        # Total mappings
        stats['total_mappings'] = db.query(func.count(VersificationMapping.id)).scalar()
        
        # Mappings by type
        type_counts = db.query(
            VersificationMapping.mapping_type,
            func.count(VersificationMapping.id)
        ).group_by(VersificationMapping.mapping_type).all()
        stats['mappings_by_type'] = dict(type_counts)
        
        # Distinct traditions
        stats['source_traditions'] = [r[0] for r in db.query(
            VersificationMapping.source_tradition
        ).distinct().all()]
        
        stats['target_traditions'] = [r[0] for r in db.query(
            VersificationMapping.target_tradition
        ).distinct().all()]
        
        return stats

def find_conflicting_mappings() -> List[Dict[str, Any]]:
    """Find potentially conflicting versification mappings."""
    with get_db() as db:
        # Find cases where same source maps to different targets
        conflicts = db.query(VersificationMapping).join(
            db.query(VersificationMapping).with_entities(
                VersificationMapping.source_book,
                VersificationMapping.source_chapter,
                VersificationMapping.source_verse,
                VersificationMapping.source_tradition,
                func.count('*').label('count')
            ).group_by(
                VersificationMapping.source_book,
                VersificationMapping.source_chapter,
                VersificationMapping.source_verse,
                VersificationMapping.source_tradition
            ).having(func.count('*') > 1).subquery()
        ).all()
        
        return [{
            'source_book': m.source_book,
            'source_chapter': m.source_chapter,
            'source_verse': m.source_verse,
            'source_tradition': m.source_tradition,
            'target_book': m.target_book,
            'target_chapter': m.target_chapter,
            'target_verse': m.target_verse,
            'mapping_type': m.mapping_type
        } for m in conflicts]

def verify_mapping_chain(
    source_book: str,
    source_chapter: int,
    source_verse: int,
    from_tradition: str,
    to_tradition: str
) -> List[Dict[str, Any]]:
    """
    Verify a chain of mappings between traditions.
    Useful for checking consistency of multi-step mappings.
    """
    with get_db() as db:
        chain = []
        current = db.query(VersificationMapping).filter(
            and_(
                VersificationMapping.source_book == source_book,
                VersificationMapping.source_chapter == source_chapter,
                VersificationMapping.source_verse == source_verse,
                VersificationMapping.source_tradition == from_tradition,
                VersificationMapping.target_tradition == to_tradition
            )
        ).first()
        
        while current:
            chain.append({
                'source_book': current.source_book,
                'source_chapter': current.source_chapter,
                'source_verse': current.source_verse,
                'source_tradition': current.source_tradition,
                'target_book': current.target_book,
                'target_chapter': current.target_chapter,
                'target_verse': current.target_verse,
                'target_tradition': current.target_tradition,
                'mapping_type': current.mapping_type
            })
            
            # Look for next mapping in chain
            current = db.query(VersificationMapping).filter(
                and_(
                    VersificationMapping.source_book == current.target_book,
                    VersificationMapping.source_chapter == current.target_chapter,
                    VersificationMapping.source_verse == current.target_verse,
                    VersificationMapping.source_tradition == current.target_tradition
                )
            ).first()
        
        return chain

def get_mapping_by_reference(
    source_book: str,
    source_chapter: int,
    source_verse: int,
    source_tradition: str = "standard"
) -> Optional[Dict[str, Any]]:
    """
    Get a versification mapping by reference.
    This is an example of how SQLAlchemy can make complex queries easier.
    """
    with get_db() as db:
        result = db.execute(
            select(VersificationMapping).where(
                VersificationMapping.source_book == source_book,
                VersificationMapping.source_chapter == source_chapter,
                VersificationMapping.source_verse == source_verse,
                VersificationMapping.source_tradition == source_tradition
            )
        ).first()
        
        if result:
            mapping = result[0]
            return {
                'source_book': mapping.source_book,
                'source_chapter': mapping.source_chapter,
                'source_verse': mapping.source_verse,
                'target_book': mapping.target_book,
                'target_chapter': mapping.target_chapter,
                'target_verse': mapping.target_verse,
                'mapping_type': mapping.mapping_type,
                'notes': mapping.notes
            }
    return None

def get_tradition_info(tradition_name: str) -> Optional[Dict[str, Any]]:
    """Get information about a versification tradition."""
    with get_db() as db:
        result = db.execute(
            select(VersificationTradition).where(
                VersificationTradition.tradition_name == tradition_name
            )
        ).first()
        
        if result:
            tradition = result[0]
            return {
                'tradition_name': tradition.tradition_name,
                'description': tradition.description,
                'related_traditions': tradition.related_traditions,
                'notes': tradition.notes
            }
    return None

def get_manuscript_variations(reference: str) -> List[Dict[str, Any]]:
    """Get all manuscript variations for a given reference."""
    with get_db() as db:
        results = db.execute(
            select(ManuscriptVariation).where(
                ManuscriptVariation.reference == reference
            )
        ).all()
        
        return [{
            'reference': var[0].reference,
            'variation_type': var[0].variation_type,
            'description': var[0].description,
            'affected_traditions': var[0].affected_traditions,
            'notes': var[0].notes
        } for var in results]

def get_rules_by_type(rule_type: str) -> List[Dict[str, Any]]:
    """Get all versification rules of a specific type."""
    with get_db() as db:
        results = db.execute(
            select(VersificationRule).where(
                VersificationRule.rule_type == rule_type
            )
        ).all()
        
        return [{
            'rule_type': rule[0].rule_type,
            'content': rule[0].content,
            'section_title': rule[0].section_title,
            'applies_to': rule[0].applies_to
        } for rule in results]

def validate_mapping(mapping_data: Dict[str, Any]) -> bool:
    """
    Validate mapping data using SQLAlchemy models.
    Returns True if valid, raises ValueError if invalid.
    """
    try:
        mapping = VersificationMapping(**mapping_data)
        return True
    except Exception as e:
        raise ValueError(f"Invalid mapping data: {str(e)}")

def validate_tradition(tradition_data: Dict[str, Any]) -> bool:
    """
    Validate tradition data using SQLAlchemy models.
    Returns True if valid, raises ValueError if invalid.
    """
    try:
        tradition = VersificationTradition(**tradition_data)
        return True
    except Exception as e:
        raise ValueError(f"Invalid tradition data: {str(e)}")

# Data quality check functions
def check_mapping_consistency() -> List[Dict[str, Any]]:
    """Check for inconsistencies in versification mappings."""
    issues = []
    with get_db() as db:
        # Check for broken chains
        results = db.execute(text("""
            WITH RECURSIVE mapping_chain AS (
                SELECT source_book, source_chapter, source_verse, source_tradition,
                       target_book, target_chapter, target_verse, target_tradition,
                       ARRAY[source_tradition] as tradition_chain,
                       1 as depth
                FROM bible.versification_mappings
                UNION ALL
                SELECT m.source_book, m.source_chapter, m.source_verse, m.source_tradition,
                       m.target_book, m.target_chapter, m.target_verse, m.target_tradition,
                       tradition_chain || m.source_tradition,
                       depth + 1
                FROM bible.versification_mappings m
                JOIN mapping_chain mc ON 
                    m.source_book = mc.target_book AND
                    m.source_chapter = mc.target_chapter AND
                    m.source_verse = mc.target_verse AND
                    m.source_tradition = mc.target_tradition
                WHERE depth < 5 AND NOT m.source_tradition = ANY(tradition_chain)
            )
            SELECT * FROM mapping_chain
            WHERE target_tradition NOT IN (
                SELECT DISTINCT source_tradition FROM bible.versification_mappings
            )
        """)).all()
        
        for row in results:
            issues.append({
                'type': 'broken_chain',
                'source_book': row[0],
                'source_chapter': row[1],
                'source_verse': row[2],
                'source_tradition': row[3],
                'target_book': row[4],
                'target_chapter': row[5],
                'target_verse': row[6],
                'target_tradition': row[7],
                'tradition_chain': row[8]
            })
    
    return issues

def validate_json_field(data: Any) -> Optional[Dict]:
    """
    Validate and normalize JSON data.
    Returns None if data is invalid.
    """
    if not data:
        return None
    
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON string: {data[:100]}...")
            return None
    
    if isinstance(data, dict):
        return data
    
    return None

def batch_insert_verses(verses_data: List[Dict], session: Session) -> bool:
    """
    Insert verses in batches with proper error handling and validation.
    Returns True if successful, False otherwise.
    """
    total_verses = len(verses_data)
    inserted_count = 0
    error_count = 0
    
    try:
        for i in range(0, len(verses_data), BATCH_SIZE):
            batch = verses_data[i:i + BATCH_SIZE]
            verse_objects = []
            
            try:
                for verse_data in batch:
                    # Validate JSON fields
                    strongs_json = validate_json_field(verse_data.get('strongs_json'))
                    morphology_json = validate_json_field(verse_data.get('morphology_json'))
                    
                    # Create verse object with validated data
                    verse = Verse(
                        book_name=verse_data['book_name'],
                        chapter=verse_data['chapter'],
                        verse=verse_data['verse'],
                        word=verse_data.get('word'),
                        transliteration=verse_data.get('transliteration'),
                        strongs=verse_data.get('strongs'),
                        morphology=verse_data.get('morphology'),
                        gloss=verse_data.get('gloss'),
                        function=verse_data.get('function'),
                        root=verse_data.get('root'),
                        strongs_json=strongs_json,
                        morphology_json=morphology_json
                    )
                    verse_objects.append(verse)
                
                session.bulk_save_objects(verse_objects)
                session.flush()
                inserted_count += len(batch)
                logger.info(f"Inserted batch of {len(batch)} verses. Progress: {inserted_count}/{total_verses}")
                
            except SQLAlchemyError as e:
                session.rollback()
                error_count += len(batch)
                logger.error(f"Error in batch {i//BATCH_SIZE + 1}: {str(e)}")
                logger.error("Problem verses in this batch:")
                for verse in batch:
                    logger.error(f"{verse['book_name']} {verse['chapter']}:{verse['verse']}")
                continue
        
        # Verify all verses were inserted
        if error_count > 0:
            logger.error(f"Failed to insert {error_count} verses out of {total_verses}")
            return False
            
        # Final verification
        actual_count = session.query(Verse).count()
        if actual_count != total_verses:
            logger.error(f"Verse count mismatch. Expected: {total_verses}, Got: {actual_count}")
            return False
            
        session.commit()
        logger.info(f"Successfully inserted all {total_verses} verses")
        return True
    
    except Exception as e:
        session.rollback()
        logger.error(f"Fatal error in batch insert: {str(e)}")
        return False

def validate_data_quality(session: Session) -> Dict:
    """
    Validate data quality in the database.
    Returns a dictionary with validation results.
    """
    try:
        # Check for missing required fields
        missing_required = session.query(Verse).filter(
            or_(
                Verse.book_name.is_(None),
                Verse.chapter.is_(None),
                Verse.verse.is_(None)
            )
        ).count()
        
        # Check for invalid JSON in verses
        invalid_json = session.query(Verse).filter(
            or_(
                and_(Verse.strongs_json.isnot(None), ~Verse.strongs_json.cast(Text).regexp_match(r'^\[.*\]$')),
                and_(Verse.morphology_json.isnot(None), ~Verse.morphology_json.cast(Text).regexp_match(r'^\[.*\]$'))
            )
        ).count()
        
        # Check proper names data
        proper_names_count = session.execute(text("""
            SELECT COUNT(*) FROM bible.proper_names
            WHERE verse_id IS NOT NULL
            AND name_text IS NOT NULL
        """)).scalar()
        
        return {
            'missing_required_fields': missing_required,
            'invalid_json_count': invalid_json,
            'proper_names_count': proper_names_count
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Error in data quality validation: {str(e)}")
        return {'error': str(e)}

def cleanup_database(session: Session) -> bool:
    """
    Perform cleanup operations on the database.
    Returns True if successful, False otherwise.
    """
    try:
        # Create indexes if they don't exist
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_verses_book_chapter_verse 
            ON bible.verses (book_name, chapter, verse)
        """))
        
        # Create composite index for efficient lookups
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_verses_composite 
            ON bible.verses (book_name, chapter, verse)
        """))
        
        # Analyze tables for query optimization
        session.execute(text("ANALYZE bible.verses"))
        
        session.commit()
        return True
        
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error in database cleanup: {str(e)}")
        return False 