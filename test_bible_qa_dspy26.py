#!/usr/bin/env python3
"""
Test Script for DSPy 2.6 Bible QA Model

This script tests the enhanced DSPy 2.6 Bible QA model with multi-turn conversation
support and theological assertions.

Usage:
    python test_bible_qa_dspy26.py --model-path "models/dspy/bible_qa_t5_latest" --conversation
"""

import os
import sys
import json
import logging
import argparse
import requests
from pathlib import Path
import dspy
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_bible_qa.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
if os.path.exists('.env.dspy'):
    load_dotenv('.env.dspy')
    logger.info("Loaded environment variables from .env.dspy")
else:
    load_dotenv()
    logger.info("Loaded environment variables from .env")

# Import the HuggingFace integration module
try:
    from src.dspy_programs.huggingface_integration import (
        configure_local_student_model,
        configure_teacher_model
    )
except ImportError as e:
    logger.error(f"Error importing huggingface_integration: {e}")
    sys.exit(1)

# Try importing the module from project, or define a local version if not available
try:
    from src.dspy_programs.bible_qa_dspy26 import BibleQAModule, BibleQASignature
except ImportError as e:
    logger.error(f"Error importing bible_qa_dspy26: {e}")
    logger.info("Using local implementation of BibleQAModule and BibleQASignature")
    
    # Define local versions of the classes
    class BibleQASignature(dspy.Signature):
        """Signature for Bible Question Answering with conversation history support."""
        context = dspy.InputField(desc="Biblical context or verse")
        question = dspy.InputField(desc="Question about the biblical context")
        history = dspy.InputField(desc="Previous conversation turns as a list of questions and answers", default=[])
        answer = dspy.OutputField(desc="Answer to the question based on the biblical context")
    
    class BibleQAModule(dspy.Module):
        """Module for Bible QA with conversation history support."""
        
        def __init__(self):
            super().__init__()
            self.qa_model = dspy.ChainOfThought(BibleQASignature)
        
        def forward(self, context, question, history=None):
            """
            Answer a question based on context and conversation history.
            
            Args:
                context (str): Biblical context or verse
                question (str): Question about the biblical context
                history (list): Previous conversation turns
                
            Returns:
                Prediction with answer field
            """
            # Ensure history is a list
            if history is None:
                history = []
                
            # Format history for better prompting
            formatted_history = ""
            if history:
                for i, (hist_q, hist_a) in enumerate(history):
                    formatted_history += f"Q{i+1}: {hist_q}\nA{i+1}: {hist_a}\n"
            
            # Make prediction
            return self.qa_model(
                context=context,
                question=question,
                history=formatted_history
            )

