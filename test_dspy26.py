#!/usr/bin/env python
"""
Test script for DSPy 2.6 with LM Studio integration
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('.env.dspy'):
    load_dotenv('.env.dspy')
    print("Loaded environment variables from .env.dspy")

import dspy
from dspy import InputField, OutputField

# Print DSPy version
print(f"DSPy version: {dspy.__version__}")

# Configure LM Studio connection
lm_studio_url = os.environ.get('LM_STUDIO_API_URL', 'http://localhost:1234/v1')
model_name = os.environ.get('LM_STUDIO_CHAT_MODEL', 'darkidol-llama-3.1-8b-instruct-1.2-uncensored')

print(f"Connecting to LM Studio at {lm_studio_url}")
print(f"Using model: {model_name}")

# Create a language model with DSPy 2.6 API
lm = dspy.LM(
    f"openai/{model_name}", 
    api_base=lm_studio_url,
    api_key="lm-studio",
    model_type='chat'
)

# Configure DSPy to use this language model
dspy.configure(lm=lm)

# Define a simple signature for testing
class SimpleQA(dspy.Signature):
    """Answer simple questions."""
    question = InputField(desc="The question to answer")
    answer = OutputField(desc="The answer to the question")

# Create a basic module
class SimpleQAModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.qa_model = dspy.Predict(SimpleQA)
    
    def forward(self, question):
        return self.qa_model(question=question)

# Run a simple test
print("\nRunning test with DSPy 2.6...")
try:
    module = SimpleQAModule()
    result = module(question="What is the capital of France?")
    print(f"Question: What is the capital of France?")
    print(f"Answer: {result.answer}")
    print("\nTest completed successfully!")
except Exception as e:
    print(f"Error during test: {e}")
