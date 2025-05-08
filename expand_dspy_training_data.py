#!/usr/bin/env python3
"""
DSPy Training Data Expansion Script

This script integrates multiple data sources to create comprehensive training datasets for DSPy:
1. Archives existing corpus data generation scripts
2. Downloads HuggingFace datasets
3. Expands the Bible corpus with specialized theological examples
4. Consolidates and de-duplicates datasets
5. Prepares proper train/validation/test splits

Usage:
    python expand_dspy_training_data.py --output-dir data/processed/dspy_training_data/bible_corpus/dspy
                                       --examples 5000
                                       --huggingface
                                       --deduplicate
"""

import os
import sys
import json
import logging
import argparse
import random
import shutil
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dspy_training_data_expansion.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Expand DSPy training data")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed/dspy_training_data/bible_corpus/dspy",
        help="Directory to save expanded dataset"
    )
    parser.add_argument(
        "--examples",
        type=int,
        default=5000,
        help="Target number of examples to generate"
    )
    parser.add_argument(
        "--huggingface",
        action="store_true",
        help="Download and include HuggingFace datasets"
    )
    parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="Deduplicate the final dataset"
    )
    parser.add_argument(
        "--train-pct",
        type=float,
        default=0.8,
        help="Percentage of data for training set"
    )
    parser.add_argument(
        "--stratify",
        action="store_true",
        help="Stratify splits by book/source"
    )
    return parser.parse_args()

def run_archive_generator(output_dir: str, examples: int = 1000) -> Path:
    """Run the archived comprehensive data generator script."""
    logger.info(f"Running archived data generator for {examples} examples")
    
    try:
        # Import the generator script dynamically
        sys.path.append(str(Path.cwd()))
        
        if os.path.exists("archive/scripts/generate_dspy_training_data.py"):
            from archive.scripts.generate_dspy_training_data import main as generate_main
            
            # Create temp args object for the generator
            class GeneratorArgs:
                def __init__(self):
                    self.output_dir = output_dir
                    self.examples = examples
                    self.include_all = True
            
            # Run the generator with our args
            gen_args = GeneratorArgs()
            generate_main(gen_args)
            
            # Look for the generated dataset
            qa_path = Path(output_dir) / "qa_dataset.jsonl"
            if qa_path.exists():
                logger.info(f"Generated dataset at {qa_path}")
                return qa_path
            else:
                logger.error(f"Generated dataset not found at {qa_path}")
                return None
        else:
            logger.error("Archive generator script not found")
            return None
    
    except Exception as e:
        logger.error(f"Error running archive generator: {e}")
        return None

def download_huggingface_datasets(output_dir: str, max_samples: int = 500) -> Path:
    """Download relevant datasets from HuggingFace."""
    logger.info("Downloading HuggingFace datasets")
    
    try:
        # Import the download script dynamically
        sys.path.append(str(Path.cwd()))
        
        if os.path.exists("archive/scripts/download_huggingface_datasets.py"):
            from archive.scripts.download_huggingface_datasets import main as download_main
            
            # Temporarily replace sys.argv
            original_argv = sys.argv
            sys.argv = [
                "download_huggingface_datasets.py",
                "--output-dir", output_dir,
                "--max-samples", str(max_samples)
            ]
            
            # Run the download script
            try:
                download_main()
            finally:
                # Restore original argv
                sys.argv = original_argv
            
            # Look for the combined dataset
            combined_path = Path(output_dir) / "combined_bible_qa_dataset.json"
            if combined_path.exists():
                logger.info(f"Downloaded combined dataset at {combined_path}")
                return combined_path
            else:
                logger.error(f"Combined dataset not found at {combined_path}")
                return None
        else:
            logger.error("HuggingFace download script not found")
            return None
    
    except Exception as e:
        logger.error(f"Error downloading HuggingFace datasets: {e}")
        return None

