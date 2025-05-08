#!/usr/bin/env python
"""
Test script for verifying Claude API integration with BibleScholarProject

This script checks whether the Claude API is properly configured and can be used
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

def test_claude_api_connection():
    """Test basic connection to Claude API"""
    try:
        import anthropic
        logger.info("Anthropic package successfully imported")
        
        # Load API key from environment
        load_dotenv('.env.dspy')
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not set in environment")
            return False
            
        # Create client
        client = anthropic.Anthropic(api_key=api_key)
        
        # Test API call with simple prompt
        try:
            prompt = "Please provide a short explanation of what the Bible is."
            response = client.messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229"),
                max_tokens=100,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Print the response
            logger.info("Claude API test successful!")
            logger.info(f"Prompt: {prompt}")
            logger.info(f"Response: {response.content[0].text}")
            return True
        except Exception as e:
            logger.error(f"Error making API call to Claude: {e}")
            return False
    except ImportError:
        logger.error("Anthropic package not installed. Install with: pip install anthropic")
        return False

def test_dspy_claude_integration():
    """Test DSPy integration with Claude"""
    try:
        import dspy
        from src.dspy_programs.huggingface_integration import configure_claude_model
        
        logger.info("Testing DSPy integration with Claude")
        
        # Load API key from environment
        load_dotenv('.env.dspy')
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not set in environment")
            return False
        
        # Configure Claude as the LM for DSPy
        try:
            lm = configure_claude_model(api_key=api_key)
            dspy.settings.configure(lm=lm)
            
            # Define a simple DSPy signature
            class SimpleQA(dspy.Signature):
                question = dspy.InputField()
                answer = dspy.OutputField()
            
            # Create a simple module
            basic_qa = dspy.Predict(SimpleQA)
            
            # Test the module
            result = basic_qa(question="What is the first verse of the Bible?")
            
            logger.info("DSPy Claude integration test successful!")
            logger.info(f"Question: What is the first verse of the Bible?")
            logger.info(f"Answer: {result.answer}")
            return True
        except Exception as e:
            logger.error(f"Error in DSPy Claude integration: {e}")
            return False
    except ImportError as e:
        logger.error(f"Error importing required packages: {e}")
        return False

def test_bible_qa_with_claude():
    """Test the Bible QA module with Claude as the LM"""
    try:
        import dspy
        from src.dspy_programs.huggingface_integration import configure_claude_model, BibleQAModule
        
        logger.info("Testing Bible QA module with Claude")
        
        # Load API key from environment
        load_dotenv('.env.dspy')
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not set in environment")
            return False
        
        # Configure Claude as the LM for DSPy
        try:
            lm = configure_claude_model(api_key=api_key)
            dspy.settings.configure(lm=lm)
            
            # Create the Bible QA module
            bible_qa = BibleQAModule()
            
            # Test with a simple Bible question
            context = "In the beginning God created the heavens and the earth."
            question = "Who created the heavens and the earth?"
            
            result = bible_qa(context=context, question=question)
            
            logger.info("Bible QA with Claude test successful!")
            logger.info(f"Context: {context}")
            logger.info(f"Question: {question}")
            logger.info(f"Answer: {result.answer}")
            return True
        except Exception as e:
            logger.error(f"Error in Bible QA Claude test: {e}")
            return False
    except ImportError as e:
        logger.error(f"Error importing required packages: {e}")
        return False

def main():
    """Run all Claude integration tests"""
    logger.info("Starting Claude API integration tests")
    
    # Test 1: Basic Claude API connection
    api_success = test_claude_api_connection()
    if not api_success:
        logger.error("Failed to connect to Claude API. Check your API key and internet connection.")
    
    # Test 2: DSPy integration with Claude
    dspy_success = test_dspy_claude_integration()
    if not dspy_success:
        logger.error("Failed to integrate Claude with DSPy.")
    
    # Test 3: Bible QA with Claude
    bible_qa_success = test_bible_qa_with_claude()
    if not bible_qa_success:
        logger.error("Failed to run Bible QA with Claude.")
    
    # Overall status
    if api_success and dspy_success and bible_qa_success:
        logger.info("All Claude integration tests passed successfully!")
        return 0
    else:
        logger.warning("Some Claude integration tests failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 