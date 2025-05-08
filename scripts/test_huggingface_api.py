#!/usr/bin/env python
"""
Test script for verifying HuggingFace API integration with BibleScholarProject

This script checks whether the HuggingFace API is properly configured and can be used
for both teacher and student models in the DSPy framework.
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

def test_huggingface_api_connection():
    """Test basic connection to HuggingFace API"""
    try:
        import requests
        logger.info("Requests package successfully imported")
        
        # Load API key from environment
        load_dotenv('.env.dspy')
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        
        if not api_key:
            logger.error("HUGGINGFACE_API_KEY not set in environment")
            return False
            
        # Test API call with a simple request
        try:
            # Test API access - just check if we can access the user info
            response = requests.get(
                "https://huggingface.co/api/whoami",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code == 200:
                logger.info("HuggingFace API connection successful!")
                logger.info(f"User info: {response.json()}")
                return True
            else:
                logger.error(f"Failed to connect to HuggingFace API: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error making API call to HuggingFace: {e}")
            return False
    except ImportError:
        logger.error("Requests package not installed. Install with: pip install requests")
        return False

def test_dspy_huggingface_integration():
    """Test DSPy integration with HuggingFace"""
    try:
        import dspy
        from src.dspy_programs.huggingface_integration import configure_huggingface_model
        
        logger.info("Testing DSPy integration with HuggingFace")
        
        # Load API key from environment
        load_dotenv('.env.dspy')
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        
        if not api_key:
            logger.error("HUGGINGFACE_API_KEY not set in environment")
            return False
        
        # Configure HuggingFace as the LM for DSPy
        try:
            # Use Llama-3-70b-instruct as the default model
            model_name = "meta-llama/Llama-3-70b-instruct"
            logger.info(f"Using model: {model_name}")
            
            lm = configure_huggingface_model(api_key=api_key, model_name=model_name)
            
            # Define a simple DSPy signature
            class SimpleQA(dspy.Signature):
                question = dspy.InputField()
                answer = dspy.OutputField()
            
            # Create a simple module
            basic_qa = dspy.Predict(SimpleQA)
            
            # Test the module with a simple question
            logger.info("Sending test query to model...")
            result = basic_qa(question="What is the first verse of the Bible?")
            
            logger.info("DSPy HuggingFace integration test successful!")
            logger.info(f"Question: What is the first verse of the Bible?")
            logger.info(f"Answer: {result.answer}")
            return True
        except Exception as e:
            logger.error(f"Error in DSPy HuggingFace integration: {e}")
            return False
    except ImportError as e:
        logger.error(f"Error importing required packages: {e}")
        return False

def test_direct_inference():
    """Test direct inference using the HuggingFace API without DSPy"""
    try:
        import requests
        logger.info("Testing direct inference with HuggingFace API")
        
        # Load API key from environment
        load_dotenv('.env.dspy')
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        
        if not api_key:
            logger.error("HUGGINGFACE_API_KEY not set in environment")
            return False
        
        # Use Inference API directly
        try:
            # Use Llama-3-70b-instruct as the default model
            model_name = "meta-llama/Llama-3-70b-instruct"
            logger.info(f"Using model: {model_name}")
            
            API_URL = f"https://api-inference.huggingface.co/models/{model_name}"
            
            # Send a simple query
            headers = {"Authorization": f"Bearer {api_key}"}
            payload = {
                "inputs": "What is the first verse of the Bible?",
                "parameters": {
                    "temperature": 0.7,
                    "max_length": 100
                }
            }
            
            logger.info("Sending request to HuggingFace Inference API")
            response = requests.post(API_URL, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info("Direct inference test successful!")
                logger.info(f"Response: {response.json()}")
                return True
            else:
                logger.error(f"Inference API error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error in direct inference test: {e}")
            return False
    except ImportError:
        logger.error("Requests package not installed. Install with: pip install requests")
        return False

def main():
    """Run all HuggingFace integration tests"""
    logger.info("Starting HuggingFace API integration tests")
    
    # Test 1: Basic HuggingFace API connection
    api_success = test_huggingface_api_connection()
    if not api_success:
        logger.error("Failed to connect to HuggingFace API. Check your API key and internet connection.")
    
    # Test 2: DSPy integration with HuggingFace (only if API test succeeded)
    if api_success:
        dspy_success = test_dspy_huggingface_integration()
        if not dspy_success:
            logger.error("Failed to integrate HuggingFace with DSPy.")
    else:
        logger.warning("Skipping DSPy integration test due to API connection failure.")
        dspy_success = False
    
    # Test 3: Direct inference test (only if API test succeeded)
    if api_success:
        direct_success = test_direct_inference()
        if not direct_success:
            logger.error("Failed to run direct inference with HuggingFace API.")
    else:
        logger.warning("Skipping direct inference test due to API connection failure.")
        direct_success = False
    
    # Overall status
    if api_success and dspy_success and direct_success:
        logger.info("All HuggingFace integration tests passed successfully!")
        return 0
    else:
        logger.warning("Some HuggingFace integration tests failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 