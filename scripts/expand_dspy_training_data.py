#!/usr/bin/env python3
"""
Expand DSPy Training Dataset

This script expands the existing DSPy training dataset with:
1. More theological terms and concepts
2. Multi-turn conversations
3. Complex semantic queries
4. Data from reliable Bible database sources

Usage:
    python scripts/expand_dspy_training_data.py --output-file data/processed/dspy_training_data/bible_corpus/dspy/expanded_bible_corpus_dataset.json
"""

import os
import sys
import json
import random
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.insert(0, project_root)

# Import database utilities
from src.database.connection import get_db_connection
from src.database.secure_connection import get_secure_connection
from src.utils.bible_reference_parser import parse_reference, extract_references

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/expand_training_dataset.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_existing_dataset(file_path: str) -> List[Dict[str, Any]]:
    """Load an existing dataset file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} examples from {file_path}")
            return data
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}. Starting with empty dataset.")
        return []
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in {file_path}. Trying as JSONL.")
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('//'):
                        data.append(json.loads(line))
            logger.info(f"Loaded {len(data)} examples from JSONL {file_path}")
            return data
        except:
            logger.error(f"Failed to load {file_path} as JSON or JSONL.")
            return []

def load_theological_terms(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load theological terms from a JSONL file or database."""
    if file_path and os.path.exists(file_path):
        terms = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('//'):
                        terms.append(json.loads(line))
            logger.info(f"Loaded {len(terms)} theological terms from {file_path}")
            return terms
        except Exception as e:
            logger.error(f"Error loading theological terms: {e}")
    
    # Fall back to database query
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Query for Hebrew terms
            cursor.execute("""
                SELECT strongs_id, lemma, transliteration, definition
                FROM bible.strongs_dictionary
                WHERE strongs_id LIKE 'H%'
                ORDER BY RANDOM()
                LIMIT 50
            """)
            hebrew_terms = [
                {
                    "strongs_id": row[0],
                    "lemma": row[1],
                    "transliteration": row[2],
                    "definition": row[3],
                    "source": "Hebrew"
                }
                for row in cursor.fetchall()
            ]
            
            # Query for Greek terms
            cursor.execute("""
                SELECT strongs_id, lemma, transliteration, definition
                FROM bible.strongs_dictionary
                WHERE strongs_id LIKE 'G%'
                ORDER BY RANDOM()
                LIMIT 50
            """)
            greek_terms = [
                {
                    "strongs_id": row[0],
                    "lemma": row[1],
                    "transliteration": row[2],
                    "definition": row[3],
                    "source": "Greek"
                }
                for row in cursor.fetchall()
            ]
            
            terms = hebrew_terms + greek_terms
            logger.info(f"Loaded {len(terms)} theological terms from database")
            return terms
    except Exception as e:
        logger.error(f"Database error loading theological terms: {e}")
        
    # Fallback to hardcoded common theological terms
    logger.warning("Using hardcoded theological terms as fallback")
    return [
        {"strongs_id": "H430", "lemma": "אֱלֹהִים", "transliteration": "Elohim", "definition": "God, gods", "source": "Hebrew"},
        {"strongs_id": "H3068", "lemma": "יְהֹוָה", "transliteration": "YHWH", "definition": "the proper name of the God of Israel", "source": "Hebrew"},
        {"strongs_id": "H2617", "lemma": "חֶסֶד", "transliteration": "Chesed", "definition": "goodness, kindness, faithfulness", "source": "Hebrew"},
        {"strongs_id": "G26", "lemma": "ἀγάπη", "transliteration": "Agape", "definition": "love, charity", "source": "Greek"},
        {"strongs_id": "G4102", "lemma": "πίστις", "transliteration": "Pistis", "definition": "faith, belief, trust, confidence", "source": "Greek"},
        {"strongs_id": "G3056", "lemma": "λόγος", "transliteration": "Logos", "definition": "word, account, speech", "source": "Greek"}
    ]

