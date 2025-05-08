#!/usr/bin/env python3
"""
External Dataset Integration Script

This script integrates external Biblical datasets with the internal database
to create a comprehensive training dataset for the Bible QA system.

Usage:
    python scripts/integrate_external_datasets.py
"""

import os
import sys
import json
import logging
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/dataset_integration.log", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Define paths
BASE_DIR = Path(os.getcwd())
DATA_DIR = BASE_DIR / "data"
EXTERNAL_DATASETS_DIR = DATA_DIR / "processed" / "dspy_training_data" / "external"
DSPY_BIBLE_CORPUS_DIR = DATA_DIR / "processed" / "dspy_training_data" / "bible_corpus" / "dspy"
INTEGRATED_OUTPUT_DIR = DATA_DIR / "processed" / "dspy_training_data" / "bible_corpus" / "integrated"

# Ensure directories exist
os.makedirs(INTEGRATED_OUTPUT_DIR, exist_ok=True)

def load_qa_dataset(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load a QA dataset from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file
        
    Returns:
        List of QA pairs
    """
    try:
        qa_pairs = []
        
        if file_path.suffix == '.jsonl':
            # Read JSONL file
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    qa_pairs.append(json.loads(line))
        
        elif file_path.suffix == '.json':
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    qa_pairs = data
                elif isinstance(data, dict) and 'data' in data:
                    qa_pairs = data['data']
        
        logger.info(f"Loaded {len(qa_pairs)} QA pairs from {file_path}")
        return qa_pairs
    
    except Exception as e:
        logger.error(f"Error loading QA dataset from {file_path}: {e}")
        return []

def load_external_datasets() -> List[Dict[str, Any]]:
    """
    Load all external datasets from the external datasets directory.
    
    Returns:
        List of all QA pairs from external datasets
    """
    try:
        # Check if combined file exists
        combined_file = EXTERNAL_DATASETS_DIR / "all_external_datasets_qa_pairs.jsonl"
        if combined_file.exists():
            return load_qa_dataset(combined_file)
        
        # Load individual files if combined file doesn't exist
        qa_pairs = []
        for jsonl_file in EXTERNAL_DATASETS_DIR.glob("*_qa_pairs.jsonl"):
            qa_pairs.extend(load_qa_dataset(jsonl_file))
        
        logger.info(f"Loaded a total of {len(qa_pairs)} QA pairs from external datasets")
        return qa_pairs
    
    except Exception as e:
        logger.error(f"Error loading external datasets: {e}")
        return []

def load_internal_dataset() -> List[Dict[str, Any]]:
    """
    Load the internal Bible QA dataset.
    
    Returns:
        List of QA pairs from the internal dataset
    """
    try:
        # Check for train/val split files first
        train_file = DSPY_BIBLE_CORPUS_DIR / "qa_dataset_train.jsonl"
        val_file = DSPY_BIBLE_CORPUS_DIR / "qa_dataset_val.jsonl"
        
        qa_pairs = []
        
        if train_file.exists() and val_file.exists():
            qa_pairs.extend(load_qa_dataset(train_file))
            qa_pairs.extend(load_qa_dataset(val_file))
            return qa_pairs
        
        # Fall back to combined dataset
        combined_file = DSPY_BIBLE_CORPUS_DIR / "qa_dataset.jsonl"
        if combined_file.exists():
            return load_qa_dataset(combined_file)
        
        alt_combined_file = DSPY_BIBLE_CORPUS_DIR / "combined_bible_corpus_dataset.json"
        if alt_combined_file.exists():
            return load_qa_dataset(alt_combined_file)
        
        logger.error(f"No internal dataset files found in {DSPY_BIBLE_CORPUS_DIR}")
        return []
    
    except Exception as e:
        logger.error(f"Error loading internal dataset: {e}")
        return []

def deduplicate_dataset(qa_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate QA pairs based on question text.
    
    Args:
        qa_pairs: List of QA pairs
        
    Returns:
        Deduplicated list of QA pairs
    """
    try:
        # Use a set to track seen questions
        seen_questions = set()
        deduplicated_pairs = []
        
        for qa_pair in qa_pairs:
            question = qa_pair.get("question", "").strip().lower()
            
            # Skip if question has already been seen
            if question in seen_questions:
                continue
            
            # Add to deduplicated list and mark as seen
            deduplicated_pairs.append(qa_pair)
            seen_questions.add(question)
        
        logger.info(f"Deduplicated dataset from {len(qa_pairs)} to {len(deduplicated_pairs)} QA pairs")
        return deduplicated_pairs
    
    except Exception as e:
        logger.error(f"Error deduplicating dataset: {e}")
        return qa_pairs

def create_train_val_split(qa_pairs: List[Dict[str, Any]], train_pct: float = 0.8) -> Dict[str, List[Dict[str, Any]]]:
    """
    Create a train/validation split of the dataset.
    
    Args:
        qa_pairs: List of QA pairs
        train_pct: Percentage of data to use for training
        
    Returns:
        Dictionary with train and val splits
    """
    try:
        # Shuffle the data
        random.seed(42)
        random.shuffle(qa_pairs)
        
        # Calculate split indices
        train_size = int(len(qa_pairs) * train_pct)
        
        # Split the data
        train_data = qa_pairs[:train_size]
        val_data = qa_pairs[train_size:]
        
        logger.info(f"Split dataset into {len(train_data)} training and {len(val_data)} validation examples")
        
        return {
            "train": train_data,
            "val": val_data
        }
    
    except Exception as e:
        logger.error(f"Error creating train/val split: {e}")
        return {
            "train": qa_pairs,
            "val": []
        }

def create_dataset_summary(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a summary of the integrated dataset.
    
    Args:
        dataset: List of QA pairs
        
    Returns:
        Dictionary with dataset statistics
    """
    try:
        # Initialize counters
        sources = {}
        types = {}
        books = {}
        languages = {}
        
        # Count occurrences
        for qa_pair in dataset:
            metadata = qa_pair.get("metadata", {})
            
            # Count by source
            source = metadata.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
            
            # Count by type
            data_type = metadata.get("type", "unknown")
            types[data_type] = types.get(data_type, 0) + 1
            
            # Count by book
            book = metadata.get("book", "unknown")
            books[book] = books.get(book, 0) + 1
            
            # Count by language
            language = metadata.get("language", "unknown")
            languages[language] = languages.get(language, 0) + 1
        
        # Create summary
        summary = {
            "total_qa_pairs": len(dataset),
            "sources": sources,
            "types": types,
            "books": books,
            "languages": languages,
            "generated_at": datetime.now().isoformat()
        }
        
        return summary
    
    except Exception as e:
        logger.error(f"Error creating dataset summary: {e}")
        return {
            "total_qa_pairs": len(dataset),
            "error": str(e)
        }

def generate_theological_qa_pairs(internal_data: List[Dict[str, Any]], external_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate advanced theological QA pairs by combining internal and external data.
    
    Args:
        internal_data: QA pairs from internal dataset
        external_data: QA pairs from external datasets
        
    Returns:
        List of new theological QA pairs
    """
    try:
        qa_pairs = []
        
        # Extract Strong's IDs and definitions from external data
        strongs_data = {}
        for qa_pair in external_data:
            metadata = qa_pair.get("metadata", {})
            if metadata.get("type") == "lexical" and "strongs_id" in metadata:
                strongs_id = metadata["strongs_id"]
                strongs_data[strongs_id] = {
                    "lemma": qa_pair.get("question", "").split("'")[1] if "'" in qa_pair.get("question", "") else "",
                    "definition": qa_pair.get("answer", ""),
                    "language": metadata.get("language", "unknown")
                }
        
        # Generate new theological QA pairs
        theological_terms = {
            "H7225": {"term": "beginning", "passages": ["Genesis 1:1", "John 1:1"]},
            "H430": {"term": "God (Elohim)", "passages": ["Genesis 1:1", "Psalms 19:1"]},
            "H3068": {"term": "LORD (YHWH)", "passages": ["Genesis 2:4", "Exodus 3:15"]},
            "G26": {"term": "love (agape)", "passages": ["John 3:16", "1 Corinthians 13:4-7"]},
            "G4102": {"term": "faith (pistis)", "passages": ["Hebrews 11:1", "Romans 10:17"]},
            "G5485": {"term": "grace (charis)", "passages": ["Ephesians 2:8-9", "Romans 3:24"]},
            "G1680": {"term": "hope (elpis)", "passages": ["Romans 5:5", "Hebrews 6:19"]},
            "G1515": {"term": "peace (eirene)", "passages": ["John 14:27", "Philippians 4:7"]},
            "H7965": {"term": "peace (shalom)", "passages": ["Numbers 6:26", "Psalms 29:11"]},
            "G2222": {"term": "life (zoe)", "passages": ["John 10:10", "John 14:6"]}
        }
        
        for strongs_id, term_info in theological_terms.items():
            # Skip if we don't have data for this Strong's ID
            if strongs_id not in strongs_data:
                continue
            
            term = term_info["term"]
            passages = term_info["passages"]
            lang = "Hebrew" if strongs_id.startswith("H") else "Greek"
            
            # Create theological significance QA pair
            qa_pairs.append({
                "question": f"What is the theological significance of the {lang} term '{term}' in the Bible?",
                "answer": f"The {lang} term '{term}' (Strong's {strongs_id}) means '{strongs_data[strongs_id]['definition']}'. " +
                        f"It appears in key passages such as {', '.join(passages)} and carries theological significance in Biblical understanding.",
                "context": f"Strong's: {strongs_id}, Term: {term}, Passages: {', '.join(passages)}",
                "metadata": {
                    "source": "integrated_theological",
                    "type": "theological_term",
                    "strongs_id": strongs_id,
                    "language": lang.lower(),
                    "term": term
                }
            })
            
            # Create cross-reference QA pair
            qa_pairs.append({
                "question": f"How is the {lang} concept of '{term}' used across different Bible passages?",
                "answer": f"The {lang} concept of '{term}' (Strong's {strongs_id}) appears in passages such as {', '.join(passages)}. " +
                        f"It refers to '{strongs_data[strongs_id]['definition']}' and provides insights into Biblical theology.",
                "context": f"Strong's: {strongs_id}, Term: {term}, Passages: {', '.join(passages)}",
                "metadata": {
                    "source": "integrated_theological",
                    "type": "cross_reference",
                    "strongs_id": strongs_id,
                    "language": lang.lower(),
                    "term": term
                }
            })
        
        logger.info(f"Generated {len(qa_pairs)} new theological QA pairs")
        return qa_pairs
    
    except Exception as e:
        logger.error(f"Error generating theological QA pairs: {e}")
        return []

def create_multilingual_examples(internal_data: List[Dict[str, Any]], external_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create multilingual QA examples from internal and external data.
    
    Args:
        internal_data: QA pairs from internal dataset
        external_data: QA pairs from external datasets
        
    Returns:
        List of new multilingual QA pairs
    """
    try:
        multilingual_qa_pairs = []
        
        # Key verses to focus on
        key_verses = ["John 3:16", "Genesis 1:1", "Psalm 23:1", "Romans 8:28", "Matthew 28:19-20"]
        
        # Create multilingual comparison questions
        for verse_ref in key_verses:
            multilingual_qa_pairs.append({
                "question": f"How do different translations render {verse_ref}?",
                "answer": f"Different Bible translations vary in how they render {verse_ref} based on translation philosophy and source texts. " +
                        f"For example, literal translations like NASB and ESV aim for word-for-word accuracy, while dynamic translations " +
                        f"like NIV or NLT focus on thought-for-thought equivalence to make the meaning clear.",
                "context": f"Verse reference: {verse_ref}, Translation comparison",
                "metadata": {
                    "source": "integrated_multilingual",
                    "type": "translation_comparison",
                    "verse_ref": verse_ref
                }
            })
        
        # Extract Hebrew/Greek word questions
        hebrew_greek_words = [
            {"word": "shalom", "lang": "Hebrew", "meaning": "peace, completeness, welfare", "strongs_id": "H7965"},
            {"word": "hesed", "lang": "Hebrew", "meaning": "steadfast love, lovingkindness", "strongs_id": "H2617"},
            {"word": "agape", "lang": "Greek", "meaning": "sacrificial love", "strongs_id": "G26"},
            {"word": "logos", "lang": "Greek", "meaning": "word, reason", "strongs_id": "G3056"},
            {"word": "charis", "lang": "Greek", "meaning": "grace, favor", "strongs_id": "G5485"}
        ]
        
        for word_info in hebrew_greek_words:
            multilingual_qa_pairs.append({
                "question": f"What are the challenges in translating the {word_info['lang']} word '{word_info['word']}' into English?",
                "answer": f"The {word_info['lang']} word '{word_info['word']}' (Strong's {word_info['strongs_id']}) means '{word_info['meaning']}'. " +
                        f"Translating it into English presents challenges because there isn't always a single English word that captures " +
                        f"the full range of meaning in the original language. Different translations handle this by choosing different " +
                        f"English words based on context or by using phrases to convey the meaning.",
                "context": f"Word: {word_info['word']}, Language: {word_info['lang']}, Meaning: {word_info['meaning']}, Strong's ID: {word_info['strongs_id']}",
                "metadata": {
                    "source": "integrated_multilingual",
                    "type": "translation_challenge",
                    "word": word_info['word'],
                    "language": word_info['lang'].lower(),
                    "strongs_id": word_info['strongs_id']
                }
            })
        
        logger.info(f"Created {len(multilingual_qa_pairs)} multilingual QA examples")
        return multilingual_qa_pairs
    
    except Exception as e:
        logger.error(f"Error creating multilingual examples: {e}")
        return []

def integrate_datasets(internal_data: List[Dict[str, Any]], external_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Integrate internal and external datasets.
    
    Args:
        internal_data: QA pairs from internal dataset
        external_data: QA pairs from external datasets
        
    Returns:
        Integrated dataset
    """
    try:
        # Start with internal data
        integrated_data = internal_data.copy()
        
        # Add external data
        integrated_data.extend(external_data)
        
        # Generate theological QA pairs
        theological_qa = generate_theological_qa_pairs(internal_data, external_data)
        integrated_data.extend(theological_qa)
        
        # Create multilingual examples
        multilingual_qa = create_multilingual_examples(internal_data, external_data)
        integrated_data.extend(multilingual_qa)
        
        # Deduplicate the dataset
        integrated_data = deduplicate_dataset(integrated_data)
        
        logger.info(f"Created integrated dataset with {len(integrated_data)} QA pairs")
        return integrated_data
    
    except Exception as e:
        logger.error(f"Error integrating datasets: {e}")
        return internal_data

def save_dataset(dataset: List[Dict[str, Any]], output_dir: Path, split: bool = True):
    """
    Save the dataset to output files.
    
    Args:
        dataset: QA pairs to save
        output_dir: Directory to save to
        split: Whether to create train/val split
    """
    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save combined dataset
        combined_path = output_dir / "combined_training_data.jsonl"
        with open(combined_path, 'w', encoding='utf-8') as f:
            for qa_pair in dataset:
                f.write(json.dumps(qa_pair, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved combined dataset with {len(dataset)} QA pairs to {combined_path}")
        
        # Create and save train/val split if requested
        if split:
            splits = create_train_val_split(dataset)
            
            # Save train split
            train_path = output_dir / "qa_dataset_train.jsonl"
            with open(train_path, 'w', encoding='utf-8') as f:
                for qa_pair in splits["train"]:
                    f.write(json.dumps(qa_pair, ensure_ascii=False) + '\n')
            
            # Save val split
            val_path = output_dir / "qa_dataset_val.jsonl"
            with open(val_path, 'w', encoding='utf-8') as f:
                for qa_pair in splits["val"]:
                    f.write(json.dumps(qa_pair, ensure_ascii=False) + '\n')
            
            logger.info(f"Saved {len(splits['train'])} training and {len(splits['val'])} validation examples")
        
        # Create and save dataset summary
        summary = create_dataset_summary(dataset)
        summary_path = output_dir / "dataset_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved dataset summary to {summary_path}")
    
    except Exception as e:
        logger.error(f"Error saving dataset: {e}")

def main():
    """Main function to integrate internal and external datasets."""
    parser = argparse.ArgumentParser(description="Integrate external Bible datasets with internal data")
    parser.add_argument("--output-dir", type=str, 
                      default="data/processed/dspy_training_data/bible_corpus/integrated",
                      help="Directory to save integrated dataset")
    parser.add_argument("--no-split", action="store_true", 
                      help="Don't create train/val split")
    args = parser.parse_args()
    
    # Get output directory
    output_dir = Path(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Load datasets
    logger.info("Loading internal dataset")
    internal_data = load_internal_dataset()
    
    logger.info("Loading external datasets")
    external_data = load_external_datasets()
    
    if not internal_data:
        logger.error("No internal data found. Integration aborted.")
        return
    
    if not external_data:
        logger.warning("No external data found. Will continue with only internal data.")
    
    # Integrate datasets
    logger.info("Integrating datasets")
    integrated_data = integrate_datasets(internal_data, external_data)
    
    # Save the integrated dataset
    logger.info(f"Saving integrated dataset to {output_dir}")
    save_dataset(integrated_data, output_dir, split=not args.no_split)
    
    logger.info("Dataset integration complete")

if __name__ == "__main__":
    main() 