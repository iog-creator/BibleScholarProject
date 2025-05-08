#!/usr/bin/env python
"""
Script to generate theological term examples for Bible QA training data.
This script creates question-answer pairs focused on theological terms from Hebrew and Greek lexicons.

Usage:
    python scripts/generate_theological_term_examples.py --output-file data/processed/bible_training_data/theological_terms_train.jsonl --num-examples 100
"""

import argparse
import json
import logging
import os
import random
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/theological_term_examples.log", mode="a"),
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

def get_hebrew_terms(conn, term_ids: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Get Hebrew terms from the database.
    
    Args:
        conn: Database connection
        term_ids: List of Hebrew Strong's IDs
        
    Returns:
        Dictionary mapping Strong's IDs to term data
    """
    hebrew_data = {}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT strongs_id, hebrew_word, definition, gloss, transliteration
                FROM bible.hebrew_entries
                WHERE strongs_id IN %s
            """, (tuple(term_ids),))
            
            for row in cursor.fetchall():
                hebrew_data[row['strongs_id']] = {
                    'term': row['hebrew_word'],
                    'definition': row['definition'],
                    'gloss': row['gloss'],
                    'transliteration': row['transliteration'],
                    'language': 'Hebrew'
                }
    except Exception as e:
        logger.error(f"Error fetching Hebrew terms: {str(e)}")
    
    return hebrew_data

def get_greek_terms(conn, term_ids: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Get Greek terms from the database.
    
    Args:
        conn: Database connection
        term_ids: List of Greek Strong's IDs
        
    Returns:
        Dictionary mapping Strong's IDs to term data
    """
    greek_data = {}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT strongs_id, greek_word, definition, gloss, transliteration
                FROM bible.greek_entries
                WHERE strongs_id IN %s
            """, (tuple(term_ids),))
            
            for row in cursor.fetchall():
                greek_data[row['strongs_id']] = {
                    'term': row['greek_word'],
                    'definition': row['definition'],
                    'gloss': row['gloss'],
                    'transliteration': row['transliteration'],
                    'language': 'Greek'
                }
    except Exception as e:
        logger.error(f"Error fetching Greek terms: {str(e)}")
    
    return greek_data

