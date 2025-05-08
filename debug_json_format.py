#!/usr/bin/env python3
"""
Debug JSON Format Issues with DSPy and LM Studio

This script helps debug JSON parsing errors when using DSPy 2.6+ with LM Studio.
It tests different configurations to identify what works and what causes errors.

Usage:
    python debug_json_format.py
"""

import os
import sys
import json
import logging
import time
import inspect
import dataclasses
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable

import dspy
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/debug_json_format.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Enable experimental features for DSPy 2.6+
dspy.settings.experimental = True

# Load environment variables
load_dotenv('.env.dspy')

# ============================
# Utility Functions
# ============================

def patch_lm_completion(lm_object):
    """
    Patch LM Studio's completion method to handle JSON parsing errors.
    """
    original_completion = lm_object.completion
    
    def patched_completion(prompt, **kwargs):
        logger.info(f"Original kwargs: {kwargs}")
        
        # Remove problematic fields known to cause issues
        if 'response_format' in kwargs:
            logger.info("Removing response_format from kwargs")
            del kwargs['response_format']
        
        # Add JSON fix - Use OpenAPI function calling format
        function_spec = {
            "name": "answer_question",
            "description": "Answer a question about the Bible",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The answer to the Bible question"
                    }
                },
                "required": ["answer"]
            }
        }
        
        try:
            # Try with function calling
            logger.info("Attempting with function specification")
            result = original_completion(prompt, functions=[function_spec], **kwargs)
            logger.info(f"Result with function spec: {result}")
            return result
        except Exception as e1:
            logger.warning(f"Function calling approach failed: {e1}")
            try:
                # Try with plain completion
                logger.info("Attempting basic completion without any JSON formatting")
                result = original_completion(prompt, **kwargs)
                logger.info(f"Plain completion result: {result}")
                
                # If result is a string, try to convert to expected format
                if isinstance(result, str):
                    logger.info("Converting string result to expected format")
                    return {"answer": result}
                
                return result
            except Exception as e2:
                logger.error(f"Both approaches failed. Final error: {e2}")
                raise e2
    
    # Replace the method
    lm_object.completion = patched_completion
    logger.info("Patched LM completion method")
    return lm_object

def configure_lm_studio():
    """Configure LM Studio as the LM provider."""
    try:
        # Get the API URL and model name from environment variables
        api_url = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1")
        model_name = os.getenv("LM_STUDIO_EMBEDDING_MODEL", "mistral-nemo-instruct-2407")
        
        logger.info(f"Using LM Studio API at: {api_url}")
        logger.info(f"Using model: {model_name}")
        
        # Create the language model
        lm = dspy.LM(
            model=model_name,
            api_base=api_url,
            api_type="openai",
            api_key="lm-studio",
            max_tokens=256
        )
        
        # Apply the patch to fix JSON issues
        lm = patch_lm_completion(lm)
        
        # Configure DSPy with the patched LM
        dspy.configure(lm=lm)
        logger.info("DSPy configured with patched LM Studio")
        return True
    except Exception as e:
        logger.error(f"Error configuring LM Studio: {e}")
        return False

# ============================
# Test Classes
# ============================

class SimpleQA(dspy.Module):
    """Simple question answering module."""
    
    def __init__(self):
        super().__init__()
        self.qa = dspy.ChainOfThought('question -> answer')
    
    def forward(self, question):
        return self.qa(question=question)

class JsonStructuredQA(dspy.Module):
    """Structured QA module."""
    
    def __init__(self):
        super().__init__()
        self.qa = dspy.ChainOfThought('question -> answer')
    
    def forward(self, question):
        response = self.qa(question=question)
        logger.info(f"Raw response: {response}")
        # Convert response to dict if it's a string
        if isinstance(response, str):
            logger.info("Converting string response to dict")
            return {"answer": response}
        return response

# ============================
# Test Functions
# ============================

def test_simple_qa():
    """Test a simple QA module."""
    logger.info("Testing simple QA module...")
    try:
        model = SimpleQA()
        question = "What is the first verse in Genesis?"
        result = model(question=question)
        logger.info(f"Question: {question}")
        logger.info(f"Answer: {result.answer}")
        return True
    except Exception as e:
        logger.error(f"Simple QA test failed: {e}")
        return False

def test_json_structured_qa():
    """Test a JSON structured QA module."""
    logger.info("Testing JSON structured QA module...")
    try:
        model = JsonStructuredQA()
        question = "What is the first verse in Genesis?"
        result = model(question=question)
        logger.info(f"Question: {question}")
        logger.info(f"Answer: {result}")
        return True
    except Exception as e:
        logger.error(f"JSON structured QA test failed: {e}")
        return False

