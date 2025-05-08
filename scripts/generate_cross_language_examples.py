#!/usr/bin/env python
"""
Script to generate cross-language concept examples for Bible QA training data.
This script creates question-answer pairs connecting Hebrew, Greek, and Arabic theological concepts.

Usage:
    python scripts/generate_cross_language_examples.py --output-file data/processed/bible_training_data/cross_language_train.jsonl --num-examples 50
"""

import argparse
import json
import logging
import os
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/cross_language_examples.log", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import database connection
try:
    from src.database.secure_connection import get_secure_connection
    logger.info("Using secure_connection for database access")
except ImportError:
    logger.warning("Could not import secure_connection, falling back to direct connection")
    
    def get_secure_connection(mode='read'):
        """Fallback connection method"""
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "bible_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "")
        )

# Define cross-language theological concepts
CROSS_LANGUAGE_CONCEPTS = [
    {
        "concept": "God",
        "hebrew_terms": ["H430", "H3068", "H410"],  # Elohim, YHWH, El
        "greek_terms": ["G2316", "G2962"],          # Theos, Kyrios
        "key_verses": ["Genesis 1:1", "John 1:1", "Psalm 23:1"]
    },
    {
        "concept": "Love",
        "hebrew_terms": ["H157", "H160"],           # Ahav, Ahavah
        "greek_terms": ["G26", "G25"],              # Agape, Agapao
        "key_verses": ["1 Corinthians 13:4", "Deuteronomy 6:5", "John 3:16"]
    },
    {
        "concept": "Faith",
        "hebrew_terms": ["H539"],                   # Aman
        "greek_terms": ["G4102", "G4100"],          # Pistis, Pisteuo
        "key_verses": ["Hebrews 11:1", "Genesis 15:6", "Romans 10:17"]
    },
    {
        "concept": "Righteousness",
        "hebrew_terms": ["H6662", "H6664"],         # Tsaddiq, Tsedeq
        "greek_terms": ["G1343", "G1342"],          # Dikaiosyne, Dikaios
        "key_verses": ["Genesis 15:6", "Romans 3:22", "Matthew 5:6"]
    },
    {
        "concept": "Salvation",
        "hebrew_terms": ["H3444", "H3467"],         # Yeshuah, Yasha
        "greek_terms": ["G4991", "G4982"],          # Soteria, Sozo
        "key_verses": ["Acts 4:12", "Isaiah 12:2", "Romans 10:9"]
    },
    {
        "concept": "Spirit",
        "hebrew_terms": ["H7307"],                  # Ruach
        "greek_terms": ["G4151"],                   # Pneuma
        "key_verses": ["Genesis 1:2", "John 4:24", "Romans 8:16"]
    },
    {
        "concept": "Sin",
        "hebrew_terms": ["H2398", "H2403"],         # Chata, Chataat
        "greek_terms": ["G266", "G264"],            # Hamartia, Hamartano
        "key_verses": ["Romans 3:23", "Genesis 4:7", "1 John 1:8"]
    },
    {
        "concept": "Mercy",
        "hebrew_terms": ["H2617", "H7355"],         # Chesed, Racham
        "greek_terms": ["G1656", "G3628"],          # Eleos, Oiktirmos
        "key_verses": ["Psalm 103:8", "Titus 3:5", "Luke 6:36"]
    },
    {
        "concept": "Redemption",
        "hebrew_terms": ["H1350", "H6299"],         # Gaal, Padah
        "greek_terms": ["G629", "G3084"],           # Apolytrosis, Lytrosis
        "key_verses": ["Ephesians 1:7", "Ruth 4:7", "Exodus 6:6"]
    },
    {
        "concept": "Grace",
        "hebrew_terms": ["H2580"],                  # Chen
        "greek_terms": ["G5485"],                   # Charis
        "key_verses": ["Ephesians 2:8", "Genesis 6:8", "John 1:16"]
    }
]

def get_term_data(conn, strongs_id: str) -> Dict[str, Any]:
    """
    Get data for a specific Strong's ID.
    
    Args:
        conn: Database connection
        strongs_id: Strong's ID to look up
        
    Returns:
        Dictionary with term data
    """
    term_data = {}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            if strongs_id.startswith('H'):
                cursor.execute("""
                    SELECT strongs_id, hebrew_word as term, transliteration, definition, gloss
                    FROM bible.hebrew_entries
                    WHERE strongs_id = %s
                """, (strongs_id,))
                
                row = cursor.fetchone()
                if row:
                    term_data = {
                        'strongs_id': row['strongs_id'],
                        'term': row['term'],
                        'transliteration': row['transliteration'],
                        'definition': row['definition'],
                        'gloss': row['gloss'],
                        'language': 'Hebrew'
                    }
            else:
                cursor.execute("""
                    SELECT strongs_id, greek_word as term, transliteration, definition, gloss
                    FROM bible.greek_entries
                    WHERE strongs_id = %s
                """, (strongs_id,))
                
                row = cursor.fetchone()
                if row:
                    term_data = {
                        'strongs_id': row['strongs_id'],
                        'term': row['term'],
                        'transliteration': row['transliteration'],
                        'definition': row['definition'],
                        'gloss': row['gloss'],
                        'language': 'Greek'
                    }
    except Exception as e:
        logger.error(f"Error fetching term data for {strongs_id}: {str(e)}")
    
    return term_data

