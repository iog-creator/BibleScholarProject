#!/usr/bin/env python
"""
Test script for directly verifying Claude API functionality without DSPy integration
"""

import os
import sys
import logging
import json
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

def test_claude_direct():
    """Test direct API calls to Claude"""
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
        
        # Test a series of API calls with bible-related prompts
        test_prompts = [
            "What is the first verse of Genesis?",
            "Who was Moses?",
            "Explain the significance of the Exodus in the Bible.",
        ]
        
        for prompt in test_prompts:
            try:
                response = client.messages.create(
                    model=os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229"),
                    max_tokens=150,
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Print the response
                logger.info(f"\nPrompt: {prompt}")
                logger.info(f"Response: {response.content[0].text}\n")
            except Exception as e:
                logger.error(f"Error making API call to Claude for prompt '{prompt}': {e}")
                return False
        
        # Test with a specific theology question that requires reasoning
        theology_prompt = "Explain the concept of the Trinity in Christianity and how it relates to monotheism."
        
        try:
            response = client.messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229"),
                max_tokens=250,
                temperature=0.2,
                messages=[
                    {"role": "user", "content": theology_prompt}
                ]
            )
            
            logger.info(f"\nTheology Prompt: {theology_prompt}")
            logger.info(f"Response: {response.content[0].text}\n")
        except Exception as e:
            logger.error(f"Error with theology prompt: {e}")
            return False
            
        # Test with a Hebrew word analysis
        hebrew_prompt = "Explain the meaning and significance of the Hebrew word 'Elohim' in the Bible."
        
        try:
            response = client.messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229"),
                max_tokens=250,
                temperature=0.2,
                messages=[
                    {"role": "user", "content": hebrew_prompt}
                ]
            )
            
            logger.info(f"\nHebrew Analysis Prompt: {hebrew_prompt}")
            logger.info(f"Response: {response.content[0].text}\n")
        except Exception as e:
            logger.error(f"Error with Hebrew analysis prompt: {e}")
            return False
        
        logger.info("All direct Claude API tests completed successfully!")
        return True
    except ImportError:
        logger.error("Anthropic package not installed. Install with: pip install anthropic")
        return False

def main():
    """Run direct Claude API tests"""
    logger.info("Starting direct Claude API tests")
    
    success = test_claude_direct()
    
    if success:
        logger.info("All direct Claude API tests passed successfully!")
        return 0
    else:
        logger.error("Some direct Claude API tests failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 