def test_dspy_predictor():
    """Test DSPy's Predictor class."""
    logger.info("Testing DSPy Predictor...")
    try:
        # Define a predictor for Bible questions
        class BiblePredictor(dspy.Predictor):
            question = dspy.InputField()
            answer = dspy.OutputField()
        
        # Create an instance
        predictor = BiblePredictor()
        
        # Test it
        question = "What is the first verse in Genesis?"
        result = predictor(question=question)
        logger.info(f"Question: {question}")
        logger.info(f"Answer: {result.answer}")
        return True
    except Exception as e:
        logger.error(f"DSPy Predictor test failed: {e}")
        return False

def test_dspy_signature():
    """Test DSPy's Signature with fix."""
    logger.info("Testing DSPy Signature with custom fix...")
    try:
        # Define a signature for Bible QA
        BibleQA = dspy.Signature(
            inputs=["question"],
            outputs=["answer"]
        )
        
        # Create a program with the signature
        program = dspy.ChainOfThought(BibleQA)
        
        # Test it
        question = "What is the first verse in Genesis?"
        result = program(question=question)
        logger.info(f"Question: {question}")
        logger.info(f"Answer: {result.answer}")
        return True
    except Exception as e:
        logger.error(f"DSPy Signature test failed: {e}")
        return False

def apply_json_fix():
    """Apply JSON format fix to DSPy."""
    logger.info("Applying JSON format fix to DSPy...")
    try:
        # Monkey patch DSPy's JSON handling
        import dspy.utils
        import dspy.utils.parallelizer
        
        # Create a backup of the original function
        original_parse = getattr(dspy.utils.parallelizer, 'parse_json')
        
        def patched_parse_json(text, **kwargs):
            """Patched JSON parsing function that handles string responses."""
            try:
                # First try regular parsing
                return original_parse(text, **kwargs)
            except Exception as e:
                logger.warning(f"Original parse failed: {e}")
                # If it's a string, wrap it in a dict
                if isinstance(text, str):
                    logger.info(f"Converting string to JSON: '{text}'")
                    return {"answer": text.strip()}
                raise e
        
        # Apply the patch
        setattr(dspy.utils.parallelizer, 'parse_json', patched_parse_json)
        logger.info("DSPy JSON parsing patched successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to apply JSON fix: {e}")
        return False

def test_theological_module():
    """Test a theological QA module with Strong's IDs."""
    logger.info("Testing theological QA module...")
    try:
        # Define a simple theological QA module
        class TheologicalQA(dspy.Module):
            def __init__(self):
                super().__init__()
                self.qa = dspy.ChainOfThought('context, question -> answer')
            
            def forward(self, context, question):
                return self.qa(context=context, question=question)
        
        # Create an instance
        model = TheologicalQA()
        
        # Test with Strong's ID question
        context = "H430 - Elohim: God; the plural form of Eloah, which can refer to the one true God or false gods."
        question = "What does Elohim (H430) mean in the Bible?"
        
        result = model(context=context, question=question)
        logger.info(f"Context: {context}")
        logger.info(f"Question: {question}")
        logger.info(f"Answer: {result.answer}")
        return True
    except Exception as e:
        logger.error(f"Theological QA test failed: {e}")
        return False