def get_term_verses(conn, strongs_id: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Get Bible verses containing the given Strong's ID.
    
    Args:
        conn: Database connection
        strongs_id: Strong's ID to search for
        limit: Maximum number of verses to return
        
    Returns:
        List of verse dictionaries
    """
    verses = []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            if strongs_id.startswith('H'):
                # Use a subquery with DISTINCT ON to get random verses for a term
                cursor.execute("""
                    SELECT v.book_name, v.chapter_num, v.verse_num, v.verse_text, v.translation_source
                    FROM (
                        SELECT DISTINCT ON (hw.book_name, hw.chapter_num, hw.verse_num) 
                            hw.book_name, hw.chapter_num, hw.verse_num
                        FROM bible.hebrew_ot_words hw
                        WHERE hw.strongs_id = %s
                        ORDER BY hw.book_name, hw.chapter_num, hw.verse_num, random()
                        LIMIT %s
                    ) AS random_verses
                    JOIN bible.verses v ON 
                        random_verses.book_name = v.book_name AND 
                        random_verses.chapter_num = v.chapter_num AND 
                        random_verses.verse_num = v.verse_num
                    WHERE v.translation_source = 'KJV'
                """, (strongs_id, limit))
            else:
                # Use a subquery with DISTINCT ON to get random verses for a term
                cursor.execute("""
                    SELECT v.book_name, v.chapter_num, v.verse_num, v.verse_text, v.translation_source
                    FROM (
                        SELECT DISTINCT ON (gw.book_name, gw.chapter_num, gw.verse_num) 
                            gw.book_name, gw.chapter_num, gw.verse_num
                        FROM bible.greek_nt_words gw
                        WHERE gw.strongs_id = %s
                        ORDER BY gw.book_name, gw.chapter_num, gw.verse_num, random()
                        LIMIT %s
                    ) AS random_verses
                    JOIN bible.verses v ON 
                        random_verses.book_name = v.book_name AND 
                        random_verses.chapter_num = v.chapter_num AND 
                        random_verses.verse_num = v.verse_num
                    WHERE v.translation_source = 'KJV'
                """, (strongs_id, limit))
            
            for row in cursor.fetchall():
                verses.append({
                    'reference': f"{row['book_name']} {row['chapter_num']}:{row['verse_num']}",
                    'text': row['verse_text'],
                    'translation': row['translation_source']
                })
    except Exception as e:
        logger.error(f"Error fetching verses for {strongs_id}: {str(e)}")
    
    return verses

def generate_question(term_data: Dict[str, str], context_verses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a theological term question.
    
    Args:
        term_data: Dictionary with term information
        context_verses: List of verses containing the term
        
    Returns:
        Dictionary with question, answer, and metadata
    """
    strongs_id = term_data.get('strongs_id', '')
    term = term_data.get('term', '')
    gloss = term_data.get('gloss', '')
    transliteration = term_data.get('transliteration', '')
    language = term_data.get('language', '')
    definition = term_data.get('definition', '')
    
    # Generate display term
    display_term = term
    if transliteration:
        display_term = f"{transliteration} ({term})"
    elif term:
        display_term = term
    else:
        display_term = gloss
    
    # Generate question types
    question_types = [
        f"What is the meaning of {display_term} ({strongs_id}) in the Bible?",
        f"Explain the theological significance of {gloss} ({strongs_id}) in {language}.",
        f"How is {display_term} ({strongs_id}) used in Biblical context?",
        f"What is the definition of the {language} word {display_term} ({strongs_id})?"
    ]
    
    # Format verse context
    context = []
    verse_references = []
    
    for verse in context_verses:
        context.append(f"{verse['reference']}: {verse['text']}")
        verse_references.append(verse['reference'])
    
    context_str = "\n".join(context)
    
    # Generate example
    return {
        "question": random.choice(question_types),
        "context": context_str,
        "answer": definition,
        "metadata": {
            "strongs_id": strongs_id,
            "language": language,
            "verses": verse_references,
            "category": "theological_term"
        }
    }

def generate_examples(output_file: str, num_examples: int = 100, verbose: bool = False) -> None:
    """
    Generate theological term examples and save to output file.
    
    Args:
        output_file: Path to save generated examples
        num_examples: Number of examples to generate
        verbose: Whether to print detailed information
    """
    # Important Hebrew theological terms
    hebrew_terms = [
        'H430',   # Elohim (God)
        'H3068',  # YHWH (LORD)
        'H2617',  # Hesed (lovingkindness)
        'H539',   # Aman (believe, faithful)
        'H7225',  # Reshith (beginning)
        'H1818',  # Dam (blood)
        'H5315',  # Nephesh (soul)
        'H3722',  # Kaphar (atonement)
        'H6662',  # Tsaddiq (righteous)
        'H1285'   # Berith (covenant)
    ]
    
    # Important Greek theological terms
    greek_terms = [
        'G26',    # Agape (love)
        'G5485',  # Charis (grace)
        'G4102',  # Pistis (faith)
        'G1680',  # Elpis (hope)
        'G40',    # Hagios (holy)
        'G3056',  # Logos (word)
        'G1343',  # Dikaiosyne (righteousness)
        'G3952',  # Parousia (coming)
        'G4991',  # Soteria (salvation)
        'G1391'   # Doxa (glory)
    ]
    
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_secure_connection(mode='read')
    examples = []
    
    try:
        # Get term data
        hebrew_data = get_hebrew_terms(conn, hebrew_terms)
        greek_data = get_greek_terms(conn, greek_terms)
        
        if verbose:
            logger.info(f"Retrieved {len(hebrew_data)} Hebrew terms and {len(greek_data)} Greek terms")
        
        # Add Strong's IDs to term data
        for strongs_id, data in hebrew_data.items():
            data['strongs_id'] = strongs_id
        
        for strongs_id, data in greek_data.items():
            data['strongs_id'] = strongs_id
        
        # Generate examples
        for _ in range(num_examples):
            # Randomly choose Hebrew or Greek
            if random.random() < 0.5 and hebrew_data:
                strongs_id = random.choice(list(hebrew_data.keys()))
                term_data = hebrew_data[strongs_id]
            elif greek_data:
                strongs_id = random.choice(list(greek_data.keys()))
                term_data = greek_data[strongs_id]
            else:
                logger.error("No term data available")
                continue
            
            # Get verses containing the term
            verses = get_term_verses(conn, strongs_id, limit=3)
            
            if not verses:
                if verbose:
                    logger.warning(f"No verses found for term {strongs_id}")
                continue
            
            # Generate question
            example = generate_question(term_data, verses)
            examples.append(example)
            
            if verbose and len(examples) % 10 == 0:
                logger.info(f"Generated {len(examples)} examples so far")
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
                
        logger.info(f"Generated {len(examples)} theological term examples and saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error generating theological term examples: {str(e)}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Generate theological term examples for Bible QA training")
    parser.add_argument('--output-file', default='data/processed/bible_training_data/theological_terms_train.jsonl',
                        help='Path to save generated examples')
    parser.add_argument('--num-examples', type=int, default=100,
                        help='Number of examples to generate')
    parser.add_argument('--verbose', action='store_true',
                        help='Print detailed information')
    args = parser.parse_args()
    
    generate_examples(args.output_file, args.num_examples, args.verbose)

if __name__ == "__main__":
    main() 