#!/usr/bin/env python3
"""
Test DSPy JSON Patch

This script tests the JSON patch for DSPy to handle string responses
from LM Studio before running the optimization pipeline.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_dspy_json_fix.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs("logs", exist_ok=True)

# First import DSPy
import dspy

# Enable experimental features
dspy.settings.experimental = True

# Then apply the patch
try:
    import dspy_json_patch
    logger.info("Successfully imported DSPy JSON patch")
except ImportError:
    logger.error("Failed to import dspy_json_patch. Please make sure it's available.")
    sys.exit(1)

# Configure DSPy with LM Studio
try:
    # Get LM Studio API URL from environment variables
    from dotenv import load_dotenv
    load_dotenv('.env.dspy')
    
    lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://localhost:1234/v1")
    model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
    
    # Configure DSPy with LM Studio - IMPORTANT: Don't use response_format
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
except Exception as e:
    logger.error(f"Error configuring LM Studio: {e}")
    sys.exit(1)

# Define a simple math QA signature
class MathQA(dspy.Signature):
    question = dspy.InputField(desc="A math question")
    answer = dspy.OutputField(desc="The answer to the math question")

# Create a simple module for testing
class SimpleMathQA(dspy.Module):
    def __init__(self):
        super().__init__()
        self.qa = dspy.Predict(MathQA)
    
    def forward(self, question):
        return self.qa(question=question)

# Define simple metric
class SimpleMetric:
    def __call__(self, example, pred, trace=None):
        # Very simple metric - always returns 1.0 for testing
        return 1.0

# Test basic module
logger.info("Testing with question: What is 2+2 and why?")
try:
    module = SimpleMathQA()
    response = module("What is 2+2 and why?")
    logger.info(f"Response type: {type(response)}")
    logger.info(f"Response attributes: {dir(response)}")
    logger.info(f"Got answer: {response.answer}")
except Exception as e:
    logger.error(f"Error in basic module test: {e}")
    sys.exit(1)

# Test BootstrapFewShot optimizer which doesn't require fine-tuning
try:
    # Create a simple training example
    example = dspy.Example(
        question="What is 2+2?",
        answer="4"
    ).with_inputs("question")
    
    # Create optimizer with a simple metric
    metric = SimpleMetric()
    optimizer = dspy.BootstrapFewShot(
        metric=metric,
        max_bootstrapped_demos=2,  # Only use 2 demos for testing
        max_labeled_demos=1
    )
    
    # Compile the optimizer with a single example
    # This should trigger the JSON patch and handle string responses
    try:
        optimized_module = optimizer.compile(
            student=module,
            trainset=[example]
        )
        logger.info("BootstrapFewShot compilation succeeded!")
        
        # Test the optimized module
        test_response = optimized_module("What is 5+5?")
        logger.info(f"Optimized response to 'What is 5+5?': {test_response.answer}")
    except Exception as e:
        logger.error(f"Optimizer error: {e}")
        raise
except Exception as e:
    logger.error(f"Error testing optimizer: {e}")
    sys.exit(1)

# If we got here, the test succeeded
logger.info("DSPy JSON patch test succeeded!")
print("DSPy JSON patch is working correctly!") 