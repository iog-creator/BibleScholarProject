#!/usr/bin/env python
"""
Bible Corpus Dataset Verification Script

This script loads and verifies the Bible corpus dataset without requiring DSPy's complex features.
It examines the dataset structure and provides a summary of its contents.
"""

import os
import json
import logging
from pprint import pprint
from collections import Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dataset(dataset_path):
    """Load dataset from file."""
    logger.info(f"Loading dataset from {dataset_path}")
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Successfully loaded {len(data)} examples")
        return data
    
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise

def analyze_dataset(data):
    """Analyze the dataset structure and provide statistics."""
    logger.info("Analyzing dataset structure and content...")
    
    # Basic statistics
    example_count = len(data)
    
    # Check structure of examples
    fields = set()
    field_counts = Counter()
    metadata_fields = set()
    question_types = Counter()
    
    # Types of content
    has_verses = 0
    has_lexicon = 0
    has_theological_terms = 0
    
    for item in data:
        # Collect all fields
        item_fields = set(item.keys())
        fields.update(item_fields)
        for field in item_fields:
            field_counts[field] += 1
        
        # Collect metadata fields if present
        if 'metadata' in item and isinstance(item['metadata'], dict):
            metadata_fields.update(item['metadata'].keys())
        
        # Analyze question types
        if 'question' in item:
            question = item['question'].lower()
            if 'what does' in question and 'say' in question:
                question_types['verse content'] += 1
            elif 'what is' in question:
                question_types['definition'] += 1
            elif 'who' in question:
                question_types['person'] += 1
            else:
                question_types['other'] += 1
        
        # Content type detection
        context = item.get('context', '').lower()
        question = item.get('question', '').lower()
        
        if any(book in context for book in ['genesis', 'exodus', 'psalms', 'romans']):
            has_verses += 1
        if any(term in context for term in ['h430', 'h3068', 'elohim', 'adon']):
            has_lexicon += 1
        if any(term in question for term in ['theological', 'meaning', 'significance']):
            has_theological_terms += 1
    
    # Prepare report
    report = {
        "example_count": example_count,
        "fields": list(fields),
        "field_counts": dict(field_counts),
        "metadata_fields": list(metadata_fields),
        "question_types": dict(question_types),
        "content_types": {
            "bible_verses": has_verses,
            "lexicon_entries": has_lexicon,
            "theological_terms": has_theological_terms
        }
    }
    
    return report

def print_examples(data, num_examples=3):
    """Print a few examples from the dataset."""
    logger.info(f"Printing {num_examples} sample examples:")
    for i, example in enumerate(data[:num_examples]):
        print(f"\nExample {i+1}:")
        pprint(example)
        print("-" * 50)

def generate_recommendations(report):
    """Generate recommendations based on the dataset analysis."""
    recommendations = []
    
    # Check dataset size
    if report["example_count"] < 50:
        recommendations.append("Dataset is quite small. Consider generating more examples for better model training.")
    
    # Check field consistency
    if report["field_counts"].get("context", 0) < report["example_count"]:
        recommendations.append("Some examples are missing 'context' field, which may be important for QA tasks.")
    
    # Check diversity
    question_types = report["question_types"]
    most_common = max(question_types.items(), key=lambda x: x[1])[0]
    if question_types[most_common] > 0.7 * sum(question_types.values()):
        recommendations.append(f"Question types are skewed towards '{most_common}'. Consider adding more diverse questions.")
    
    # Check content types
    content_types = report["content_types"]
    if content_types["lexicon_entries"] == 0:
        recommendations.append("No lexicon entries detected. Consider adding examples with Strong's numbers and Hebrew/Greek terms.")
    
    # Additional general recommendations
    recommendations.append("For DSPy training, ensure you have complete input/output pairs for each example.")
    recommendations.append("Consider splitting the dataset into train/dev/test sets (e.g., 70%/15%/15%).")
    
    return recommendations

def main():
    # Dataset path
    dataset_path = "data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json"
    
    try:
        # Load dataset
        data = load_dataset(dataset_path)
        
        # Print a few examples
        print_examples(data)
        
        # Analyze dataset
        report = analyze_dataset(data)
        
        # Print report
        print("\nDataset Analysis Report:")
        pprint(report)
        
        # Generate recommendations
        recommendations = generate_recommendations(report)
        
        # Print recommendations
        print("\nRecommendations:")
        for i, rec in enumerate(recommendations):
            print(f"{i+1}. {rec}")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main() 