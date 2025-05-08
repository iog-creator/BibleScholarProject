#!/usr/bin/env python3
"""
Expand Validation Dataset for Bible QA

This script expands the validation dataset for Bible QA by:
1. Adding diverse theological questions
2. Creating multi-turn conversation examples
3. Ensuring coverage of Strong's IDs and theological terms
4. Balancing factual and interpretive questions

Usage:
    python scripts/expand_validation_dataset.py --output-file "data/processed/dspy_training_data/bible_corpus/integrated/qa_dataset_val.jsonl" --num-single 40 --num-multi 10
"""

import os
import sys
import json
import logging
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/validation_expansion.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Add directory to path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import database utilities
try:
    from src.database.db_utils import get_connection
    DB_UTILS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import db_utils: {e}")
    DB_UTILS_AVAILABLE = False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Expand validation dataset for Bible QA")
    parser.add_argument(
        "--output-file",
        type=str,
        default="data/processed/dspy_training_data/bible_corpus/integrated/qa_dataset_val.jsonl",
        help="Path to output validation JSONL file"
    )
    parser.add_argument(
        "--theological-file",
        type=str,
        default="data/processed/dspy_training_data/theological_terms_dataset.jsonl",
        help="Path to theological terms dataset JSONL file"
    )
    parser.add_argument(
        "--corpus-file",
        type=str,
        default="data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json",
        help="Path to combined Bible corpus dataset JSON file"
    )
    parser.add_argument(
        "--num-single",
        type=int,
        default=40,
        help="Number of single-turn QA pairs to generate"
    )
    parser.add_argument(
        "--num-multi",
        type=int,
        default=10,
        help="Number of multi-turn conversation examples to generate"
    )
    parser.add_argument(
        "--sample-theological",
        action="store_true",
        help="Use sample theological terms if none are found"
    )
    return parser.parse_args()

def load_existing_dataset(file_path: str) -> List[Dict[str, Any]]:
    """Load existing validation dataset if it exists."""
    if not os.path.exists(file_path):
        logger.info(f"No existing dataset found at {file_path}")
        return []
    
    try:
        examples = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('//'):
                    examples.append(json.loads(line))
        
        logger.info(f"Loaded {len(examples)} existing examples from {file_path}")
        return examples
    
    except Exception as e:
        logger.error(f"Error loading existing dataset: {e}")
        return []

def load_theological_terms(file_path: str) -> List[Dict[str, Any]]:
    """Load theological terms dataset."""
    # Fix path if needed
    if not os.path.exists(file_path):
        # Try absolute path with project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abs_path = os.path.join(project_root, "data/processed/dspy_training_data/theological_terms_dataset.jsonl")
        
        if os.path.exists(abs_path):
            file_path = abs_path
            logger.info(f"Using absolute path for theological terms: {file_path}")
        else:
            # Try alternative relative paths
            alt_paths = [
                "../data/processed/dspy_training_data/theological_terms_dataset.jsonl",
                "../../data/processed/dspy_training_data/theological_terms_dataset.jsonl",
                "../theological_terms_dataset.jsonl"
            ]
            
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    file_path = alt_path
                    logger.info(f"Using alternative path for theological terms: {file_path}")
                    break
            else:
                logger.error(f"Cannot find theological terms dataset at any location")
                return []
    
    try:
        terms = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('//'):
                    terms.append(json.loads(line))
        
        logger.info(f"Loaded {len(terms)} theological terms from {file_path}")
        return terms
    
    except Exception as e:
        logger.error(f"Error loading theological terms: {e}")
        return []