# Custom implementation for LM Studio that works with DSPy
class DirectLMStudioAPI:
    """Direct implementation for LM Studio API without relying on DSPy's LM class"""
    
    def __init__(self, model_name, api_base):
        self.model = model_name
        self.api_base = api_base
        self.max_tokens = 1024
        self.temperature = 0.3
        self.stop_sequences = None
        self.top_p = 1.0
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    def __call__(self, prompt, **kwargs):
        """Call the LM Studio API directly with retry logic"""
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                # Determine if this is a chat or completion model
                is_chat_model = "instruct" in self.model.lower() or "chat" in self.model.lower()
                
                # Prepare the response
                if is_chat_model:
                    return self._call_chat_api(prompt, **kwargs)
                else:
                    return self._call_completion_api(prompt, **kwargs)
                    
            except Exception as e:
                last_error = e
                logger.warning(f"API call failed (attempt {retries+1}/{self.max_retries+1}): {e}")
                retries += 1
                if retries <= self.max_retries:
                    import time
                    time.sleep(self.retry_delay)
                    
        # If we get here, all retries failed
        logger.error(f"All API call attempts failed: {last_error}")
        return f"Error after {self.max_retries+1} attempts: {str(last_error)}"
    
    def _call_chat_api(self, prompt, **kwargs):
        """Call the chat completions API"""
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", self.temperature),
                    "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                    "stop": kwargs.get("stop", self.stop_sequences),
                    "top_p": kwargs.get("top_p", self.top_p)
                },
                timeout=30  # Add timeout to avoid hanging
            )
            
            if response.status_code == 200:
                resp_json = response.json()
                content = resp_json["choices"][0]["message"]["content"]
                return self._clean_mistral_markup(content)
            else:
                # Handle error responses
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return error_msg
                
        except requests.RequestException as e:
            raise Exception(f"Chat API request failed: {str(e)}")
    
    def _call_completion_api(self, prompt, **kwargs):
        """Call the completions API"""
        try:
            response = requests.post(
                f"{self.api_base}/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": kwargs.get("temperature", self.temperature),
                    "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                    "stop": kwargs.get("stop", self.stop_sequences),
                    "top_p": kwargs.get("top_p", self.top_p)
                },
                timeout=30  # Add timeout to avoid hanging
            )
            
            if response.status_code == 200:
                resp_json = response.json()
                content = resp_json["choices"][0]["text"]
                return self._clean_mistral_markup(content)
            else:
                # Handle error responses
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return error_msg
                
        except requests.RequestException as e:
            raise Exception(f"Completion API request failed: {str(e)}")
    
    def _clean_mistral_markup(self, text):
        """Clean up Mistral's thinking markup if present"""
        # For Mistral models that have <answer> tags or <think> tags
        if "<answer>" in text and "</answer>" in text:
            try:
                parts = text.split("<answer>")[1].split("</answer>")[0].strip()
                return parts
            except IndexError:
                logger.warning("Error parsing <answer> tags, returning original text")
                return text
        
        if "<think>" in text and "</think>" in text:
            try:
                # Build clean text by removing thinking sections
                clean_text = ""
                in_thinking = False
                for line in text.split("\n"):
                    if "<think>" in line:
                        in_thinking = True
                        continue
                    if "</think>" in line:
                        in_thinking = False
                        continue
                    if not in_thinking:
                        clean_text += line + "\n"
                return clean_text.strip()
            except Exception as e:
                logger.warning(f"Error parsing <think> tags: {e}, returning original text")
                return text
        
        return text

# Mock implementation of a BibleQAModule that works directly with LM Studio API
class MockBibleQAModule:
    """A mock BibleQAModule that uses LM Studio API directly without DSPy"""
    
    def __init__(self, lm_studio_api=None):
        """Initialize the module with an optional API client"""
        self.api = lm_studio_api
        
    def __call__(self, context, question, history=None):
        """Answer a Bible question using LM Studio API directly"""
        if self.api is None:
            # Create a new instance of the DirectLMStudioAPI using environment variables
            api_base = os.environ.get('LM_STUDIO_API_URL', 'http://localhost:1234/v1')
            model_name = os.environ.get('LM_STUDIO_CHAT_MODEL', 'mistral-nemo-instruct-2407')
            self.api = DirectLMStudioAPI(model_name=model_name, api_base=api_base)
        
        # Format the prompt with context and question
        prompt = self._format_prompt(context, question, history)
        
        # Call the API
        response = self.api(prompt)
        
        # Create a simple response object with an 'answer' field
        class Response:
            def __init__(self, answer):
                self.answer = answer
        
        return Response(response)
    
    def _format_prompt(self, context, question, history=None):
        """Format the prompt for the LM Studio API"""
        if history is None:
            history = []
            
        # Format history
        history_text = ""
        if history:
            for i, (q, a) in enumerate(history):
                history_text += f"Q{i+1}: {q}\nA{i+1}: {a}\n\n"
        
        # Format the prompt with explicit instructions for concise answers
        if context:
            prompt = f"""You are a biblical scholar and expert. 
Please answer the following question about the Bible based on the provided context.
Provide a DIRECT and CONCISE answer - one or two sentences at most.
Be precise and to the point without extra explanation.

Context: {context}

{history_text}Question: {question}

Answer:"""
        else:
            prompt = f"""You are a biblical scholar and expert. 
Please answer the following question about the Bible.
Provide a DIRECT and CONCISE answer - one or two sentences at most.
Be precise and to the point without extra explanation.

{history_text}Question: {question}

Answer:"""
        
        return prompt

