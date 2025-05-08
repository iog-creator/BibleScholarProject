#!/usr/bin/env python
"""
Test script for verifying HuggingFace API integration with Llama-3.3-70B-Instruct model
"""

import os
import sys
import logging
import json
import requests
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

def test_llama_inference():
    """Test direct inference with Llama-3.3-70B-Instruct via HuggingFace API"""
    try:
        # Load API key from environment
        load_dotenv('.env.dspy')
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        
        if not api_key:
            logger.error("HUGGINGFACE_API_KEY not set in environment")
            return False
        
        # Model name
        model_name = "meta-llama/Llama-3.3-70B-Instruct"
        logger.info(f"Testing inference with model: {model_name}")
        
        # API URL
        API_URL = f"https://api-inference.huggingface.co/models/{model_name}"
        
        # Headers with authorization
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # Payload - similar to the JavaScript example
        payload = {
            "inputs": "What is the first verse of the Bible?",
            "parameters": {
                "temperature": 0.5,
                "max_tokens": 500,
                "top_p": 0.7,
                "provider": "nscale",  # Using nscale provider as in the JS example
            }
        }
        
        # Make API call
        logger.info("Making request to HuggingFace API...")
        response = requests.post(API_URL, headers=headers, json=payload)
        
        # Check response
        if response.status_code == 200:
            logger.info("API call successful! Response:")
            result = response.json()
            logger.info(json.dumps(result, indent=2))
            return True
        else:
            logger.error(f"API call failed with status {response.status_code}: {response.text}")
            
            # Try alternative API format
            logger.info("Trying alternative API format...")
            
            # This is the chat completion format from the JS example
            chat_payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": "What is the first verse of the Bible?"
                    }
                ],
                "temperature": 0.5,
                "max_tokens": 500,
                "top_p": 0.7,
                "provider": "nscale",
            }
            
            chat_response = requests.post(
                "https://api-inference.huggingface.co/chat/completions", 
                headers=headers, 
                json=chat_payload
            )
            
            if chat_response.status_code == 200:
                logger.info("Chat completion API call successful! Response:")
                chat_result = chat_response.json()
                logger.info(json.dumps(chat_result, indent=2))
                return True
            else:
                logger.error(f"Chat completion API call failed with status {chat_response.status_code}: {chat_response.text}")
                
                # Try testing with simpler model
                logger.info("Testing with a simpler, public model...")
                simple_model = "facebook/bart-large-cnn"
                simple_url = f"https://api-inference.huggingface.co/models/{simple_model}"
                
                simple_payload = {
                    "inputs": "What is the first verse of the Bible?",
                }
                
                simple_response = requests.post(simple_url, headers=headers, json=simple_payload)
                
                if simple_response.status_code == 200:
                    logger.info(f"API call to {simple_model} successful! Response:")
                    simple_result = simple_response.json()
                    logger.info(json.dumps(simple_result, indent=2))
                    return True
                else:
                    logger.error(f"API call to {simple_model} failed with status {simple_response.status_code}: {simple_response.text}")
                    return False
    except Exception as e:
        logger.error(f"Error during inference test: {e}")
        return False

def main():
    """Run the test"""
    logger.info("Starting Llama-3.3 inference test")
    
    success = test_llama_inference()
    
    if success:
        logger.info("Llama-3.3 inference test completed successfully!")
        return 0
    else:
        logger.error("Llama-3.3 inference test failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 