def get_arabic_term(conn, concept: str) -> Optional[Dict[str, str]]:
    """
    Try to find an Arabic term matching the given concept.
    
    Args:
        conn: Database connection
        concept: Theological concept to match
        
    Returns:
        Dictionary with Arabic term data or None
    """
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # Try to find from cross_language_terms
            cursor.execute("""
                SELECT arabic_term, notes
                FROM bible.cross_language_terms
                WHERE theological_category ILIKE %s
            """, (f"%{concept}%",))
            
            row = cursor.fetchone()
            if row and row['arabic_term']:
                return {
                    'term': row['arabic_term'],
                    'notes': row['notes'] if row['notes'] else '',
                    'source': 'cross_language_terms'
                }
            
            # If not found, try to find from arabic_words linked to a relevant Strong's ID
            # This is an approximation and would need refinement in a real implementation
            cursor.execute("""
                SELECT DISTINCT aw.arabic_word, aw.transliteration, aw.gloss
                FROM bible.arabic_words aw
                JOIN bible.verses v ON aw.verse_id = v.id
                WHERE aw.gloss ILIKE %s
                LIMIT 1
            """, (f"%{concept}%",))
            
            row = cursor.fetchone()
            if row:
                return {
                    'term': row['arabic_word'],
                    'transliteration': row['transliteration'] if row['transliteration'] else '',
                    'gloss': row['gloss'] if row['gloss'] else '',
                    'source': 'arabic_words'
                }
    except Exception as e:
        logger.error(f"Error fetching Arabic term for concept {concept}: {str(e)}")
    
    return None

