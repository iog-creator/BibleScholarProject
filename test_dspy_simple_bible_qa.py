#!/usr/bin/env python3
"""
Simple test script for DSPy Bible QA using LM Studio
This script uses DSPy directly without loading a saved model
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

import dspy
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.dspy')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bible_qa_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def parse_args():
    parser = argparse.ArgumentParser(description="Test DSPy Bible QA with LM Studio")
    parser.add_argument(
        "--test-queries",
        type=str,
        default="data/test_queries.json",
        help="Path to test queries JSON file"
    )
    return parser.parse_args()

def configure_lm_studio():
    """Configure DSPy to use LM Studio."""
    try:
        # Get LM Studio API URL and model from environment variables
        lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
        model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
        
        logger.info(f"Using LM Studio API at: {lm_studio_api}")
        logger.info(f"Using model: {model_name}")
        
        # Configure DSPy with LM Studio
        lm = dspy.LM(
            model_type="openai", 
            model=model_name,
            api_base=lm_studio_api,
            api_key="dummy"  # LM Studio doesn't need a real key
        )
        dspy.configure(lm=lm)
        logger.info("DSPy configured with LM Studio")
        return True
    
    except Exception as e:
        logger.error(f"Error configuring LM Studio: {e}")
        return False

def create_test_queries():
    """Create sample test queries if they don't exist."""
    test_queries = [
        {
            "question": "Who created the heavens and the earth?",
            "context": "Genesis 1:1 In the beginning God created the heavens and the earth."
        },
        {
            "question": "What did God give because of his love for the world?",
            "context": "John 3:16 For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life."
        },
        {
            "question": "Who is the psalmist's shepherd?",
            "context": "Psalms 23:1 The LORD is my shepherd, I shall not want."
        },
        {
            "question": "What does Isaiah say about those who wait upon the Lord?",
            "context": "Isaiah 40:31 But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint."
        }
    ]
    
    # Create directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Write test queries to file
    with open("data/test_queries.json", "w") as f:
        json.dump(test_queries, f, indent=2)
    
    return test_queries

def main():
    """Main function to test the Bible QA model."""
    args = parse_args()
    
    # Configure LM Studio
    if not configure_lm_studio():
        logger.error("Failed to configure LM Studio")
        return 1
    
    # Create signature and model
    class BibleQASignature(dspy.Signature):
        """Answer questions about Bible verses with theological accuracy."""
        context = dspy.InputField(desc="Biblical context or verse")
        question = dspy.InputField(desc="Question about the biblical context")
        answer = dspy.OutputField(desc="Answer to the question based on the biblical context")
    
    # Create a simple chain of thought model
    model = dspy.ChainOfThought(BibleQASignature)
    
    # Create test queries if the file doesn't exist
    if not os.path.exists(args.test_queries):
        logger.info(f"Creating test queries at {args.test_queries}")
        test_queries = create_test_queries()
    else:
        # Load test queries from file
        with open(args.test_queries, "r") as f:
            test_queries = json.load(f)
    
    # Test the model with each query
    logger.info(f"Testing model with {len(test_queries)} queries")
    for i, query in enumerate(test_queries):
        try:
            # Generate a prediction
            prediction = model(
                context=query["context"],
                question=query["question"]
            )
            
            # Print the results
            print(f"\nQuery {i+1}:")
            print(f"Context: {query['context']}")
            print(f"Question: {query['question']}")
            print(f"Answer: {prediction.answer}")
        
        except Exception as e:
            logger.error(f"Error testing query {i+1}: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 