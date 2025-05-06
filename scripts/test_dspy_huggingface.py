#!/usr/bin/env python3
"""
Test DSPy with Hugging Face Integration

This script demonstrates and tests the integration between DSPy and Hugging Face,
performing a simple Bible question answering task.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_basic_completion():
    """Test basic model completion using DSPy and Hugging Face."""
    try:
        # Import and initialize DSPy with Hugging Face
        from src.utils.dspy_hf_init import initialize_dspy
        import dspy
        
        # Initialize DSPy
        if not initialize_dspy():
            logger.error("Failed to initialize DSPy with Hugging Face")
            return False
        
        logger.info("DSPy initialized successfully with Hugging Face")
        
        # Define a simple signature for Bible verse completion
        class BibleVerseCompletion(dspy.Signature):
            """Complete a Bible verse fragment."""
            verse_fragment = dspy.InputField(desc="Beginning of a Bible verse")
            completion = dspy.OutputField(desc="Completed verse")
        
        # Create a simple completion module
        completion_module = dspy.Predict(BibleVerseCompletion)
        
        # Test verse fragments
        test_fragments = [
            "In the beginning God created",
            "For God so loved the world",
            "The Lord is my shepherd"
        ]
        
        # Run tests
        logger.info("Testing Bible verse completion:")
        for fragment in test_fragments:
            logger.info(f"Fragment: {fragment}")
            try:
                result = completion_module(verse_fragment=fragment)
                logger.info(f"Completion: {result.completion}")
                print(f"\nFragment: {fragment}")
                print(f"Completion: {result.completion}")
            except Exception as e:
                logger.error(f"Error completing fragment '{fragment}': {e}")
        
        logger.info("Basic completion tests completed")
        return True
    
    except Exception as e:
        logger.error(f"Error in basic completion test: {e}")
        return False

def test_bible_qa():
    """Test Bible QA using DSPy and Hugging Face."""
    try:
        # Import and initialize DSPy with Hugging Face
        from src.utils.dspy_hf_init import initialize_dspy
        import dspy
        
        # Initialize DSPy if not already initialized
        if not initialize_dspy():
            logger.error("Failed to initialize DSPy with Hugging Face")
            return False
        
        # Define Bible QA signature
        class BibleQA(dspy.Signature):
            """Answer questions about Bible verses."""
            context = dspy.InputField(desc="Bible verses for context")
            question = dspy.InputField(desc="Question about the verses")
            answer = dspy.OutputField(desc="Answer to the question")
        
        # Create a QA module
        qa_module = dspy.Predict(BibleQA)
        
        # Test cases
        test_cases = [
            {
                "context": "In the beginning God created the heavens and the earth. " 
                          "Now the earth was formless and empty, darkness was over the surface of the deep, "
                          "and the Spirit of God was hovering over the waters. " 
                          "And God said, 'Let there be light,' and there was light.",
                "question": "What did God create first according to Genesis?"
            },
            {
                "context": "For God so loved the world that he gave his one and only Son, "
                          "that whoever believes in him shall not perish but have eternal life.",
                "question": "What is the promise to those who believe in God's Son?"
            }
        ]
        
        # Run tests
        logger.info("Testing Bible QA:")
        for case in test_cases:
            logger.info(f"Question: {case['question']}")
            try:
                result = qa_module(context=case['context'], question=case['question'])
                logger.info(f"Answer: {result.answer}")
                print(f"\nContext: {case['context']}")
                print(f"Question: {case['question']}")
                print(f"Answer: {result.answer}")
            except Exception as e:
                logger.error(f"Error answering question '{case['question']}': {e}")
        
        logger.info("Bible QA tests completed")
        return True
    
    except Exception as e:
        logger.error(f"Error in Bible QA test: {e}")
        return False

def test_embedding():
    """Test embedding generation using DSPy and Hugging Face."""
    try:
        # Import required modules
        from src.utils.hf_api_config import HuggingFaceAPI
        import os
        from dotenv import load_dotenv
        import numpy as np
        
        # Load environment variables
        load_dotenv()
        
        # Get API token
        token = os.getenv('HF_API_TOKEN')
        if not token:
            logger.error("No Hugging Face API token found in environment")
            return False
        
        # Initialize API client
        hf_api = HuggingFaceAPI(token)
        
        # Test texts
        texts = [
            "In the beginning God created the heavens and the earth.",
            "For God so loved the world that he gave his one and only Son.",
            "The Lord is my shepherd, I shall not want."
        ]
        
        # Get embeddings
        logger.info("Testing embedding generation:")
        embeddings = hf_api.get_embeddings(texts)
        
        if embeddings and len(embeddings) == len(texts):
            # Print embedding dimensions
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            logger.info(f"Embedding dimensions: {len(embeddings[0])}")
            
            # Calculate similarity between embeddings
            def cosine_similarity(a, b):
                return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            
            logger.info("Calculating similarities between verses:")
            for i in range(len(texts)):
                for j in range(i+1, len(texts)):
                    similarity = cosine_similarity(embeddings[i], embeddings[j])
                    logger.info(f"Similarity between verse {i+1} and verse {j+1}: {similarity:.4f}")
                    print(f"\nVerse 1: {texts[i]}")
                    print(f"Verse 2: {texts[j]}")
                    print(f"Similarity: {similarity:.4f}")
            
            logger.info("Embedding tests completed")
            return True
        else:
            logger.error("Failed to generate embeddings")
            return False
    
    except Exception as e:
        logger.error(f"Error in embedding test: {e}")
        return False

def main():
    """Run tests for Hugging Face DSPy integration."""
    print("\n=== Testing DSPy with Hugging Face Integration ===\n")
    
    # Ensure directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('models/huggingface', exist_ok=True)
    
    # Check if token exists
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv('HF_API_TOKEN')
    if not token:
        logger.error("No Hugging Face API token found. Please add it to your .env file.")
        return False
    
    # Run tests
    tests = [
        ("Basic Completion", test_basic_completion),
        ("Bible QA", test_bible_qa),
        ("Embedding Generation", test_embedding)
    ]
    
    success = True
    for name, test_func in tests:
        print(f"\n--- Running Test: {name} ---\n")
        try:
            if not test_func():
                success = False
                logger.error(f"Test '{name}' failed")
            else:
                logger.info(f"Test '{name}' succeeded")
        except Exception as e:
            success = False
            logger.error(f"Test '{name}' failed with exception: {e}")
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("The Hugging Face DSPy integration is working correctly.")
    else:
        print("\n❌ Some tests failed. See logs for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 