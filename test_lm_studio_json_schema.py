#!/usr/bin/env python3
"""
Test LM Studio JSON Schema Integration with DSPy

This script verifies that LM Studio's JSON schema capability is correctly integrated with DSPy.
It demonstrates how to ensure structured JSON output from LM Studio models using JSON Schema.

Usage:
    python test_lm_studio_json_schema.py
"""
import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_lm_studio_json_schema.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def setup():
    """Set up environment and imports."""
    # Load environment variables from .env.dspy
    load_dotenv('.env.dspy')
    
    try:
        # Import required modules
        import dspy
        import dspy_json_patch
        
        # Enable experimental features for DSPy 2.6
        dspy.settings.experimental = True
        
        # Configure LM Studio
        lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://localhost:1234/v1")
        model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
        
        logger.info(f"Using LM Studio API at {lm_studio_api} with model {model_name}")
        
        # Create LM configuration for DSPy 2.6
        lm = dspy.LM(
            model_type="openai", 
            model=model_name,
            api_base=lm_studio_api,
            api_key="dummy",
            config={"temperature": 0.1, "max_tokens": 1024}
        )
        
        dspy.configure(lm=lm)
        return True
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return False

def test_direct_api_call():
    """Test direct API call to LM Studio with JSON schema."""
    try:
        # Get environment variables
        api_url = os.environ.get("LM_STUDIO_API_URL", "http://localhost:1234/v1")
        model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
        
        # Create a simple schema
        schema = {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The answer to the question"
                }
            },
            "required": ["answer"]
        }
        
        # Create request body - use proper format for LM Studio
        request_body = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a Biblical scholar."},
                {"role": "user", "content": "What did God create in Genesis 1:1?"}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "bible_answer",
                    "schema": schema
                }
            }
        }
        
        # Make the API call
        logger.info("Making direct API call to LM Studio with JSON schema")
        response = requests.post(
            f"{api_url.rstrip('/')}/chat/completions",
            json=request_body,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"API call successful, status code: {response.status_code}")
            
            # Extract the content from the response
            content = None
            if "choices" in result and len(result["choices"]) > 0:
                if "message" in result["choices"][0]:
                    content = result["choices"][0]["message"].get("content", "")
                elif "text" in result["choices"][0]:
                    content = result["choices"][0]["text"]
            
            if content:
                try:
                    parsed_content = json.loads(content)
                    if "answer" in parsed_content:
                        logger.info(f"Received answer: {parsed_content['answer']}")
                        return True
                    else:
                        logger.warning("Response doesn't contain 'answer' field")
                        return False
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Raw content: {content}")
                    return False
            else:
                logger.error("No content in response")
                return False
        else:
            logger.error(f"API call failed with status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Direct API call test failed: {e}")
        return False

def test_dspy_integration():
    """Test JSON schema integration with DSPy."""
    try:
        import dspy
        import dspy_json_patch
        
        # Define a simple signature with a single output field
        class SimpleBibleQA(dspy.Signature):
            """Answer questions about Bible verses."""
            question = dspy.InputField(desc="Question about the Bible")
            answer = dspy.OutputField(desc="Answer to the question")
        
        predictor = dspy.Predict(SimpleBibleQA)
        question = "What did God create in Genesis 1:1?"
        
        logger.info(f"Testing DSPy integration with question: {question}")
        
        # Try to use the predictor
        try:
            result = predictor(question=question)
            logger.info(f"Received answer: {result.answer}")
            return True
        except Exception as e:
            logger.error(f"DSPy prediction failed: {e}")
            return False
    except Exception as e:
        logger.error(f"DSPy integration test failed: {e}")
        return False

def main():
    """Run the JSON schema tests."""
    results = {}
    
    # Set up environment
    results['setup'] = setup()
    if not results['setup']:
        logger.error("Setup failed. Exiting.")
        return False
    
    # Run tests - start with direct API call which is more reliable
    results['direct_api_call'] = test_direct_api_call()
    
    # Only try DSPy integration if direct API call works
    if results['direct_api_call']:
        results['dspy_integration'] = test_dspy_integration()
    else:
        results['dspy_integration'] = False
        logger.warning("Skipping DSPy integration test as direct API call failed")
    
    # Report results
    logger.info("\nTest Results:")
    all_passed = True
    for test, passed in results.items():
        logger.info(f"  {test}: {'PASSED' if passed else 'FAILED'}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("\nAll tests PASSED! LM Studio JSON schema integration is working correctly.")
        return True
    else:
        logger.error("\nSome tests FAILED. Please check the logs for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 