def get_verse_text(conn, reference: str) -> Optional[Dict[str, str]]:
    """
    Get verse text for a given reference.
    
    Args:
        conn: Database connection
        reference: Verse reference (e.g., "John 3:16")
        
    Returns:
        Dictionary with verse data or None
    """
    try:
        # Parse reference
        parts = reference.split()
        book = " ".join(parts[:-1])
        chapter_verse = parts[-1].split(":")
        chapter = int(chapter_verse[0])
        verse = int(chapter_verse[1])
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT verse_text, translation_source
                FROM bible.verses
                WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
                AND translation_source = 'KJV'
            """, (book, chapter, verse))
            
            row = cursor.fetchone()
            if row:
                return {
                    'reference': reference,
                    'text': row['verse_text'],
                    'translation': row['translation_source']
                }
    except Exception as e:
        logger.error(f"Error fetching verse text for {reference}: {str(e)}")
    
    return None

def generate_concept_example(conn, concept_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a cross-language concept example.
    
    Args:
        conn: Database connection
        concept_data: Dictionary with concept information
        
    Returns:
        Dictionary with example data
    """
    concept = concept_data["concept"]
    hebrew_terms_ids = concept_data["hebrew_terms"]
    greek_terms_ids = concept_data["greek_terms"]
    key_verses_refs = concept_data["key_verses"]
    
    # Get Hebrew term data
    hebrew_terms = []
    for strongs_id in hebrew_terms_ids:
        term_data = get_term_data(conn, strongs_id)
        if term_data:
            hebrew_terms.append(term_data)
    
    # Get Greek term data
    greek_terms = []
    for strongs_id in greek_terms_ids:
        term_data = get_term_data(conn, strongs_id)
        if term_data:
            greek_terms.append(term_data)
    
    # Get Arabic term
    arabic_term = get_arabic_term(conn, concept)
    
    # Get verse texts
    verses = []
    for reference in key_verses_refs:
        verse_data = get_verse_text(conn, reference)
        if verse_data:
            verses.append(verse_data)
    
    # Generate question types
    question_types = [
        f"How is the concept of '{concept}' expressed in Hebrew, Greek, and Arabic?",
        f"Compare the Hebrew and Greek terms for '{concept}' in the Bible.",
        f"What are the key biblical terms for '{concept}' across different languages?",
        f"Explain the linguistic and theological nuances of '{concept}' in biblical languages."
    ]
    
    # Construct answer
    answer_parts = []
    
    answer_parts.append(f"The concept of '{concept}' is expressed through several key terms in biblical languages:")
    
    if hebrew_terms:
        answer_parts.append("\nIn Hebrew:")
        for term in hebrew_terms:
            term_str = term['term'] if term['term'] else ''
            trans_str = f" ({term['transliteration']})" if term.get('transliteration') else ''
            gloss_str = f" - {term['gloss']}" if term.get('gloss') else ''
            strongs_str = f" [{term['strongs_id']}]" if term.get('strongs_id') else ''
            
            answer_parts.append(f"• {term_str}{trans_str}{gloss_str}{strongs_str}: {term['definition']}")
    
    if greek_terms:
        answer_parts.append("\nIn Greek:")
        for term in greek_terms:
            term_str = term['term'] if term['term'] else ''
            trans_str = f" ({term['transliteration']})" if term.get('transliteration') else ''
            gloss_str = f" - {term['gloss']}" if term.get('gloss') else ''
            strongs_str = f" [{term['strongs_id']}]" if term.get('strongs_id') else ''
            
            answer_parts.append(f"• {term_str}{trans_str}{gloss_str}{strongs_str}: {term['definition']}")
    
    if arabic_term:
        answer_parts.append("\nIn Arabic:")
        term_str = arabic_term['term'] if arabic_term['term'] else ''
        trans_str = f" ({arabic_term['transliteration']})" if arabic_term.get('transliteration') else ''
        gloss_str = f" - {arabic_term['gloss']}" if arabic_term.get('gloss') else ''
        
        answer_parts.append(f"• {term_str}{trans_str}{gloss_str}")
        
        if arabic_term.get('notes'):
            answer_parts.append(f"  {arabic_term['notes']}")
    
    if verses:
        answer_parts.append("\nKey Biblical passages:")
        for verse in verses:
            answer_parts.append(f"• {verse['reference']}: \"{verse['text']}\"")
    
    answer = "\n".join(answer_parts)
    
    # Format context
    context_parts = []
    
    if hebrew_terms:
        for term in hebrew_terms:
            context_parts.append(f"Hebrew term: {term['term']} ({term['strongs_id']}): {term['definition']}")
    
    if greek_terms:
        for term in greek_terms:
            context_parts.append(f"Greek term: {term['term']} ({term['strongs_id']}): {term['definition']}")
    
    if verses:
        for verse in verses:
            context_parts.append(f"{verse['reference']}: {verse['text']}")
    
    context = "\n".join(context_parts)
    
    # Build metadata
    metadata = {
        "concept": concept,
        "hebrew_terms": [term.get('strongs_id') for term in hebrew_terms if term.get('strongs_id')],
        "greek_terms": [term.get('strongs_id') for term in greek_terms if term.get('strongs_id')],
        "has_arabic": arabic_term is not None,
        "key_verses": [verse.get('reference') for verse in verses if verse.get('reference')],
        "category": "cross_language_concept"
    }
    
    # Create example
    return {
        "question": random.choice(question_types),
        "context": context,
        "answer": answer,
        "metadata": metadata
    }

def generate_examples(output_file: str, num_examples: int = 50, verbose: bool = False) -> None:
    """
    Generate cross-language concept examples and save to output file.
    
    Args:
        output_file: Path to save generated examples
        num_examples: Number of examples to generate
        verbose: Whether to print detailed information
    """
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_secure_connection(mode='read')
    examples = []
    
    try:
        # Calculate how many examples to generate per concept
        num_concepts = len(CROSS_LANGUAGE_CONCEPTS)
        examples_per_concept = max(1, num_examples // num_concepts)
        
        if verbose:
            logger.info(f"Generating approximately {examples_per_concept} examples per concept")
        
        # Generate examples for each concept
        for concept_data in CROSS_LANGUAGE_CONCEPTS:
            concept = concept_data["concept"]
            
            if verbose:
                logger.info(f"Generating examples for concept: {concept}")
            
            for _ in range(examples_per_concept):
                example = generate_concept_example(conn, concept_data)
                if example:
                    examples.append(example)
                    
                    if verbose and len(examples) % 5 == 0:
                        logger.info(f"Generated {len(examples)} examples so far")
            
            # Break if we've generated enough examples
            if len(examples) >= num_examples:
                break
        
        # Fill in with random concepts if needed
        while len(examples) < num_examples:
            concept_data = random.choice(CROSS_LANGUAGE_CONCEPTS)
            example = generate_concept_example(conn, concept_data)
            if example:
                examples.append(example)
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
                
        logger.info(f"Generated {len(examples)} cross-language concept examples and saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error generating cross-language concept examples: {str(e)}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Generate cross-language concept examples for Bible QA training")
    parser.add_argument('--output-file', default='data/processed/bible_training_data/cross_language_train.jsonl',
                        help='Path to save generated examples')
    parser.add_argument('--num-examples', type=int, default=50,
                        help='Number of examples to generate')
    parser.add_argument('--verbose', action='store_true',
                        help='Print detailed information')
    args = parser.parse_args()
    
    generate_examples(args.output_file, args.num_examples, args.verbose)

if __name__ == "__main__":
    main() 