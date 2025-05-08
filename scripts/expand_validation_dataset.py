#!/usr/bin/env python3
"""
Validation Dataset Expansion Script

This script expands the validation dataset for Bible QA optimization
by generating theological questions with Strong's IDs and multi-turn conversations.
"""

import os
import sys
import json
import random
import logging
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/expand_validation_dataset.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Expand validation dataset for Bible QA")
    parser.add_argument(
        "--output-file",
        type=str,
        default="data/processed/dspy_training_data/bible_corpus/integrated/qa_dataset_val.jsonl",
        help="Output JSONL file path"
    )
    parser.add_argument(
        "--theological-file",
        type=str,
        default="data/processed/dspy_training_data/theological_terms_dataset.jsonl",
        help="Theological terms dataset file"
    )
    parser.add_argument(
        "--corpus-file",
        type=str,
        default="data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json",
        help="Bible corpus dataset file"
    )
    parser.add_argument(
        "--num-single",
        type=int,
        default=40,
        help="Number of single-turn questions to generate"
    )
    parser.add_argument(
        "--num-multi",
        type=int,
        default=10,
        help="Number of multi-turn conversations to generate"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    return parser.parse_args()

def load_jsonl_file(file_path: str) -> List[Dict]:
    """Load a JSONL file into a list of dictionaries."""
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith("//"):
                    try:
                        item = json.loads(line.strip())
                        data.append(item)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Error parsing JSON line: {e}")
                        continue
        logger.info(f"Loaded {len(data)} items from {file_path}")
        return data
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        return []

def load_json_file(file_path: str) -> List[Dict]:
    """Load a JSON file into a list of dictionaries."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} items from {file_path}")
        return data if isinstance(data, list) else []
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        return []

def extract_theological_terms(theological_data: List[Dict]) -> List[Dict]:
    """Extract theological terms with Strong's IDs from the dataset."""
    terms = []
    for item in theological_data:
        # Check for Strong's IDs in question or answer
        strongs_ids = []
        for field in ["question", "answer", "context"]:
            if field in item:
                # Extract patterns like H1234 or G5678
                import re
                matches = re.findall(r'(?:H|G)\d{1,4}', item.get(field, ""))
                strongs_ids.extend(matches)
        
        if strongs_ids:
            # Get unique Strong's IDs
            strongs_ids = list(set(strongs_ids))
            
            term = {
                "strongs_ids": strongs_ids,
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "context": item.get("context", "")
            }
            terms.append(term)
    
    logger.info(f"Extracted {len(terms)} theological terms with Strong's IDs")
    return terms

def extract_verse_references(corpus_data: List[Dict]) -> List[Dict]:
    """Extract verse references from the corpus dataset."""
    verses = []
    for item in corpus_data:
        context = item.get("context", "")
        if context:
            # Try to extract verse references like "Genesis 1:1"
            import re
            match = re.search(r'([1-3]?\s?[A-Za-z]+)\s+(\d+):(\d+)', context)
            if match:
                book = match.group(1)
                chapter = match.group(2)
                verse = match.group(3)
                
                verses.append({
                    "reference": f"{book} {chapter}:{verse}",
                    "book": book,
                    "chapter": chapter,
                    "verse": verse,
                    "text": context,
                    "question": item.get("question", ""),
                    "answer": item.get("answer", "")
                })
    
    logger.info(f"Extracted {len(verses)} verse references")
    return verses

def generate_single_turn_questions(terms: List[Dict], verses: List[Dict], count: int) -> List[Dict]:
    """Generate single-turn theological questions with Strong's IDs."""
    questions = []
    templates = [
        "What does the term '{term}' ({strongs_id}) mean in {reference}?",
        "What is the theological significance of '{term}' ({strongs_id}) in {reference}?",
        "How does '{term}' ({strongs_id}) relate to God's character in {reference}?",
        "What Hebrew/Greek concept does '{term}' ({strongs_id}) express in {reference}?",
        "Why is the term '{term}' ({strongs_id}) important in understanding {reference}?"
    ]
    
    # Ensure we have terms and verses to work with
    if not terms or not verses:
        logger.warning("Insufficient data to generate single-turn questions")
        return []
    
    # Generate questions
    attempts = 0
    max_attempts = count * 3  # Allow more attempts than needed to find good combinations
    
    while len(questions) < count and attempts < max_attempts:
        attempts += 1
        
        # Select random term and verse
        term = random.choice(terms)
        verse = random.choice(verses)
        
        # If we have any strongs_ids, pick one
        strongs_id = random.choice(term.get("strongs_ids", ["H0000"]))
        
        # Generate question
        template = random.choice(templates)
        reference = verse.get("reference", "Genesis 1:1")
        
        # Extract a term from the Strong's ID using simple pattern
        term_text = "theological term"
        if "(אלה)" in term.get("context", ""):
            term_text = "אלה"
        elif "(יהוה)" in term.get("context", ""):
            term_text = "יהוה"
        elif len(term.get("question", "")) > 10:
            # Try to extract term from question
            term_match = re.search(r"'([^']+)'", term.get("question", ""))
            if term_match:
                term_text = term_match.group(1)
        
        question_text = template.format(
            term=term_text,
            strongs_id=strongs_id,
            reference=reference
        )
        
        # Generate answer (combining information from term and verse)
        answer_text = f"The term '{term_text}' ({strongs_id}) in {reference} "
        if len(term.get("answer", "")) > 10:
            answer_text += term.get("answer", "")
        else:
            answer_text += "refers to an important theological concept in Scripture."
        
        # Create the question object
        question_obj = {
            "context": verse.get("text", ""),
            "question": question_text,
            "answer": answer_text,
            "history": [],
            "metadata": {
                "type": "theological",
                "strongs_id": strongs_id,
                "reference": reference
            }
        }
        
        # Add to our list, avoiding duplicates
        if question_text not in [q["question"] for q in questions]:
            questions.append(question_obj)
    
    logger.info(f"Generated {len(questions)} single-turn theological questions")
    return questions[:count]  # Ensure we only return exactly the requested count

def generate_multi_turn_conversations(terms: List[Dict], verses: List[Dict], count: int) -> List[Dict]:
    """Generate multi-turn theological conversations."""
    conversations = []
    
    # Templates for multi-turn conversations
    conversation_templates = [
        [
            {
                "question": "What does the term '{term1}' ({strongs_id1}) mean in the Bible?",
                "answer": "The term '{term1}' ({strongs_id1}) in the Bible refers to {definition1}."
            },
            {
                "question": "How does this relate to '{term2}' ({strongs_id2})?",
                "answer": "'{term1}' ({strongs_id1}) relates to '{term2}' ({strongs_id2}) through {relationship}."
            }
        ],
        [
            {
                "question": "What is the theological significance of {reference}?",
                "answer": "{reference} is significant because it reveals {significance}."
            },
            {
                "question": "How does the term '{term1}' ({strongs_id1}) contribute to this meaning?",
                "answer": "The term '{term1}' ({strongs_id1}) contributes by emphasizing {contribution}."
            }
        ],
        [
            {
                "question": "Can you explain what '{term1}' ({strongs_id1}) means in its original language?",
                "answer": "In the original language, '{term1}' ({strongs_id1}) means {definition1}."
            },
            {
                "question": "Which Bible passages best demonstrate this concept?",
                "answer": "{reference} is a key passage demonstrating this concept, as it states {demonstration}."
            }
        ]
    ]
    
    # Ensure we have terms and verses to work with
    if not terms or not verses:
        logger.warning("Insufficient data to generate multi-turn conversations")
        return []
    
    # Generate conversations
    attempts = 0
    max_attempts = count * 3  # Allow more attempts than needed
    
    while len(conversations) < count and attempts < max_attempts:
        attempts += 1
        
        # Select random terms and verse
        term1 = random.choice(terms)
        term2 = random.choice([t for t in terms if t != term1])
        verse = random.choice(verses)
        
        # Select Strong's IDs
        strongs_id1 = random.choice(term1.get("strongs_ids", ["H0000"]))
        strongs_id2 = random.choice(term2.get("strongs_ids", ["H0000"]))
        
        # Extract term texts
        term_text1 = "first term"
        if "(אלה)" in term1.get("context", ""):
            term_text1 = "אלה"
        elif "(יהוה)" in term1.get("context", ""):
            term_text1 = "יהוה"
        elif len(term1.get("question", "")) > 10:
            term_match = re.search(r"'([^']+)'", term1.get("question", ""))
            if term_match:
                term_text1 = term_match.group(1)
        
        term_text2 = "second term"
        if "(אלה)" in term2.get("context", ""):
            term_text2 = "אלה"
        elif "(יהוה)" in term2.get("context", ""):
            term_text2 = "יהוה"
        elif len(term2.get("question", "")) > 10:
            term_match = re.search(r"'([^']+)'", term2.get("question", ""))
            if term_match:
                term_text2 = term_match.group(1)
        
        # Select conversation template
        template = random.choice(conversation_templates)
        reference = verse.get("reference", "Genesis 1:1")
        
        # Fill in template
        history = []
        for i, turn in enumerate(template[:-1]):  # All turns except the last one go into history
            q_template = turn["question"]
            a_template = turn["answer"]
            
            # Replace placeholders
            q = q_template.format(
                term1=term_text1,
                strongs_id1=strongs_id1,
                term2=term_text2,
                strongs_id2=strongs_id2,
                reference=reference
            )
            
            # Generate appropriate answer content
            definition1 = "an important theological concept"
            definition2 = "a related theological concept"
            significance = "important truths about God"
            relationship = "their theological connection"
            contribution = "its theological meaning"
            demonstration = "important truths"
            
            # Use content from original data if available
            if len(term1.get("answer", "")) > 10:
                definition1 = term1.get("answer", "")
            if len(term2.get("answer", "")) > 10:
                definition2 = term2.get("answer", "")
            if len(verse.get("answer", "")) > 10:
                demonstration = verse.get("answer", "")
            
            a = a_template.format(
                term1=term_text1,
                strongs_id1=strongs_id1,
                term2=term_text2,
                strongs_id2=strongs_id2,
                reference=reference,
                definition1=definition1,
                definition2=definition2,
                relationship=relationship,
                significance=significance,
                contribution=contribution,
                demonstration=demonstration
            )
            
            history.append({"question": q, "answer": a})
        
        # Final turn becomes the current Q&A
        final_turn = template[-1]
        final_q = final_turn["question"].format(
            term1=term_text1,
            strongs_id1=strongs_id1,
            term2=term_text2,
            strongs_id2=strongs_id2,
            reference=reference
        )
        
        # Generate final answer content
        definition1 = "an important theological concept"
        definition2 = "a related theological concept"
        significance = "important truths about God"
        relationship = "their theological connection"
        contribution = "its theological meaning"
        demonstration = "important truths"
        
        # Use content from original data if available
        if len(term1.get("answer", "")) > 10:
            definition1 = term1.get("answer", "")
        if len(term2.get("answer", "")) > 10:
            definition2 = term2.get("answer", "")
        if len(verse.get("answer", "")) > 10:
            demonstration = verse.get("answer", "")
        
        final_a = final_turn["answer"].format(
            term1=term_text1,
            strongs_id1=strongs_id1,
            term2=term_text2,
            strongs_id2=strongs_id2,
            reference=reference,
            definition1=definition1,
            definition2=definition2,
            relationship=relationship,
            significance=significance,
            contribution=contribution,
            demonstration=demonstration
        )
        
        # Create the conversation object
        conversation_obj = {
            "context": verse.get("text", ""),
            "question": final_q,
            "answer": final_a,
            "history": history,
            "metadata": {
                "type": "multi-turn",
                "strongs_ids": [strongs_id1, strongs_id2],
                "reference": reference
            }
        }
        
        # Add to our list, avoiding duplicates
        if final_q not in [c["question"] for c in conversations]:
            conversations.append(conversation_obj)
    
    logger.info(f"Generated {len(conversations)} multi-turn conversations")
    return conversations[:count]  # Ensure we only return exactly the requested count

def save_jsonl_file(data: List[Dict], file_path: str) -> bool:
    """Save data to a JSONL file."""
    try:
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        
        logger.info(f"Saved {len(data)} items to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving file {file_path}: {e}")
        return False

def main():
    """Main function to expand the validation dataset."""
    args = parse_args()
    
    # Set random seed for reproducibility
    random.seed(args.seed)
    
    # Load existing files
    theological_data = load_jsonl_file(args.theological_file)
    corpus_data = load_json_file(args.corpus_file)
    
    # Check if we have enough data
    if not theological_data or not corpus_data:
        logger.error("Insufficient data to generate validation examples")
        return 1
    
    # Extract theological terms and verse references
    terms = extract_theological_terms(theological_data)
    verses = extract_verse_references(corpus_data)
    
    # Check if we have enough extracted data
    if not terms or not verses:
        logger.error("Failed to extract sufficient terms or verses")
        return 1
    
    # Load existing validation dataset if it exists
    existing_data = load_jsonl_file(args.output_file) if os.path.exists(args.output_file) else []
    
    # Generate new examples
    single_turn = generate_single_turn_questions(terms, verses, args.num_single)
    multi_turn = generate_multi_turn_conversations(terms, verses, args.num_multi)
    
    # Combine all data
    all_data = existing_data + single_turn + multi_turn
    
    # Save the expanded dataset
    if save_jsonl_file(all_data, args.output_file):
        logger.info(f"Successfully expanded validation dataset with {len(single_turn) + len(multi_turn)} new examples")
        return 0
    else:
        logger.error("Failed to save expanded validation dataset")
        return 1

if __name__ == "__main__":
    # Import regex here to avoid import errors if not needed elsewhere
    import re
    sys.exit(main()) 