#!/usr/bin/env python
"""
Test script for verifying DSPy integration with Llama-3.3-70B-Instruct model
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path so we can import from src
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_dspy_llama_integration():
    """Test DSPy integration with Llama-3.3-70B-Instruct"""
    try:
        import dspy
        from src.dspy_programs.huggingface_integration import configure_huggingface_model
        
        logger.info("Testing DSPy integration with Llama-3.3-70B-Instruct")
        
        # Load API key from environment
        load_dotenv('.env.dspy')
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        model_name = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
        
        if not api_key:
            logger.error("HUGGINGFACE_API_KEY not set in environment")
            return False
        
        # Configure Llama as the LM for DSPy
        try:
            logger.info(f"Configuring model: {model_name}")
            lm = configure_huggingface_model(api_key=api_key, model_name=model_name)
            dspy.configure(lm=lm)
            
            # Define a simple DSPy signature for Bible Q&A
            class BibleQA(dspy.Signature):
                """Answer questions about the Bible."""
                question = dspy.InputField(desc="A question about the Bible")
                answer = dspy.OutputField(desc="A comprehensive answer to the question with biblical references")
            
            # Create a simple module
            logger.info("Creating DSPy Predict module")
            bible_qa = dspy.Predict(BibleQA)
            
            # Test with a simple Bible question
            test_question = "What is the significance of the Exodus in the Bible?"
            logger.info(f"Testing with question: {test_question}")
            
            # Call the model
            result = bible_qa(question=test_question)
            
            # Print the result
            logger.info("DSPy prediction successful!")
            logger.info(f"Question: {test_question}")
            logger.info(f"Answer: {result.answer}")
            
            # Test another theological question
            theo_question = "Explain the concept of salvation in Christianity"
            logger.info(f"Testing with theological question: {theo_question}")
            
            # Call the model
            theo_result = bible_qa(question=theo_question)
            
            # Print the result
            logger.info(f"Question: {theo_question}")
            logger.info(f"Answer: {theo_result.answer}")
            
            return True
        except Exception as e:
            logger.error(f"Error in DSPy integration: {e}")
            logger.exception("Detailed traceback:")
            return False
    except ImportError as e:
        logger.error(f"Error importing required packages: {e}")
        return False

def main():
    """Run the test"""
    logger.info("Starting DSPy Llama-3.3 integration test")
    
    success = test_dspy_llama_integration()
    
    if success:
        logger.info("DSPy Llama-3.3 integration test completed successfully!")
        return 0
    else:
        logger.error("DSPy Llama-3.3 integration test failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 