def load_corpus_dataset(file_path: str) -> List[Dict[str, Any]]:
    """Load the combined Bible corpus dataset."""
    # Try to find the corpus file
    if not os.path.exists(file_path):
        # Try absolute path with project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Try QA dataset instead
        qa_path_abs = os.path.join(project_root, "data/processed/dspy_training_data/qa_dataset.jsonl")
        if os.path.exists(qa_path_abs):
            file_path = qa_path_abs
            logger.info(f"Using absolute path for QA dataset: {file_path}")
            # Try to load as JSONL
            try:
                data = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('//'):
                            data.append(json.loads(line))
                logger.info(f"Loaded {len(data)} examples from QA dataset at {file_path}")
                return data
            except Exception as e:
                logger.error(f"Error loading QA dataset: {e}")
                
        # Try conversation history dataset as another fallback
        conv_path_abs = os.path.join(project_root, "data/processed/dspy_training_data/conversation_history_dataset.jsonl")
        if os.path.exists(conv_path_abs):
            file_path = conv_path_abs
            logger.info(f"Using conversation history dataset: {file_path}")
            # Try to load as JSONL
            try:
                data = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('//'):
                            data.append(json.loads(line))
                logger.info(f"Loaded {len(data)} examples from conversation history dataset at {file_path}")
                return data
            except Exception as e:
                logger.error(f"Error loading conversation history dataset: {e}")
        
        # If all else fails, create some synthetic examples
        logger.warning("No corpus dataset found, creating synthetic examples")
        return [
            {
                "context": "Genesis 1:1 In the beginning God created the heavens and the earth.",
                "question": "What did God create in the beginning?",
                "answer": "God created the heavens and the earth in the beginning.",
                "metadata": {"book": "Genesis", "chapter": 1, "verse": 1, "translation": "KJV"}
            },
            {
                "context": "John 3:16 For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.",
                "question": "What did God give because of his love for the world?",
                "answer": "God gave his one and only Son.",
                "metadata": {"book": "John", "chapter": 3, "verse": 16, "translation": "NIV"}
            },
            {
                "context": "Psalm 23:1 The LORD is my shepherd, I shall not want.",
                "question": "Who is the psalmist's shepherd?",
                "answer": "The LORD is the psalmist's shepherd.",
                "metadata": {"book": "Psalm", "chapter": 23, "verse": 1, "translation": "KJV"}
            }
        ]
    
    try:
        # Try to load as JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded corpus dataset with {len(data)} examples from {file_path}")
        return data
    
    except Exception as e:
        logger.error(f"Error loading corpus dataset as JSON: {e}")
        
        # Try to load as JSONL as fallback
        try:
            data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('//'):
                        data.append(json.loads(line))
            logger.info(f"Loaded {len(data)} examples from JSONL at {file_path}")
            return data
        except Exception as e2:
            logger.error(f"Error loading as JSONL: {e2}")
            return []

def generate_theological_qa_pairs(terms: List[Dict[str, Any]], num_pairs: int) -> List[Dict[str, Any]]:
    """Generate QA pairs focusing on theological terms."""
    if not terms:
        return []
    
    qa_pairs = []
    selected_terms = random.sample(terms, min(num_pairs, len(terms)))
    
    for term in selected_terms:
        try:
            term_name = term.get("term", "")
            term_id = term.get("strongs_id", "")
            definition = term.get("definition", "")
            
            if not term_name or not term_id or not definition:
                continue
            
            # Create a simple question about the term
            language = "Hebrew" if term_id.startswith("H") else "Greek"
            
            question = random.choice([
                f"What is the meaning of the {language} term '{term_name}' (Strong's {term_id})?",
                f"What does the {language} word '{term_name}' (Strong's {term_id}) mean in biblical context?",
                f"What is the theological significance of '{term_name}' (Strong's {term_id})?"
            ])
            
            # Add relevant metadata
            qa_pair = {
                "question": question,
                "answer": definition,
                "context": f"Theological term: {term_name}, Strong's ID: {term_id}, Language: {language}",
                "metadata": {
                    "type": "theological",
                    "strongs_id": term_id,
                    "language": language,
                    "term": term_name
                }
            }
            
            qa_pairs.append(qa_pair)
        
        except Exception as e:
            logger.error(f"Error generating theological QA pair: {e}")
    
    logger.info(f"Generated {len(qa_pairs)} theological QA pairs")
    return qa_pairs

def generate_factual_qa_pairs(corpus: List[Dict[str, Any]], num_pairs: int) -> List[Dict[str, Any]]:
    """Generate factual QA pairs from the Bible corpus."""
    if not corpus:
        return []
    
    qa_pairs = []
    selected_examples = random.sample(corpus, min(num_pairs, len(corpus)))
    
    for example in selected_examples:
        try:
            context = example.get("context", "")
            
            if "question" in example and "answer" in example:
                # Use existing QA pair
                qa_pair = {
                    "question": example["question"],
                    "answer": example["answer"],
                    "context": context,
                    "metadata": example.get("metadata", {"type": "factual"})
                }
            else:
                # Create a new factual question based on the context
                if "book" in example.get("metadata", {}) and "chapter" in example.get("metadata", {}):
                    book = example["metadata"]["book"]
                    chapter = example["metadata"]["chapter"]
                    verse = example["metadata"].get("verse", 1)
                    
                    question = f"What does {book} {chapter}:{verse} say?"
                    answer = context
                    
                    qa_pair = {
                        "question": question,
                        "answer": answer,
                        "context": context,
                        "metadata": {"type": "factual", "book": book, "chapter": chapter, "verse": verse}
                    }
                else:
                    continue
            
            if qa_pair:
                qa_pairs.append(qa_pair)
        
        except Exception as e:
            logger.error(f"Error generating factual QA pair: {e}")
    
    logger.info(f"Generated {len(qa_pairs)} factual QA pairs")
    return qa_pairs