def fetch_random_verses(num_verses: int = 100) -> List[Dict[str, Any]]:
    """Fetch random verses from the database."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Get random verses across multiple translations
            cursor.execute("""
                SELECT v.id AS verse_id, v.book_name, v.chapter AS chapter_num, v.verse AS verse_num, 
                       v.word || ' ' || v.transliteration AS verse_text, 'KJV' AS translation_source
                FROM bible.verses v
                WHERE v.word IS NOT NULL
                ORDER BY RANDOM()
                LIMIT %s
            """, (num_verses,))
            
            verses = [
                {
                    "verse_id": row[0],
                    "book_name": row[1],
                    "chapter_num": row[2],
                    "verse_num": row[3],
                    "verse_text": row[4] or "Verse text not available",
                    "translation": row[5]
                }
                for row in cursor.fetchall()
            ]
            
            # If no verses found, use hardcoded examples
            if not verses:
                logger.warning("No verses found in database, using hardcoded examples")
                verses = [
                    {
                        "verse_id": 1,
                        "book_name": "Genesis",
                        "chapter_num": 1,
                        "verse_num": 1,
                        "verse_text": "In the beginning God created the heaven and the earth.",
                        "translation": "KJV"
                    },
                    {
                        "verse_id": 2,
                        "book_name": "John",
                        "chapter_num": 3,
                        "verse_num": 16,
                        "verse_text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
                        "translation": "KJV"
                    }
                ]
                # Add more hardcoded verses
                for i in range(3, 101):
                    verses.append({
                        "verse_id": i,
                        "book_name": "Psalms",
                        "chapter_num": 23,
                        "verse_num": 1,
                        "verse_text": "The LORD is my shepherd; I shall not want.",
                        "translation": "KJV"
                    })
            
            logger.info(f"Fetched {len(verses)} verses from database or hardcoded")
            return verses
    except Exception as e:
        logger.error(f"Database error fetching verses: {e}")
        
        # Return hardcoded examples in case of error
        logger.warning("Using hardcoded verse examples as fallback")
        return [
            {
                "verse_id": 1,
                "book_name": "Genesis",
                "chapter_num": 1,
                "verse_num": 1,
                "verse_text": "In the beginning God created the heaven and the earth.",
                "translation": "KJV"
            },
            {
                "verse_id": 2,
                "book_name": "John",
                "chapter_num": 3,
                "verse_num": 16,
                "verse_text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
                "translation": "KJV"
            },
            {
                "verse_id": 3,
                "book_name": "Psalms",
                "chapter_num": 23,
                "verse_num": 1,
                "verse_text": "The LORD is my shepherd; I shall not want.",
                "translation": "KJV"
            }
        ]

def generate_single_turn_qa(verses: List[Dict[str, Any]], terms: List[Dict[str, Any]], 
                           count: int = 100) -> List[Dict[str, Any]]:
    """Generate single-turn QA examples from verses and theological terms."""
    examples = []
    
    # Define question templates
    theological_templates = [
        "What is the meaning of {term} ({strongs_id}) in {reference}?",
        "How is {term} ({strongs_id}) used in {reference}?",
        "What theological significance does {term} have in {reference}?",
        "Explain the concept of {term} as it appears in {reference}.",
        "What does {term} ({strongs_id}) teach us about God in {reference}?"
    ]
    
    factual_templates = [
        "What does {reference} say?",
        "Who is mentioned in {reference}?",
        "What event is described in {reference}?",
        "What command is given in {reference}?",
        "What promise is found in {reference}?"
    ]
    
    # Generate examples
    for _ in range(count):
        verse = random.choice(verses)
        reference = f"{verse['book_name']} {verse['chapter_num']}:{verse['verse_num']}"
        
        # 70% theological questions, 30% factual questions
        if random.random() < 0.7 and terms:
            term = random.choice(terms)
            template = random.choice(theological_templates)
            question = template.format(
                term=term["transliteration"],
                strongs_id=term["strongs_id"],
                reference=reference
            )
            
            answer = f"In {reference}, {term['transliteration']} ({term['strongs_id']}) " + \
                     f"refers to {term['definition']}. " + \
                     f"The verse states: \"{verse['verse_text']}\""
        else:
            template = random.choice(factual_templates)
            question = template.format(reference=reference)
            answer = verse['verse_text']
        
        examples.append({
            "question": question,
            "context": f"{reference}: {verse['verse_text']}",
            "answer": answer
        })
    
    logger.info(f"Generated {len(examples)} single-turn QA examples")
    return examples

def generate_multi_turn_qa(verses: List[Dict[str, Any]], terms: List[Dict[str, Any]],
                          count: int = 50) -> List[Dict[str, Any]]:
    """Generate multi-turn QA examples with conversation history."""
    examples = []
    
    # Define multi-turn templates
    templates = [
        # Template 1: Term definition -> Application
        [
            {"role": "user", "content": "What does {term} ({strongs_id}) mean in Hebrew/Greek?"},
            {"role": "assistant", "content": "The term {term} ({strongs_id}) means \"{definition}\". It comes from {source}."},
            {"role": "user", "content": "How is this term used in {reference}?"}
        ],
        
        # Template 2: Verse meaning -> Theological implications
        [
            {"role": "user", "content": "What does {reference} say?"},
            {"role": "assistant", "content": "{reference} says: \"{verse_text}\""},
            {"role": "user", "content": "What does this teach us about {theological_concept}?"}
        ],
        
        # Template 3: Compare terms
        [
            {"role": "user", "content": "What is the difference between {term1} and {term2}?"},
            {"role": "assistant", "content": "{term1} ({strongs_id1}) means \"{definition1}\", while {term2} ({strongs_id2}) refers to \"{definition2}\"."},
            {"role": "user", "content": "How are both concepts present in {reference}?"}
        ]
    ]
    
    theological_concepts = [
        "God's nature", "salvation", "faith", "holiness", "grace", 
        "redemption", "covenant", "sin", "judgment", "mercy"
    ]
    
    # Generate examples
    for _ in range(count):
        verse = random.choice(verses)
        reference = f"{verse['book_name']} {verse['chapter_num']}:{verse['verse_num']}"
        
        template = random.choice(templates)
        history = []
        
        if len(template) >= 3:  # Ensure we have enough turns
            # Process the conversation turns
            term1 = random.choice(terms) if terms else {"transliteration": "Elohim", "strongs_id": "H430", "definition": "God, gods", "source": "Hebrew"}
            term2 = random.choice([t for t in terms if t != term1]) if len(terms) > 1 else {"transliteration": "YHWH", "strongs_id": "H3068", "definition": "the proper name of God", "source": "Hebrew"}
            
            # Process all but the last turn for history
            for i in range(len(template) - 1):
                turn = template[i].copy()
                # Format the content
                turn["content"] = turn["content"].format(
                    term=term1["transliteration"],
                    strongs_id=term1["strongs_id"],
                    definition=term1["definition"],
                    source=term1.get("source", "Biblical languages"),
                    reference=reference,
                    verse_text=verse["verse_text"],
                    theological_concept=random.choice(theological_concepts),
                    term1=term1["transliteration"],
                    strongs_id1=term1["strongs_id"],
                    definition1=term1["definition"],
                    term2=term2["transliteration"],
                    strongs_id2=term2["strongs_id"],
                    definition2=term2["definition"]
                )
                history.append(turn)
            
            # Format the last turn as the current question
            question = template[-1]["content"].format(
                term=term1["transliteration"],
                strongs_id=term1["strongs_id"],
                reference=reference,
                theological_concept=random.choice(theological_concepts),
                term1=term1["transliteration"],
                term2=term2["transliteration"]
            )
            
            # Generate an appropriate answer
            if "How is this term used in" in question:
                answer = f"In {reference}, {term1['transliteration']} ({term1['strongs_id']}) illustrates {term1['definition']} " + \
                         f"as seen in the context: \"{verse['verse_text']}\""
            elif "What does this teach us about" in question:
                concept = question.split("about ")[1].rstrip("?")
                answer = f"{reference} teaches us about {concept} by showing that {verse['verse_text']} " + \
                         f"This demonstrates God's character and purpose."
            elif "How are both concepts present" in question:
                answer = f"In {reference}, both {term1['transliteration']} ({term1['strongs_id']}) and " + \
                         f"{term2['transliteration']} ({term2['strongs_id']}) are present. " + \
                         f"The verse states: \"{verse['verse_text']}\" " + \
                         f"This shows how these concepts work together in Scripture."
            else:
                answer = f"Based on {reference}, which says \"{verse['verse_text']}\", " + \
                         f"we can understand this concept better."
            
            # Create the example
            examples.append({
                "question": question,
                "context": f"{reference}: {verse['verse_text']}",
                "answer": answer,
                "history": history
            })
    
    logger.info(f"Generated {len(examples)} multi-turn QA examples")
    return examples

def generate_cross_reference_qa(verses: List[Dict[str, Any]], count: int = 50) -> List[Dict[str, Any]]:
    """Generate QA examples that involve cross-referencing multiple passages."""
    examples = []
    
    if len(verses) < 20:
        logger.warning("Not enough verses to generate cross-reference examples")
        return examples
    
    # Define cross-reference templates
    templates = [
        "How does {reference1} relate to the teaching in {reference2}?",
        "Compare and contrast {reference1} with {reference2}.",
        "What common themes are found in {reference1} and {reference2}?",
        "How do {reference1} and {reference2} together help us understand {topic}?",
        "What theological connection exists between {reference1} and {reference2}?"
    ]
    
    topics = [
        "salvation", "God's character", "faith", "holiness", "covenant", 
        "sin and redemption", "prayer", "worship", "biblical leadership", "the Holy Spirit"
    ]
    
    # Generate examples
    for _ in range(count):
        # Pick two different verses
        verse1 = random.choice(verses)
        verse2 = random.choice([v for v in verses if v != verse1])
        
        reference1 = f"{verse1['book_name']} {verse1['chapter_num']}:{verse1['verse_num']}"
        reference2 = f"{verse2['book_name']} {verse2['chapter_num']}:{verse2['verse_num']}"
        
        template = random.choice(templates)
        topic = random.choice(topics)
        
        question = template.format(
            reference1=reference1,
            reference2=reference2,
            topic=topic
        )
        
        context = f"{reference1}: {verse1['verse_text']}\n\n{reference2}: {verse2['verse_text']}"
        
        answer = f"When comparing {reference1} and {reference2}, we see that:\n\n" + \
                 f"1. {reference1} states: \"{verse1['verse_text']}\"\n" + \
                 f"2. {reference2} states: \"{verse2['verse_text']}\"\n\n" + \
                 f"These passages relate to each other through their shared focus on {topic}. " + \
                 f"They complement each other by providing different perspectives on this important biblical theme."
        
        examples.append({
            "question": question,
            "context": context,
            "answer": answer
        })
    
    logger.info(f"Generated {len(examples)} cross-reference QA examples")
    return examples

def generate_theological_concept_qa(terms: List[Dict[str, Any]], count: int = 50) -> List[Dict[str, Any]]:
    """Generate QA examples focusing on theological concepts without specific verses."""
    examples = []
    
    # Define theological concept templates
    templates = [
        "What is the biblical meaning of {term}?",
        "Explain the theological concept of {term} ({strongs_id}).",
        "What does {term} ({strongs_id}) teach us about God's character?",
        "How is {term} important in biblical theology?",
        "What are the key aspects of {term} in the Bible?"
    ]
    
    # Generate examples
    for _ in range(count):
        if not terms:
            break
            
        term = random.choice(terms)
        template = random.choice(templates)
        
        question = template.format(
            term=term["transliteration"],
            strongs_id=term["strongs_id"]
        )
        
        answer = f"The term {term['transliteration']} ({term['strongs_id']}) refers to {term['definition']}. " + \
                 f"This concept is important in biblical theology because it reveals aspects of God's character " + \
                 f"and His relationship with humanity. Understanding {term['transliteration']} helps us " + \
                 f"interpret Scripture more accurately and apply its teachings in our lives."
        
        examples.append({
            "question": question,
            "context": f"Theological term: {term['transliteration']} ({term['strongs_id']}): {term['definition']}",
            "answer": answer
        })
    
    logger.info(f"Generated {len(examples)} theological concept QA examples")
    return examples

def save_dataset(examples: List[Dict[str, Any]], output_file: str, format: str = "json"):
    """Save the dataset to a file in the specified format."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    if format.lower() == "jsonl":
        with open(output_file, 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example) + "\n")
    else:  # Default to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(examples, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(examples)} examples to {output_file}")

