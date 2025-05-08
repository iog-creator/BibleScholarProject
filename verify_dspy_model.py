#!/usr/bin/env python3
"""
Verify DSPy Model with LM Studio

This script verifies that DSPy can be configured to work with LM Studio
by running a simple prediction task.
"""

import os
import sys
import logging
from pathlib import Path

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

# Create logs directory
os.makedirs("logs", exist_ok=True)

try:
    # First load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env.dspy')
    
    # Import DSPy with experimental features enabled
    import dspy
    dspy.settings.experimental = True
    
    # Apply the JSON patch
    import dspy_json_patch
    logger.info("DSPy JSON patch applied.")
    
    # Configure DSPy with LM Studio
    lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://localhost:1234/v1")
    model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
    
    logger.info(f"Configuring DSPy with {model_name} at {lm_studio_api}")
    lm = dspy.LM(
        model_type="openai", 
        model=model_name,
        api_base=lm_studio_api,
        api_key="dummy",  # LM Studio doesn't need a real key
        config={
            "temperature": 0.1,
            "max_tokens": 100
        }
    )
    dspy.configure(lm=lm)
    
    # Define a simple signature for a math question
    class SimpleQA(dspy.Signature):
        """Answer a simple question."""
        question = dspy.InputField()
        answer = dspy.OutputField()
    
    # Create a predictor using the signature
    predictor = dspy.Predict(SimpleQA)
    
    # Test the predictor with a simple question
    result = predictor(question="What is 2+2?")
    
    # Log the result
    logger.info(f"Result type: {type(result)}")
    logger.info(f"Result: {result}")
    logger.info(f"Answer: {result.answer}")
    
    # Check if the answer is correct
    if hasattr(result, 'answer') and "4" in result.answer:
        logger.info("DSPy model verification successful!")
        print("DSPy model verification successful!")
        print("NOTE: LM Studio does not support fine-tuning, so weight-based optimizers will not work.")
        print("      Use prompt-based optimization methods like BootstrapFewShot or PromptBreeder instead.")
        sys.exit(0)
    else:
        logger.error(f"Unexpected response: {result}")
        print("ERROR: DSPy returned an unexpected response.")
        sys.exit(1)
        
except Exception as e:
    logger.error(f"Error verifying DSPy model: {e}")
    print(f"ERROR: Failed to verify DSPy model: {e}")
    sys.exit(1) 