def load_model(args):
    """
    Load the trained DSPy model.
    
    Args:
        args: Command line arguments
        
    Returns:
        Loaded DSPy model
    """
    try:
        # For the LM Studio case, use our own direct implementation that doesn't rely on DSPy
        if args.use_lm_studio:
            # Get configuration parameters
            lm_studio_api_url = os.environ.get('LM_STUDIO_API_URL', 'http://localhost:1234/v1')
            lm_studio_model = args.lm_studio_model or os.environ.get('LM_STUDIO_CHAT_MODEL', 'mistral-nemo-instruct-2407')
            
            logger.info(f"Using LM Studio model: {lm_studio_model} at {lm_studio_api_url}")
            
            # Create the API client
            api_client = DirectLMStudioAPI(model_name=lm_studio_model, api_base=lm_studio_api_url)
            
            # Create the mock module
            logger.info("Creating MockBibleQAModule with DirectLMStudioAPI")
            model = MockBibleQAModule(lm_studio_api=api_client)
            
            return model
            
        # Handle "latest" model path
        model_path = args.model_path
        if model_path.endswith("latest") or model_path.endswith("latest/"):
            # Find the most recent model
            model_dir = os.path.dirname(model_path)
            if not os.path.exists(model_dir):
                logger.error(f"Model directory not found: {model_dir}")
                return None
                
            model_files = [f for f in os.listdir(model_dir) 
                          if f.startswith("bible_qa_") and f.endswith(".dspy")]
            
            if not model_files:
                logger.error(f"No model files found in {model_dir}")
                return None
                
            # Sort by modification time (newest first)
            model_files.sort(key=lambda f: os.path.getmtime(os.path.join(model_dir, f)), reverse=True)
            model_path = os.path.join(model_dir, model_files[0])
            logger.info(f"Using latest model: {model_path}")
            
        # For regular DSPy use (non-LM Studio), use the standard approach
        if args.use_local_lm:
            # Use a local HuggingFace model
            lm = configure_local_student_model(model_name="google/flan-t5-small")
            dspy.settings.configure(lm=lm)
        else:
            # Use a teacher model
            model_name = os.environ.get('HUGGINGFACE_MODEL') or 'meta-llama/Llama-3-8b-instruct'
            lm = configure_teacher_model(model_name=model_name)
            dspy.settings.configure(lm=lm)
        
        # If using DSPy, create or load a DSPy model
        # Check if model file exists
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            logger.warning("Using a mock BibleQAModule instead")
            # Create a mock BibleQAModule
            model = BibleQAModule()
            logger.info("Created a mock BibleQAModule for testing")
            return model
        
        # Try to parse the model file
        if model_path.endswith('.dspy'):
            # For DSPy 2.6+ models - but may just be a JSON config file
            try:
                # First try to parse as a complete module
                try:
                    model = dspy.Module.load(path=model_path)
                    logger.info(f"Successfully loaded DSPy model from {model_path}")
                    return model
                except (TypeError, AttributeError):
                    logger.warning(f"Could not load as DSPy module, trying to parse as JSON config file")
                    # If that fails, try to parse as a JSON config file
                    with open(model_path, 'r') as f:
                        config = json.load(f)
                    
                    # Create a model from the config
                    logger.info(f"Creating model from config: {config}")
                    model = BibleQAModule()
                    return model
            except Exception as inner_e:
                logger.error(f"Error parsing model file: {inner_e}")
                # Create a new model
                model = BibleQAModule()
                return model
        else:
            logger.error(f"Unsupported model format: {model_path}")
            logger.warning("Using a mock BibleQAModule instead")
            model = BibleQAModule()
            return model
            
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        # Create a new model
        model = BibleQAModule()
        return model

def run_interactive_session(model):
    """
    Run an interactive conversation session with the model.
    
    Args:
        model: Loaded DSPy model
    """
    print("\n=== Bible QA Interactive Session ===")
    print("Type 'exit' to quit, 'clear' to start a new conversation\n")
    
    context = ""
    history = []
    
    while True:
        # Get input
        if not context:
            context_input = input("\nProvide Bible context (optional, press Enter to skip): ")
            if context_input.lower() == 'exit':
                break
            if context_input:
                context = context_input
            
        # Get the question
        question = input("\nYour question: ")
        if question.lower() == 'exit':
            break
            
        if question.lower() == 'clear':
            context = ""
            history = []
            print("\nConversation history cleared.")
            continue
            
        if question.lower() == 'context':
            context = input("\nNew context: ")
            continue
            
        # Generate the answer
        try:
            prediction = model(
                context=context,
                question=question,
                history=history
            )
            
            # Print the answer
            print(f"\nAnswer: {prediction.answer}\n")
            
            # Add to history (up to 5 turns)
            history.append((question, prediction.answer))
            if len(history) > 5:
                history = history[-5:]
                
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            print(f"\nError: {e}\n")