def expand_bible_corpus(output_dir: str) -> Path:
    """Expand the Bible corpus with additional theological examples."""
    logger.info("Expanding Bible corpus with theological examples")
    
    try:
        # Import the expansion script dynamically
        sys.path.append(str(Path.cwd()))
        
        if os.path.exists("archive/scripts/expand_bible_corpus.py"):
            from archive.scripts.expand_bible_corpus import expand_bible_corpus_dataset
            
            # Run the expansion function
            expand_bible_corpus_dataset(output_dir)
            
            # Look for the expanded dataset
            expanded_path = Path(output_dir) / "expanded_bible_corpus.json"
            if expanded_path.exists():
                logger.info(f"Expanded corpus dataset at {expanded_path}")
                return expanded_path
            else:
                logger.error(f"Expanded corpus dataset not found at {expanded_path}")
                return None
        else:
            logger.error("Bible corpus expansion script not found")
            return None
    
    except Exception as e:
        logger.error(f"Error expanding Bible corpus: {e}")
        return None

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load data from a JSONL file."""
    data = []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('//'):
                    data.append(json.loads(line))
        
        logger.info(f"Loaded {len(data)} records from {path}")
        return data
    
    except Exception as e:
        logger.error(f"Error loading JSONL file {path}: {e}")
        return []

def load_json(path: Path) -> List[Dict[str, Any]]:
    """Load data from a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data)} records from {path}")
        return data
    
    except Exception as e:
        logger.error(f"Error loading JSON file {path}: {e}")
        return []

def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a record to ensure consistent format."""
    normalized = {
        "question": record.get("question", ""),
        "answer": record.get("answer", ""),
        "context": record.get("context", ""),
        "metadata": {}
    }
    
    # Include metadata if available
    if "metadata" in record:
        normalized["metadata"] = record["metadata"]
    
    # Extract metadata from fields if not in metadata
    for field in ["book", "chapter", "verse", "translation", "reference", "source"]:
        if field in record and field not in normalized["metadata"]:
            normalized["metadata"][field] = record[field]
    
    return normalized

def deduplicate_dataset(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate records based on questions."""
    logger.info(f"Deduplicating dataset with {len(records)} records")
    
    seen_questions = set()
    unique_records = []
    
    for record in records:
        question = record.get("question", "").strip().lower()
        if question and question not in seen_questions:
            seen_questions.add(question)
            unique_records.append(record)
    
    logger.info(f"Deduplicated to {len(unique_records)} unique records")
    return unique_records

