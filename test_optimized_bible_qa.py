#!/usr/bin/env python3
"""
Test Optimized Bible QA Model

This script tests the optimized Bible QA model, supporting both single-turn
and multi-turn conversation modes.

Usage:
    python test_optimized_bible_qa.py --model-path models/dspy/bible_qa_optimized/bible_qa_bootstrap_few_shot.py
    python test_optimized_bible_qa.py --conversation  # Interactive mode with conversation history
"""

import os
import sys
import json
import logging
import argparse
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

import dspy
import dspy_json_patch  # Apply JSON patch

# Enable experimental features for DSPy 2.6
dspy.settings.experimental = True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_optimized_bible_qa.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env.dspy')
os.makedirs("logs", exist_ok=True)

def configure_lm_studio():
    """Configure DSPy to use LM Studio."""
    try:
        lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
        model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
        logger.info(f"Configuring LM Studio: {lm_studio_api}, model: {model_name}")
        lm = dspy.LM(
            model_type="openai",
            model=model_name,
            api_base=lm_studio_api,
            api_key="dummy",
            config={"temperature": 0.7, "max_tokens": 1024}  # Higher temperature for more creative responses
        )
        dspy.configure(lm=lm)
        return True
    except Exception as e:
        logger.error(f"LM Studio configuration failed: {e}")
        return False

class BibleQASignature(dspy.Signature):
    """Answer questions about Bible verses with theological accuracy."""
    context = dspy.InputField(desc="Biblical context or verse")
    question = dspy.InputField(desc="Question about the biblical context")
    history = dspy.InputField(desc="Previous conversation turns", default=[])
    answer = dspy.OutputField(desc="Answer to the question")

class BibleQAModule(dspy.Module):
    """Chain of Thought module for Bible QA with theological checks."""
    def __init__(self):
        super().__init__()
        self.qa_model = dspy.ChainOfThought(BibleQASignature)

    def forward(self, context, question, history=None):
        prediction = self.qa_model(context=context, question=question, history=history or [])
        # Simple check for theological terms
        if "god" in question.lower():
            theological_terms = ["god", "elohim", "yhwh"]
            has_term = any(term in prediction.answer.lower() for term in theological_terms)
            if not has_term:
                logger.warning("Answer should reference theological terms when relevant.")
        return prediction

def load_model(model_path):
    """Load the optimized model."""
    try:
        if not os.path.exists(model_path):
            logger.error(f"Model path not found: {model_path}")
            return None
            
        logger.info(f"Loading model from {model_path}")
        
        # If the path ends with .py, try to import it as a module
        if model_path.endswith('.py'):
            try:
                # Load the Python module dynamically
                module_name = Path(model_path).stem
                spec = importlib.util.spec_from_file_location(module_name, model_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check if it has get_model function
                if hasattr(module, 'get_model'):
                    model = module.get_model()
                    logger.info(f"Model loaded successfully from Python module: {type(model).__name__}")
                    return model
                else:
                    logger.warning(f"Module {module_name} does not have get_model function")
            except Exception as e:
                logger.warning(f"Error loading model from Python module: {e}")
        
        # Fallback to default model
        logger.info("Using default BibleQAModule as fallback")
        return BibleQAModule()
            
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None

def run_interactive_session(model, use_conversation=False):
    """Run an interactive session with the model."""
    logger.info("Starting interactive session")
    print("\nBible QA Interactive Session")
    print("============================")
    print("Type 'exit' to quit, 'clear' to clear conversation history\n")
    
    # Bible context for demonstration - can be modified or entered by user
    default_context = """
    Genesis 1:1-3: "In the beginning God created the heaven and the earth. And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters. And God said, Let there be light: and there was light."
    
    John 3:16: "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."
    
    Psalm 23:1-4: "The LORD is my shepherd; I shall not want. He maketh me to lie down in green pastures: he leadeth me beside the still waters. He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake. Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me; thy rod and thy staff they comfort me."
    """
    
    print(f"Context:\n{default_context}\n")
    
    history = []
    
    while True:
        question = input("Ask a question (or 'exit' to quit, 'clear' to reset): ")
        
        if question.lower() == 'exit':
            break
        if question.lower() == 'clear':
            history = []
            print("Conversation history cleared")
            continue
            
        try:
            # Make prediction
            if use_conversation:
                # Use conversation history
                prediction = model(context=default_context, question=question, history=history)
                
                # Store the conversation turn
                history.append({
                    "question": question,
                    "answer": prediction.answer
                })
                
                # Print the answer with history
                print(f"\nAnswer: {prediction.answer}")
                print(f"Conversation history: {len(history)} turns\n")
            else:
                # Single-turn mode
                prediction = model(context=default_context, question=question, history=[])
                print(f"\nAnswer: {prediction.answer}\n")
                
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            print(f"Error: {e}")
    
    print("Session ended")

def test_sample_questions(model, sample_questions=None):
    """Test the model on sample questions."""
    if sample_questions is None:
        sample_questions = [
            "Who created the heaven and the earth?",
            "What does John 3:16 say about salvation?",
            "Who is the shepherd in Psalm 23?",
            "What does 'Elohim' refer to in Genesis?",
            "What is the meaning of 'begotten Son'?"
        ]
    
    context = "Genesis 1:1-3, John 3:16, Psalm 23:1-4, Strong's H430 (Elohim) - God, plural form"
    
    print("\nTesting model on sample questions:")
    print("==================================")
    
    results = []
    for question in sample_questions:
        try:
            result = model(context=context, question=question, history=[])
            print(f"\nQ: {question}")
            print(f"A: {result.answer}")
            results.append({"question": question, "answer": result.answer})
        except Exception as e:
            logger.error(f"Error testing question '{question}': {e}")
            print(f"Error on question '{question}': {e}")
    
    return results

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test the optimized Bible QA model")
    parser.add_argument("--model-path", default="models/dspy/bible_qa_optimized/bible_qa_bootstrap_few_shot.py", 
                        help="Path to the optimized model")
    parser.add_argument("--conversation", action="store_true", 
                        help="Enable conversation mode with history")
    parser.add_argument("--sample-only", action="store_true",
                        help="Run only on sample questions, no interactive mode")
    return parser.parse_args()

def main():
    """Main function to run the test."""
    args = parse_args()
    
    if not configure_lm_studio():
        logger.error("LM Studio configuration failed. Exiting.")
        sys.exit(1)
    
    model = load_model(args.model_path)
    if not model:
        logger.error("Failed to load model. Exiting.")
        sys.exit(1)
    
    if args.sample_only:
        test_sample_questions(model)
    else:
        if args.conversation:
            print("Running in conversation mode (with history)")
        else:
            print("Running in single-turn mode (no history)")
        
        run_interactive_session(model, use_conversation=args.conversation)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 