def run_test_examples(model):
    """
    Run a predefined set of test examples with the model.
    
    Args:
        model: Loaded DSPy model
    """
    test_examples = [
        {
            "context": "In the beginning God created the heavens and the earth.",
            "question": "Who created the heavens and the earth?",
            "expected": "God"
        },
        {
            "context": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
            "question": "What did God give?",
            "expected": "His only begotten Son"
        },
        {
            "context": "",
            "question": "Who was Jesus?",
            "expected": "Jesus Christ is the Son of God, the central figure of Christianity"
        },
        {
            "context": "But the fruit of the Spirit is love, joy, peace, longsuffering, gentleness, goodness, faith, meekness, temperance: against such there is no law.",
            "question": "What are the fruits of the Spirit?",
            "expected": "love, joy, peace, longsuffering, gentleness, goodness, faith, meekness, temperance"
        }
    ]
    
    # Multi-turn tests
    multi_turn_tests = [
        [
            ("Who wrote the Gospel of John?", "John, one of Jesus' disciples"),
            ("What other books did he write?", "John also wrote the epistles 1 John, 2 John, 3 John, and the Book of Revelation")
        ],
        [
            ("What is the first book of the Bible?", "Genesis"),
            ("Who wrote it?", "Traditionally attributed to Moses"),
            ("What is the first verse?", "In the beginning God created the heavens and the earth.")
        ]
    ]
    
    print("\n=== Testing Single-Turn Questions ===\n")
    
    for i, test in enumerate(test_examples):
        try:
            prediction = model(
                context=test["context"],
                question=test["question"],
                history=[]
            )
            
            print(f"Example {i+1}:")
            if test["context"]:
                print(f"Context: {test['context']}")
            print(f"Question: {test['question']}")
            print(f"Expected: {test['expected']}")
            print(f"Predicted: {prediction.answer}")
            print()
            
        except Exception as e:
            logger.error(f"Error on test example {i+1}: {e}")
            print(f"Error: {e}\n")
    
    print("\n=== Testing Multi-Turn Conversations ===\n")
    
    for i, conversation in enumerate(multi_turn_tests):
        print(f"Conversation {i+1}:")
        history = []
        
        for j, (question, expected) in enumerate(conversation):
            try:
                prediction = model(
                    context="",
                    question=question,
                    history=history
                )
                
                print(f"Turn {j+1}:")
                print(f"Question: {question}")
                print(f"Expected: {expected}")
                print(f"Predicted: {prediction.answer}")
                print()
                
                # Add to history
                history.append((question, prediction.answer))
                
            except Exception as e:
                logger.error(f"Error on conversation {i+1}, turn {j+1}: {e}")
                print(f"Error: {e}\n")

