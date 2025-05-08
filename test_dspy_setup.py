#!/usr/bin/env python3
"""
Simple test script to check if DSPy is working correctly with LM Studio.
"""

import os
import sys
import traceback
import dspy
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.dspy')

def main():
    """Test DSPy configuration with LM Studio."""
    print("Testing DSPy configuration with LM Studio...")
    
    # Get LM Studio API URL
    lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
    model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "gguf-flan-t5-small")
    
    print(f"Using LM Studio API at: {lm_studio_api}")
    print(f"Using model: {model_name}")
    
    # Print DSPy version
    print(f"DSPy version: {dspy.__version__}")
    
    try:
        # Configure DSPy with LM Studio as an OpenAI-compatible endpoint
        print("\nStep 1: Creating LM object...")
        lm = dspy.LM(
            model_type="openai", 
            model=model_name,
            api_base=lm_studio_api,
            api_key="dummy"  # LM Studio doesn't need a real key
        )
        print("LM object created successfully")
        
        print("\nStep 2: Configuring DSPy settings...")
        dspy.configure(lm=lm)
        print("DSPy settings configured successfully")
        
        print("\nDSPy configuration successful!")
        
        # Create a simple signature
        print("\nStep 3: Creating signature class...")
        class SimpleQuery(dspy.Signature):
            """Answer a simple question."""
            question = dspy.InputField(desc="The question to answer")
            answer = dspy.OutputField(desc="The answer to the question")
        print("Signature class created successfully")
        
        # Create a predictor
        print("\nStep 4: Creating predictor...")
        predictor = dspy.Predict(SimpleQuery)
        print("Predictor created successfully")
        
        # Test the predictor
        print("\nStep 5: Testing predictor with a simple question...")
        print("Calling predictor with question: 'What is the capital of France?'")
        result = predictor(question="What is the capital of France?")
        
        print(f"Question: What is the capital of France?")
        print(f"Answer: {result.answer}")
        
        print("\nDSPy is working correctly with LM Studio!")
        return 0
    
    except Exception as e:
        print(f"\nError: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        print("\nDSPy configuration failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 