def test_better_together():
    """Test the BetterTogether optimizer."""
    logger.info("Testing BetterTogether optimizer...")
    try:
        # Define a simple metric
        class SimpleMetric(dspy.Metric):
            def __call__(self, gold, pred, **kwargs):
                logger.info(f"Gold: {gold}")
                logger.info(f"Pred: {pred}")
                # Simple exact match
                return 1.0 if gold.answer.lower() in pred.answer.lower() else 0.0
        
        # Create a simple dataset
        dataset = [
            {"question": "What is the first verse in Genesis?", 
             "answer": "In the beginning God created the heaven and the earth."}
        ]
        
        # Create training examples
        train_data = [dspy.Example(**item) for item in dataset]
        
        # Create a simple module
        predictor = dspy.Predict("question -> answer")
        
        # Create the optimizer
        bt_optimizer = dspy.BetterTogether(metric=SimpleMetric())
        
        # Run optimization with a single iteration
        optimized = bt_optimizer.compile(
            predictor,
            trainset=train_data,
            max_bootstrapped_demos=1,
            max_labeled_demos=1,
            num_iterations=1
        )
        
        # Test the optimized model
        result = optimized(question="What is the first book of the Bible?")
        logger.info(f"Optimized result: {result.answer}")
        return True
    except Exception as e:
        logger.error(f"BetterTogether test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# ============================
# Main Function
# ============================

def main():
    """Main function."""
    logger.info("===== DSPy JSON Format Debug =====")
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Step 1: Configure LM Studio
    if not configure_lm_studio():
        logger.error("Failed to configure LM Studio")
        return 1
    
    # Apply JSON fix
    apply_json_fix()
    
    # Run tests
    tests = [
        ("Simple QA", test_simple_qa),
        ("JSON Structured QA", test_json_structured_qa),
        ("DSPy Predictor", test_dspy_predictor),
        ("DSPy Signature", test_dspy_signature),
        ("Theological Module", test_theological_module),
        ("BetterTogether Optimizer", test_better_together)
    ]
    
    results = {}
    for name, test_func in tests:
        logger.info(f"\n===== Testing {name} =====")
        try:
            success = test_func()
            results[name] = "SUCCESS" if success else "FAILED"
        except Exception as e:
            logger.error(f"Error running {name}: {e}")
            results[name] = "ERROR"
    
    # Print summary
    logger.info("\n===== Test Results =====")
    for name, result in results.items():
        logger.info(f"{name}: {result}")
    
    # Check if all tests passed
    all_passed = all(result == "SUCCESS" for result in results.values())
    
    # Write patch file if tests succeeded
    if all_passed:
        write_dspy_patch()
    
    logger.info("===== Debug Complete =====")
    return 0 if all_passed else 1

def write_dspy_patch():
    """Write a patch file to fix DSPy's JSON parsing."""
    patch_file = "dspy_json_patch.py"
    
    content = """#!/usr/bin/env python3
\"\"\"
DSPy JSON Patch

This script patches DSPy's JSON parsing to fix issues with LM Studio.
Import this file after importing DSPy to apply the patch.

Usage:
    import dspy
    import dspy_json_patch  # Apply the patch
\"\"\"

import logging
import inspect
import sys
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

def patch_dspy():
    \"\"\"Patch DSPy's JSON parsing.\"\"\"
    try:
        import dspy
        import dspy.utils
        import dspy.utils.parallelizer
        
        # Get the original parse function
        original_parse = getattr(dspy.utils.parallelizer, 'parse_json')
        
        def patched_parse_json(text, **kwargs):
            \"\"\"Patched JSON parsing function that handles string responses.\"\"\"
            try:
                # First try regular parsing
                return original_parse(text, **kwargs)
            except Exception as e:
                logger.warning(f"Original parse failed: {e}")
                # If it's a string, wrap it in a dict
                if isinstance(text, str):
                    logger.info(f"Converting string to JSON object: '{text}'")
                    return {"answer": text.strip()}
                raise e
        
        # Apply the patch
        setattr(dspy.utils.parallelizer, 'parse_json', patched_parse_json)
        logger.info("DSPy JSON parsing patched successfully")
        
        # Patch LM for LM Studio compatibility
        original_lm_class = dspy.LM
        
        class PatchedLM(original_lm_class):
            def __init__(self, *args, **kwargs):
                # Remove response_format if present
                if 'response_format' in kwargs:
                    logger.info("Removing response_format from LM kwargs")
                    del kwargs['response_format']
                
                super().__init__(*args, **kwargs)
            
            def completion(self, prompt, **kwargs):
                # Remove response_format if present
                if 'response_format' in kwargs:
                    logger.info("Removing response_format from completion kwargs")
                    del kwargs['response_format']
                
                try:
                    return super().completion(prompt, **kwargs)
                except Exception as e:
                    logger.error(f"Error in patched completion: {e}")
                    # Return a default response as fallback
                    return {"answer": "Error generating response"}
        
        # Replace the LM class
        dspy.LM = PatchedLM
        logger.info("DSPy LM class patched successfully")
        
        # Enable experimental features
        dspy.settings.experimental = True
        logger.info("DSPy experimental features enabled")
        
        return True
    except Exception as e:
        logger.error(f"Failed to patch DSPy: {e}")
        return False

# Apply the patch
patch_applied = patch_dspy()
if patch_applied:
    print("DSPy JSON patch applied successfully")
else:
    print("Failed to apply DSPy JSON patch")
"""
    
    with open(patch_file, "w") as f:
        f.write(content)
    
    logger.info(f"Wrote DSPy JSON patch to {patch_file}")
    
    # Create a batch file to apply the patch
    batch_file = "apply_dspy_patch.bat"
    batch_content = """@echo off
echo ===== Applying DSPy JSON Patch =====

echo Creating backup of train_and_optimize_bible_qa.py...
copy train_and_optimize_bible_qa.py train_and_optimize_bible_qa.py.bak

echo Updating train_and_optimize_bible_qa.py to use patch...
powershell -Command "(Get-Content train_and_optimize_bible_qa.py) -replace 'import dspy', 'import dspy\\nimport dspy_json_patch  # Apply JSON patch' | Set-Content train_and_optimize_bible_qa.py"

echo Patch applied! Run the following command to test:
echo   python run_optimization.py --method better_together --iterations 3 --target 0.95
echo.
echo Press any key to continue...
pause > nul
"""
    
    with open(batch_file, "w") as f:
        f.write(batch_content)
    
    logger.info(f"Wrote batch file to {batch_file}")

if __name__ == "__main__":
    sys.exit(main()) 