def split_dataset(records: List[Dict[str, Any]], train_pct: float = 0.8, stratify: bool = False) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split dataset into train, validation, and test sets."""
    logger.info(f"Splitting {len(records)} records into train/val/test sets")
    
    # Set random seed for reproducibility
    random.seed(42)
    
    if stratify and all("metadata" in r and ("book" in r["metadata"] or "source" in r["metadata"]) for r in records):
        # Group by book or source
        groups = {}
        for record in records:
            # Use book if available, otherwise use source
            if "book" in record["metadata"]:
                key = record["metadata"]["book"]
            elif "source" in record["metadata"]:
                key = record["metadata"]["source"]
            else:
                key = "unknown"
            
            if key not in groups:
                groups[key] = []
            groups[key].append(record)
        
        # Create stratified splits
        train, val, test = [], [], []
        
        for group, group_records in groups.items():
            # Shuffle group records
            random.shuffle(group_records)
            n = len(group_records)
            
            # Calculate split indices
            train_idx = int(n * train_pct)
            val_idx = train_idx + int(n * (1 - train_pct) / 2)
            
            # Add to splits
            train.extend(group_records[:train_idx])
            val.extend(group_records[train_idx:val_idx])
            test.extend(group_records[val_idx:])
        
        logger.info(f"Stratified split: {len(train)} train, {len(val)} validation, {len(test)} test")
        return train, val, test
    else:
        # Simple random split
        random.shuffle(records)
        n = len(records)
        
        train_idx = int(n * train_pct)
        val_idx = train_idx + int(n * (1 - train_pct) / 2)
        
        train = records[:train_idx]
        val = records[train_idx:val_idx]
        test = records[val_idx:]
        
        logger.info(f"Random split: {len(train)} train, {len(val)} validation, {len(test)} test")
        return train, val, test

def save_splits(train: List[Dict[str, Any]], val: List[Dict[str, Any]], test: List[Dict[str, Any]], output_dir: Path):
    """Save train, validation, and test splits."""
    # Make sure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a complete dataset for backward compatibility
    all_data = train + val + test
    
    # Save complete dataset
    with open(output_dir / "combined_bible_corpus_dataset.json", 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2)
    
    # Save as JSONL for DSPy compatibility
    with open(output_dir / "qa_dataset.jsonl", 'w', encoding='utf-8') as f:
        # Write header comment
        f.write("// DSPy Bible QA training dataset\n")
        
        for record in all_data:
            f.write(json.dumps(record) + '\n')
    
    # Save splits
    with open(output_dir / "qa_dataset_train.jsonl", 'w', encoding='utf-8') as f:
        f.write("// DSPy Bible QA training dataset - TRAIN split\n")
        for record in train:
            f.write(json.dumps(record) + '\n')
    
    with open(output_dir / "qa_dataset_val.jsonl", 'w', encoding='utf-8') as f:
        f.write("// DSPy Bible QA training dataset - VALIDATION split\n")
        for record in val:
            f.write(json.dumps(record) + '\n')
    
    with open(output_dir / "qa_dataset_test.jsonl", 'w', encoding='utf-8') as f:
        f.write("// DSPy Bible QA training dataset - TEST split\n")
        for record in test:
            f.write(json.dumps(record) + '\n')
    
    logger.info(f"Saved dataset splits to {output_dir}")

def main(args):
    """Main function to expand DSPy training data."""
    logger.info("Starting DSPy training data expansion")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize temp directory
    temp_dir = Path("tmp_dspy_data")
    temp_dir.mkdir(exist_ok=True)
    
    all_records = []
    
    # Run the archive generator
    archive_path = run_archive_generator(str(temp_dir), args.examples)
    if archive_path:
        logger.info(f"Loading generated data from {archive_path}")
        archive_records = load_jsonl(archive_path)
        for record in archive_records:
            all_records.append(normalize_record(record))
    
    # Download HuggingFace datasets if requested
    if args.huggingface:
        hf_path = download_huggingface_datasets(str(temp_dir), max_samples=500)
        if hf_path:
            logger.info(f"Loading HuggingFace data from {hf_path}")
            hf_records = load_json(hf_path)
            for record in hf_records:
                all_records.append(normalize_record(record))
    
    # Expand Bible corpus
    corpus_path = expand_bible_corpus(str(temp_dir))
    if corpus_path:
        logger.info(f"Loading expanded corpus from {corpus_path}")
        corpus_records = load_json(corpus_path)
        for record in corpus_records:
            all_records.append(normalize_record(record))
    
    # Load existing dataset if available
    existing_path = output_dir / "combined_bible_corpus_dataset.json"
    if existing_path.exists():
        logger.info(f"Loading existing dataset from {existing_path}")
        existing_records = load_json(existing_path)
        for record in existing_records:
            all_records.append(normalize_record(record))
    
    # Deduplicate if requested
    if args.deduplicate:
        all_records = deduplicate_dataset(all_records)
    
    # Get the right number of examples
    if len(all_records) > args.examples:
        logger.info(f"Limiting dataset to {args.examples} examples")
        random.shuffle(all_records)
        all_records = all_records[:args.examples]
    
    # Split dataset
    train_records, val_records, test_records = split_dataset(
        all_records, 
        train_pct=args.train_pct,
        stratify=args.stratify
    )
    
    # Save splits
    save_splits(train_records, val_records, test_records, output_dir)
    
    # Clean up temp directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    logger.info(f"DSPy training data expansion complete: {len(all_records)} total examples")
    logger.info(f"Final counts: {len(train_records)} train, {len(val_records)} validation, {len(test_records)} test")
    logger.info(f"Output saved to {output_dir}")

if __name__ == "__main__":
    args = parse_args()
    main(args) 