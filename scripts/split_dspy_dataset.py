#!/usr/bin/env python3
"""
Split DSPy Dataset

Split a DSPy dataset into training and validation sets with 
a configurable ratio.

Usage:
    python scripts/split_dspy_dataset.py --input-file PATH --train-ratio RATIO
"""

import os
import sys
import json
import random
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/split_dataset.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_dataset(file_path: str) -> List[Dict[str, Any]]:
    """Load a dataset from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} examples from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        return []

def split_dataset(
    dataset: List[Dict[str, Any]], 
    train_ratio: float = 0.8,
    random_seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split a dataset into training and validation sets."""
    if not dataset:
        logger.error("Cannot split empty dataset")
        return [], []
    
    # Set random seed for reproducibility
    random.seed(random_seed)
    
    # Shuffle the dataset
    shuffled = dataset.copy()
    random.shuffle(shuffled)
    
    # Calculate split point
    split_idx = int(len(shuffled) * train_ratio)
    
    # Split into training and validation sets
    train_set = shuffled[:split_idx]
    val_set = shuffled[split_idx:]
    
    logger.info(f"Split dataset into {len(train_set)} training and {len(val_set)} validation examples")
    return train_set, val_set

def save_dataset(data: List[Dict[str, Any]], file_path: str) -> None:
    """Save a dataset to a JSON file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(data)} examples to {file_path}")
    except Exception as e:
        logger.error(f"Error saving dataset: {e}")

def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(description="Split a DSPy dataset into training and validation sets")
    parser.add_argument(
        "--input-file", 
        default="data/processed/dspy_training_data/bible_corpus/dspy/expanded_bible_corpus_dataset.json",
        help="Path to input dataset"
    )
    parser.add_argument(
        "--train-ratio", 
        type=float, 
        default=0.8,
        help="Ratio of examples to use for training"
    )
    parser.add_argument(
        "--random-seed", 
        type=int, 
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--train-output", 
        default="data/processed/dspy_training_data/bible_corpus/dspy/expanded_bible_corpus_dataset_train.json",
        help="Path to output training dataset"
    )
    parser.add_argument(
        "--val-output", 
        default="data/processed/dspy_training_data/bible_corpus/dspy/expanded_bible_corpus_dataset_val.json",
        help="Path to output validation dataset"
    )
    
    args = parser.parse_args()
    
    # Load dataset
    dataset = load_dataset(args.input_file)
    if not dataset:
        logger.error(f"Failed to load dataset from {args.input_file}")
        return 1
    
    # Split dataset
    train_set, val_set = split_dataset(
        dataset, 
        train_ratio=args.train_ratio,
        random_seed=args.random_seed
    )
    
    # Save datasets
    save_dataset(train_set, args.train_output)
    save_dataset(val_set, args.val_output)
    
    # Print summary
    logger.info(f"Dataset split complete:")
    logger.info(f"  Input file: {args.input_file}")
    logger.info(f"  Training set: {args.train_output} ({len(train_set)} examples)")
    logger.info(f"  Validation set: {args.val_output} ({len(val_set)} examples)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 