def generate_multi_turn_examples(corpus: List[Dict[str, Any]], theological_terms: List[Dict[str, Any]], num_examples: int) -> List[Dict[str, Any]]:
    """Generate multi-turn conversation examples."""
    multi_turn_examples = []
    
    # Combine corpus and theological terms for context
    all_sources = []
    for example in corpus:
        if "context" in example:
            all_sources.append({
                "context": example["context"],
                "metadata": example.get("metadata", {})
            })
    
    for term in theological_terms:
        if "term" in term and "definition" in term:
            all_sources.append({
                "context": f"{term['term']}: {term['definition']}",
                "metadata": {"type": "theological", "strongs_id": term.get("strongs_id", "")}
            })
    
    if not all_sources:
        return []
    
    selected_sources = random.sample(all_sources, min(num_examples, len(all_sources)))
    
    for source in selected_sources:
        try:
            context = source["context"]
            metadata = source["metadata"]
            
            # Generate a primary question
            if metadata.get("type") == "theological":
                term = context.split(":")[0] if ":" in context else "term"
                primary_question = f"Can you explain the meaning of '{term}'?"
                primary_answer = context
            else:
                book = metadata.get("book", "Genesis")
                chapter = metadata.get("chapter", 1)
                verse = metadata.get("verse", 1)
                primary_question = f"What does {book} {chapter}:{verse} teach us?"
                primary_answer = context
            
            # Generate follow-up questions
            followup_questions = [
                "Can you provide more details?",
                "What is the theological significance of this?",
                "How does this relate to other passages?",
                "What are the implications for believers today?"
            ]
            
            # Select a random follow-up question
            followup_question = random.choice(followup_questions)
            
            # Multi-turn example with history
            multi_turn_example = {
                "question": followup_question,
                "answer": f"Based on {context}, the theological significance includes [details would follow from the model]",
                "context": context,
                "history": [
                    {"role": "user", "content": primary_question},
                    {"role": "assistant", "content": primary_answer}
                ],
                "metadata": {
                    "type": "multi_turn",
                    "original_type": metadata.get("type", "factual")
                }
            }
            
            multi_turn_examples.append(multi_turn_example)
        
        except Exception as e:
            logger.error(f"Error generating multi-turn example: {e}")
    
    logger.info(f"Generated {len(multi_turn_examples)} multi-turn conversation examples")
    return multi_turn_examples

