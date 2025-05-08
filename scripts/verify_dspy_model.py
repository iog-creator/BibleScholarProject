#!/usr/bin/env python3
"""
DSPy Model Verification Script

Runs a simple test of the Bible QA model using DSPy and LM Studio
to verify configuration before running optimization.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Import DSPy
import dspy

# Apply the JSON patch immediately after importing DSPy
try:
    # Look for dspy_json_patch in parent directory first
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import dspy_json_patch  # Apply the patch
except ImportError:
    pass  # Proceed without the patch

from dotenv import load_dotenv

# Enable experimental features for DSPy 2.6+
dspy.settings.experimental = True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/verify_dspy_model.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env.dspy')

def configure_lm_studio():
    """Configure DSPy to use LM Studio with safe configuration."""
    try:
        # Get LM Studio API URL and model from environment variables
        lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
        model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
        
        logger.info(f"Using LM Studio API at: {lm_studio_api}")
        logger.info(f"Using model: {model_name}")
        
        # Configure DSPy with LM Studio - no response_format parameter
        lm = dspy.LM(
            model_type="openai", 
            model=model_name,
            api_base=lm_studio_api,
            api_key="dummy",  # LM Studio doesn't need a real key
            config={
                "temperature": 0.1,
                "max_tokens": 512
            }
        )
        
        dspy.configure(lm=lm)
        logger.info("DSPy configured with LM Studio")
        return True
    
    except Exception as e:
        logger.error(f"Error configuring LM Studio: {e}")
        return False

def test_model():
    """Test the model with a simple Bible question."""
    try:
        # Define a simple signature for Bible QA
        class SimpleBibleQA(dspy.Signature):
            """Answer a simple Bible question."""
            question = dspy.InputField(desc="Question about the Bible")
            answer = dspy.OutputField(desc="Answer to the Bible question")
        
        # Create a predictor
        predictor = dspy.Predict(SimpleBibleQA)
        
        # Test with a simple question
        question = "What is the first verse in Genesis?"
        logger.info(f"Testing with question: {question}")
        
        result = predictor(question=question)
        
        if hasattr(result, 'answer') and result.answer:
            logger.info(f"Got answer: {result.answer}")
            return True
        else:
            logger.error("No answer returned")
            return False
    
    except Exception as e:
        logger.error(f"Error testing model: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function."""
    # Configure LM Studio
    if not configure_lm_studio():
        logger.error("Failed to configure LM Studio")
        return 1
    
    # Test model
    if not test_model():
        logger.error("Failed to test model")
        return 1
    
    logger.info("DSPy model verification succeeded!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 