def main():
    """Main function to parse arguments and run the dataset expansion."""
    parser = argparse.ArgumentParser(description="Expand DSPy training dataset")
    parser.add_argument(
        "--input-file", 
        default="data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json",
        help="Input dataset file path"
    )
    parser.add_argument(
        "--theological-terms-file", 
        default="data/processed/dspy_training_data/theological_terms_dataset.jsonl",
        help="Theological terms dataset file path"
    )
    parser.add_argument(
        "--output-file", 
        default="data/processed/dspy_training_data/bible_corpus/dspy/expanded_bible_corpus_dataset.json",
        help="Output file path for expanded dataset"
    )
    parser.add_argument(
        "--format", 
        choices=["json", "jsonl"], 
        default="json",
        help="Output file format (json or jsonl)"
    )
    parser.add_argument(
        "--num-single-turn", 
        type=int, 
        default=100,
        help="Number of single-turn QA examples to generate"
    )
    parser.add_argument(
        "--num-multi-turn", 
        type=int, 
        default=50,
        help="Number of multi-turn QA examples to generate"
    )
    parser.add_argument(
        "--num-cross-reference", 
        type=int, 
        default=50,
        help="Number of cross-reference QA examples to generate"
    )
    parser.add_argument(
        "--num-theological", 
        type=int, 
        default=50,
        help="Number of theological concept QA examples to generate"
    )
    parser.add_argument(
        "--num-verses", 
        type=int, 
        default=200,
        help="Number of verses to fetch from database"
    )
    
    args = parser.parse_args()
    
    # Load existing dataset
    existing_data = load_existing_dataset(args.input_file)
    
    # Load theological terms
    terms = load_theological_terms(args.theological_terms_file)
    
    # Fetch random verses
    verses = fetch_random_verses(args.num_verses)
    
    if not verses:
        logger.error("Failed to fetch verses from database. Exiting.")
        return 1
    
    # Generate new examples
    single_turn_examples = generate_single_turn_qa(
        verses, terms, count=args.num_single_turn
    )
    
    multi_turn_examples = generate_multi_turn_qa(
        verses, terms, count=args.num_multi_turn
    )
    
    cross_reference_examples = generate_cross_reference_qa(
        verses, count=args.num_cross_reference
    )
    
    theological_examples = generate_theological_concept_qa(
        terms, count=args.num_theological
    )
    
    # Combine all examples
    all_examples = existing_data + single_turn_examples + multi_turn_examples + \
                  cross_reference_examples + theological_examples
    
    # Remove duplicates based on question text
    seen_questions = set()
    unique_examples = []
    
    for example in all_examples:
        if example["question"] not in seen_questions:
            seen_questions.add(example["question"])
            unique_examples.append(example)
    
    # Save the expanded dataset
    save_dataset(unique_examples, args.output_file, args.format)
    
    # Stats
    new_examples = len(unique_examples) - len(existing_data)
    logger.info(f"Added {new_examples} new examples, total: {len(unique_examples)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 