def add_db_examples(num_pairs: int) -> List[Dict[str, Any]]:
    """Generate QA pairs directly from the database."""
    if not DB_UTILS_AVAILABLE:
        logger.warning("Database utilities not available, skipping database examples")
        return []
    
    qa_pairs = []
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Get Hebrew terms with Strong's IDs
            cursor.execute("""
                SELECT DISTINCT h.strongs_id, e.hebrew_word, e.transliteration, e.definition
                FROM bible.hebrew_ot_words h
                JOIN bible.hebrew_entries e ON h.strongs_id = e.strongs_id
                WHERE h.strongs_id IN ('H430', 'H3068', 'H113', 'H2617', 'H539')
                LIMIT %s
            """, (num_pairs // 2,))
            
            hebrew_terms = cursor.fetchall()
            
            for term in hebrew_terms:
                strongs_id, hebrew_word, transliteration, definition = term
                
                qa_pair = {
                    "question": f"What does the Hebrew term '{transliteration}' (Strong's {strongs_id}) mean?",
                    "answer": definition,
                    "context": f"Hebrew word: {hebrew_word}, Transliteration: {transliteration}, Strong's ID: {strongs_id}",
                    "metadata": {
                        "type": "theological",
                        "language": "Hebrew",
                        "strongs_id": strongs_id,
                        "term": transliteration
                    }
                }
                
                qa_pairs.append(qa_pair)
            
            # Get Greek terms with Strong's IDs
            cursor.execute("""
                SELECT DISTINCT g.strongs_id, e.greek_word, e.transliteration, e.definition
                FROM bible.greek_nt_words g
                JOIN bible.greek_entries e ON g.strongs_id = e.strongs_id
                WHERE g.strongs_id IN ('G2316', 'G3056', 'G5547', 'G25', 'G4102')
                LIMIT %s
            """, (num_pairs // 2,))
            
            greek_terms = cursor.fetchall()
            
            for term in greek_terms:
                strongs_id, greek_word, transliteration, definition = term
                
                qa_pair = {
                    "question": f"What does the Greek term '{transliteration}' (Strong's {strongs_id}) mean?",
                    "answer": definition,
                    "context": f"Greek word: {greek_word}, Transliteration: {transliteration}, Strong's ID: {strongs_id}",
                    "metadata": {
                        "type": "theological",
                        "language": "Greek",
                        "strongs_id": strongs_id,
                        "term": transliteration
                    }
                }
                
                qa_pairs.append(qa_pair)
    
    except Exception as e:
        logger.error(f"Error generating database examples: {e}")
    
    logger.info(f"Generated {len(qa_pairs)} QA pairs from the database")
    return qa_pairs

def save_dataset(examples: List[Dict[str, Any]], file_path: str) -> bool:
    """Save the expanded dataset to a JSONL file."""
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example) + '\n')
        
        logger.info(f"Saved {len(examples)} examples to {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving dataset: {e}")
        return False

def add_sample_term_if_empty(terms):
    """Add sample theological terms if the list is empty."""
    if len(terms) > 0:
        return terms
        
    # Add sample terms with Hebrew and Greek Strong's IDs
    sample_terms = [
        {
            "term": "אלהים", 
            "strongs_id": "H430", 
            "context": "God, gods, judges, angels; plural of H433",
            "answer": "The Hebrew term 'אלהים' (H430) means 'God' or 'gods'. It is the plural form of 'Eloah' and is used to refer to the one true God of Israel, denoting His majesty and fullness of power."
        },
        {
            "term": "יהוה", 
            "strongs_id": "H3068", 
            "context": "the proper name of the God of Israel; the self-existent and eternal one",
            "answer": "The Hebrew term 'יהוה' (H3068) is the proper name of the God of Israel, often rendered as 'LORD' in English translations. It derives from the verb 'to be' and is associated with God's self-revelation to Moses as 'I AM THAT I AM'."
        },
        {
            "term": "λόγος", 
            "strongs_id": "G3056", 
            "context": "word, speech, divine utterance, statement, declaration",
            "answer": "In John 1:1, the Greek term 'λόγος' (G3056) is translated as 'Word' and refers to Jesus Christ. It conveys the concept of divine revelation, reason, or expression. John identifies Jesus as the eternal Word who was with God and was God from the beginning."
        }
    ]
    
    logger.info(f"Added {len(sample_terms)} sample terms because no terms were found")
    return sample_terms

def main():
    """Main function to expand the validation dataset."""
    args = parse_args()
    
    # Load existing dataset
    existing_examples = load_existing_dataset(args.output_file)
    logger.info(f"Starting with {len(existing_examples)} existing examples")
    
    # Load theological terms
    theological_terms = load_theological_terms(args.theological_file)
    
    # Add sample terms if needed and enabled
    if args.sample_theological:
        theological_terms = add_sample_term_if_empty(theological_terms)
    
    # Load corpus dataset
    corpus_examples = load_corpus_dataset(args.corpus_file)
    
    # Generate new examples
    new_examples = []
    
    # Generate theological QA pairs
    theological_pairs = generate_theological_qa_pairs(theological_terms, args.num_single // 2)
    new_examples.extend(theological_pairs)
    
    # Generate factual QA pairs
    factual_pairs = generate_factual_qa_pairs(corpus_examples, args.num_single // 2)
    new_examples.extend(factual_pairs)
    
    # Generate multi-turn examples
    multi_turn_examples = generate_multi_turn_examples(corpus_examples, theological_terms, args.num_multi)
    new_examples.extend(multi_turn_examples)
    
    # Add examples from the database if available
    if DB_UTILS_AVAILABLE:
        db_examples = add_db_examples(args.num_single // 4)
        new_examples.extend(db_examples)
    
    # Combine existing and new examples
    combined_examples = existing_examples + new_examples
    
    # De-duplicate based on questions
    seen_questions = set()
    unique_examples = []
    
    for example in combined_examples:
        question = example.get("question", "").strip().lower()
        if question and question not in seen_questions:
            seen_questions.add(question)
            unique_examples.append(example)
    
    logger.info(f"Final dataset has {len(unique_examples)} examples")
    
    # Save the expanded dataset
    success = save_dataset(unique_examples, args.output_file)
    
    if success:
        logger.info("Validation dataset expansion completed successfully")
    else:
        logger.error("Validation dataset expansion failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 