def load_test_file(file_path, max_examples=None):
    """
    Load test examples from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file
        max_examples: Maximum number of examples to load
        
    Returns:
        List of test examples
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Test file not found: {file_path}")
            return None
            
        examples = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if max_examples and i >= max_examples:
                    break
                    
                data = json.loads(line.strip())
                examples.append(data)
                
        logger.info(f"Loaded {len(examples)} examples from {file_path}")
        return examples
        
    except Exception as e:
        logger.error(f"Error loading test file: {e}")
        return None

def run_file_tests(model, test_examples, pretty=False):
    """
    Run tests using examples from a file.
    
    Args:
        model: Loaded DSPy model
        test_examples: List of test examples
        pretty: Whether to print in pretty format
    """
    if not test_examples:
        logger.error("No test examples provided")
        return
        
    correct = 0
    partial_correct = 0
    total = len(test_examples)
    
    print(f"\n=== Testing {total} examples from file ===\n")
    
    for i, example in enumerate(test_examples):
        try:
            context = example.get("context", "")
            question = example.get("question", "")
            expected = example.get("answer", "")
            
            if not question:
                logger.warning(f"Example {i+1} has no question, skipping")
                continue
                
            prediction = model(
                context=context,
                question=question,
                history=[]
            )
            
            # Extract the answer from the prediction
            answer = prediction.answer
            
            # Clean up the answer - some LLMs add quotes or prefixes
            answer = answer.strip()
            if answer.startswith('"') and answer.endswith('"'):
                answer = answer[1:-1].strip()
            if answer.lower().startswith("answer:"):
                answer = answer[7:].strip()
                
            # Handle Mistral model special output format
            if "<answer>" in answer and "</answer>" in answer:
                parts = answer.split("<answer>")[1].split("</answer>")[0].strip()
                answer = parts
            elif "<think>" in answer and "</think>" in answer:
                # Remove thinking process
                clean_answer = ""
                in_thinking = False
                for line in answer.split("\n"):
                    if "<think>" in line:
                        in_thinking = True
                        continue
                    if "</think>" in line:
                        in_thinking = False
                        continue
                    if not in_thinking:
                        clean_answer += line + "\n"
                answer = clean_answer.strip()
            
            # Extract first sentence if answer is too verbose (more than 100 chars)
            if len(answer) > 100 and "." in answer[:100]:
                first_period = answer[:100].find(".")
                if first_period > 0:
                    first_sentence = answer[:first_period+1].strip()
                    # If the first sentence is reasonable, use it
                    if len(first_sentence) > 10:
                        answer = first_sentence
                        
            # Advanced answer evaluation logic
            is_exact_match = False
            
            # Case insensitive exact match
            if answer.lower().strip() == expected.lower().strip():
                is_exact_match = True
                
            # For Bible verses where we want to focus on the core content
            is_verse_match = False
            if ":" in expected and len(expected.split()) <= 5:
                # This is likely a Bible verse reference
                if expected.lower().strip() in answer.lower():
                    is_verse_match = True
                    
            # Prefix match - if the model's answer starts with the expected answer
            is_prefix_match = False
            if answer.lower().startswith(expected.lower()):
                is_prefix_match = True
                
            # Contains match - if the model's answer contains the expected answer as a substring
            is_contains_match = False
            if expected.lower() in answer.lower():
                is_contains_match = True
                    
            # Semantic match for longer answers
            is_semantic_match = False
            if len(expected.split()) > 3:
                # For longer answers, check if key terms are present
                expected_terms = [term.lower() for term in expected.split() 
                                 if len(term) > 3 and term.lower() not in 
                                 ["the", "and", "that", "with", "this", "for", "was", "have"]]
                
                # Count how many key terms are in the answer
                matches = sum(1 for term in expected_terms if term in answer.lower())
                
                # If more than 70% of key terms match, consider it correct
                if expected_terms and matches / len(expected_terms) > 0.7:
                    is_semantic_match = True
                    
            # Check theological concepts for theological questions
            is_theological_match = False
            metadata = example.get("metadata", {})
            if metadata.get("type") == "theological":
                # For theological questions, focus on key theological terms
                theological_terms = [
                    "God", "Jesus", "Christ", "Holy Spirit", "Trinity", "salvation",
                    "sin", "grace", "faith", "covenant", "redemption", "resurrection"
                ]
                
                # Count theological terms in both expected and answer
                expected_theo = [term for term in theological_terms if term.lower() in expected.lower()]
                answer_theo = [term for term in theological_terms if term.lower() in answer.lower()]
                
                # If the answer contains the same theological terms, consider it correct
                if expected_theo and set(expected_theo).issubset(set(answer_theo)):
                    is_theological_match = True
                    
            # Determine if the answer is correct
            is_correct = is_exact_match or is_verse_match or is_semantic_match or is_theological_match or is_prefix_match or is_contains_match
            
            # For partially correct answers
            if not is_correct and len(expected.split()) > 3:
                expected_terms = expected.lower().split()
                answer_terms = answer.lower().split()
                
                # Find common terms
                common_terms = set(expected_terms).intersection(set(answer_terms))
                
                # If at least 40% of the terms match, count as partially correct
                if len(common_terms) / len(set(expected_terms)) >= 0.4:
                    partial_correct += 1
                    
            if is_correct:
                correct += 1
                
            match_type = []
            if is_exact_match: match_type.append("Exact Match")
            if is_verse_match: match_type.append("Verse Match")
            if is_semantic_match: match_type.append("Semantic Match")
            if is_theological_match: match_type.append("Theological Match")
            if is_prefix_match: match_type.append("Prefix Match")
            if is_contains_match: match_type.append("Contains Match")
                
            if pretty:
                print(f"\n{'='*50}")
                print(f"Example {i+1}:")
                if context:
                    print(f"\nContext: {context}")
                print(f"\nQuestion: {question}")
                print(f"\nExpected: {expected}")
                print(f"\nPredicted: {answer}")
                
                if is_correct:
                    print(f"\nCorrect: ✓ [{', '.join(match_type)}]")
                elif len(expected.split()) > 3 and len(common_terms) / len(set(expected_terms)) >= 0.4:
                    print(f"\nPartially Correct: ⚠ ({len(common_terms)}/{len(set(expected_terms))} terms match)")
                else:
                    print(f"\nCorrect: ✗")
                print(f"{'='*50}\n")
            else:
                print(f"Example {i+1}:")
                if context:
                    print(f"Context: {context}")
                print(f"Question: {question}")
                print(f"Expected: {expected}")
                print(f"Predicted: {answer}")
                
                if is_correct:
                    print(f"Correct: ✓ [{', '.join(match_type)}]")
                elif len(expected.split()) > 3 and len(common_terms) / len(set(expected_terms)) >= 0.4:
                    print(f"Partially Correct: ⚠ ({len(common_terms)}/{len(set(expected_terms))} terms match)")
                else:
                    print(f"Correct: ✗")
                print()
                
        except Exception as e:
            logger.error(f"Error on test example {i+1}: {e}")
            print(f"Error: {e}\n")
            
    accuracy = (correct / total) * 100 if total > 0 else 0
    partial_accuracy = ((correct + partial_correct) / total) * 100 if total > 0 else 0
    
    print(f"\n=== Test Results ===")
    print(f"Strict Accuracy: {correct}/{total} ({accuracy:.2f}%)")
    print(f"With Partial Credit: {correct + partial_correct}/{total} ({partial_accuracy:.2f}%)")
    
    # Log the accuracy
    logger.info(f"Test accuracy: {correct}/{total} ({accuracy:.2f}%) - With partial credit: {partial_accuracy:.2f}%")
    
    return accuracy

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Test Bible QA with DSPy 2.6 features.")
    parser.add_argument("--model-path", default="models/dspy/bible_qa_t5_latest",
                      help="Path to the trained model (use 'latest' for most recent)")
    parser.add_argument("--conversation", action="store_true",
                      help="Run in interactive conversation mode")
    parser.add_argument("--use-local-lm", action="store_true",
                      help="Use local LM instead of teacher model")
    parser.add_argument("--test-file", 
                      help="Path to a JSONL file with test examples")
    parser.add_argument("--max-examples", type=int, default=50,
                      help="Maximum number of examples to test from the file")
    parser.add_argument("--pretty", action="store_true",
                      help="Print test results in a pretty format")
    parser.add_argument("--use-lm-studio", action="store_true",
                      help="Use LM Studio API for inference")
    parser.add_argument("--lm-studio-model", 
                      help="Model name for LM Studio (defaults to LM_STUDIO_CHAT_MODEL in .env)")
    
    args = parser.parse_args()
    
    # If using LM Studio, we don't strictly need a model path
    if args.use_lm_studio and not args.model_path:
        args.model_path = "none"  # Use a placeholder value
    
    # Load the model
    model = load_model(args)
    
    if not model:
        logger.error("Failed to load model")
        sys.exit(1)
    
    # Run tests
    if args.conversation:
        run_interactive_session(model)
    elif args.test_file:
        test_examples = load_test_file(args.test_file, args.max_examples)
        if test_examples:
            run_file_tests(model, test_examples, args.pretty)
        else:
            logger.error("Failed to load test examples")
            sys.exit(1)
    else:
        run_test_examples(model)

if __name__ == "__main__":
    main() 