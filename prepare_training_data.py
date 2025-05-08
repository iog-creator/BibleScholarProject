#!/usr/bin/env python3
"""
Prepare Training Data

This script ensures the Bible QA training data exists at the expected location.
It copies from alternative locations if needed or generates new data.

Usage:
    python prepare_training_data.py [--force]
"""

import os
import sys
import json
import shutil
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/prepare_training_data.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs("logs", exist_ok=True)

def ensure_directory(directory):
    """Ensure directory exists."""
    Path(directory).mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {directory}")

def check_training_data(primary_path, alternative_paths, force=False):
    """Check if training data exists at primary path, otherwise copy from alternatives."""
    if force:
        logger.info("Force flag enabled - will copy or generate data regardless of existing files")
    
    train_file = os.path.join(primary_path, "qa_dataset_train.jsonl")
    val_file = os.path.join(primary_path, "qa_dataset_val.jsonl")
    
    # Check if files already exist
    train_exists = os.path.exists(train_file) and not force
    val_exists = os.path.exists(val_file) and not force
    
    if train_exists and val_exists:
        logger.info(f"Training data already exists at {primary_path}")
        return True
    
    # Create target directory
    ensure_directory(primary_path)
    
    # Try alternative paths
    for alt_path in alternative_paths:
        alt_train = os.path.join(alt_path, "qa_dataset_train.jsonl")
        alt_val = os.path.join(alt_path, "qa_dataset_val.jsonl")
        
        if os.path.exists(alt_train) and (not train_exists):
            logger.info(f"Copying training dataset from {alt_train}")
            shutil.copy2(alt_train, train_file)
            train_exists = True
        
        if os.path.exists(alt_val) and (not val_exists):
            logger.info(f"Copying validation dataset from {alt_val}")
            shutil.copy2(alt_val, val_file)
            val_exists = True
        
        if train_exists and val_exists:
            logger.info("All required data files copied successfully")
            return True
    
    # If we still don't have the files, try to generate them
    if not (train_exists and val_exists):
        logger.warning("Required datasets not found in alternative locations")
        logger.info("Attempting to generate new datasets...")
        
        try:
            return generate_training_data(primary_path)
        except Exception as e:
            logger.error(f"Failed to generate training data: {e}")
            return False
    
    return train_exists and val_exists

def generate_training_data(output_path):
    """Generate minimal training data if no other sources exist."""
    logger.info(f"Generating minimal training dataset at {output_path}")
    
    # Sample training examples
    train_data = [
        {
            "context": "Genesis 1:1: In the beginning God created the heaven and the earth.",
            "question": "What does Genesis 1:1 say?",
            "answer": "In the beginning God created the heaven and the earth.",
            "history": []
        },
        {
            "context": "John 3:16: For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
            "question": "What does John 3:16 teach?",
            "answer": "God loved the world and gave His only begotten Son so that believers would have everlasting life.",
            "history": []
        },
        {
            "context": "H430 - Elohim: God; plural form of Eloah. The Creator, the supreme God.",
            "question": "What does Elohim mean?",
            "answer": "Elohim (H430) refers to God, and is the plural form of Eloah, indicating the Creator, the supreme God.",
            "history": []
        },
        {
            "context": "Psalm 23:1: The LORD is my shepherd; I shall not want.",
            "question": "Who is described as a shepherd in Psalm 23?",
            "answer": "The LORD (YHWH) is described as a shepherd.",
            "history": []
        },
        {
            "context": "Romans 3:23: For all have sinned, and come short of the glory of God.",
            "question": "What does Romans 3:23 say about humanity?",
            "answer": "All humanity has sinned and falls short of God's glory.",
            "history": []
        }
    ]
    
    # Sample validation examples
    val_data = [
        {
            "context": "Genesis 1:3: And God said, Let there be light: and there was light.",
            "question": "How did God create light?",
            "answer": "God spoke light into existence by saying 'Let there be light'.",
            "history": []
        },
        {
            "context": "John 1:1: In the beginning was the Word, and the Word was with God, and the Word was God.",
            "question": "Who is the Word in John 1:1?",
            "answer": "The Word refers to Jesus Christ, who was with God and was God from the beginning.",
            "history": []
        },
        {
            "context": "Matthew 5:3-10: The Beatitudes",
            "question": "What are the Beatitudes?",
            "answer": "The Beatitudes are a series of blessings declared by Jesus in the Sermon on the Mount, beginning with 'Blessed are the poor in spirit'.",
            "history": []
        }
    ]
    
    # Create directory
    ensure_directory(output_path)
    
    # Write training data
    train_file = os.path.join(output_path, "qa_dataset_train.jsonl")
    val_file = os.path.join(output_path, "qa_dataset_val.jsonl")
    
    try:
        # Write train data
        with open(train_file, "w", encoding="utf-8") as f:
            for example in train_data:
                f.write(json.dumps(example) + "\n")
        logger.info(f"Created training file with {len(train_data)} examples at {train_file}")
        
        # Write validation data
        with open(val_file, "w", encoding="utf-8") as f:
            for example in val_data:
                f.write(json.dumps(example) + "\n")
        logger.info(f"Created validation file with {len(val_data)} examples at {val_file}")
        
        return True
    except Exception as e:
        logger.error(f"Error writing dataset files: {e}")
        return False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Prepare Bible QA training data")
    parser.add_argument("--force", action="store_true", help="Force regeneration of data even if it exists")
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    # Define paths
    primary_path = "data/processed/bible_training_data"
    
    alternative_paths = [
        "data/processed/dspy_training_data/bible_corpus/integrated",
        "data/processed/dspy_training_data/bible_corpus/dspy",
        "data/processed/dspy_training_data/bible_corpus"
    ]
    
    # Ensure data exists
    if check_training_data(primary_path, alternative_paths, args.force):
        logger.info("Training data preparation completed successfully")
        return 0
    else:
        logger.error("Failed to prepare training data")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 