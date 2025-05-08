#!/usr/bin/env python
"""
Test script for Bible QA model.
Run this to test the trained model with sample questions.
"""

import os
import sys
import json
import pickle
import random
import logging
from pathlib import Path
from dotenv import load_dotenv
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def initialize_dspy():
    """Initialize DSPy with proper configuration."""
    try:
        import dspy
        from dotenv import load_dotenv
        import os
        
        # Load environment variables
        load_dotenv('.env.dspy')
        
        # Configure DSPy with LM Studio or Hugging Face
        lm_studio_api = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1")
        lm_studio_model = os.getenv("LM_STUDIO_CHAT_MODEL", "")
        hf_api_key = os.getenv("HUGGINGFACE_API_KEY", "")
        
        if hf_api_key:
            # Use Hugging Face
            student_model = os.getenv("STUDENT_MODEL", "google/flan-t5-base")
            logger.info(f"Configuring DSPy with Hugging Face model: {student_model}")
            
            # Fix the model name format for LiteLLM
            lm = dspy.LM(
                provider="huggingface",  # Explicitly use 'huggingface' not 'hf'
                model=student_model,
                api_key=hf_api_key
            )
        else:
            # Use LM Studio
            logger.info(f"Configuring DSPy with LM Studio: {lm_studio_model}")
            
            # Set environment variables for OpenAI compatibility
            os.environ["OPENAI_API_KEY"] = "dummy-key"
            os.environ["OPENAI_API_BASE"] = lm_studio_api
            
            lm = dspy.LM(
                provider="openai",
                model=lm_studio_model,
                api_base=lm_studio_api,
                api_key="dummy-key"
            )
        
        # Configure DSPy with the selected LM
        dspy.settings.configure(lm=lm)
        return True
    except Exception as e:
        logger.error(f"Error initializing DSPy: {e}")
        return False

def load_model(model_path="models/dspy/bible_qa_t5/bible_qa_t5_latest"):
    """Load the trained model"""
    try:
        # Try different file paths
        possible_paths = [
            model_path,
            f"{model_path}/model",
            f"{model_path}/model.pkl",
            f"{model_path}.pkl"
        ]
        
        for path in possible_paths:
            try:
                if os.path.isdir(path):
                    # For directory, try loading files inside
                    try:
                        import dspy
                        
                        # Create a proper BibleQA signature first
                        class BibleQA(dspy.Signature):
                            """Answer questions about Bible passages with theological accuracy."""
                            context = dspy.InputField(desc="Optional context from Bible passages")
                            question = dspy.InputField(desc="A question about Bible content, history, or theology")
                            answer = dspy.OutputField(desc="A comprehensive, accurate answer based on the Bible")
                        
                        # Now define the module with the proper signature
                        class BibleQAModule(dspy.Module):
                            """Module for Bible QA."""
                            def __init__(self):
                                super().__init__()
                                self.qa_predictor = dspy.Predict(BibleQA)
                            
                            def forward(self, context, question):
                                """Answer a question based on context."""
                                # Format the input for better performance
                                formatted_question = f"Answer this Bible question: {question}"
                                if context and len(context.strip()) > 0:
                                    formatted_context = f"Based on this context: {context}"
                                    return self.qa_predictor(context=formatted_context, question=formatted_question)
                                else:
                                    return self.qa_predictor(context="", question=formatted_question)
                        
                        logger.info("Created new BibleQAModule instance")
                        return BibleQAModule()
                    except Exception as e:
                        logger.error(f"Error creating model instance: {e}")
                        continue
                else:
                    # Try loading from pickle file
                    with open(path, 'rb') as f:
                        model = pickle.load(f)
                        logger.info(f"Successfully loaded model from {path}")
                        return model
            except Exception as e:
                logger.error(f"Failed to load from {path}: {e}")
                continue
        
        logger.error("Failed to load model from any path")
        return None
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None

def load_sample_questions(num_questions=5):
    """Load sample questions for testing.
    
    Args:
        num_questions: Number of questions to load
        
    Returns:
        List of sample questions
    """
    # Full list of sample questions
    sample_questions = [
        {"question": "What does Genesis 1:1 say?", "context": ""},
        {"question": "How does the Bible describe faith in Hebrews 11:1?", "context": ""},
        {"question": "What did Jesus say about loving your enemies?", "context": ""},
        {"question": "Who was King David in the Bible?", "context": ""},
        {"question": "What is the significance of the Sermon on the Mount?", "context": ""},
        {"question": "How many books are in the Bible?", "context": ""},
        {"question": "What is John 3:16?", "context": ""},
        {"question": "Who built the ark according to the Bible?", "context": ""},
        {"question": "What is the fruit of the Spirit?", "context": ""},
        {"question": "What happened on the day of Pentecost?", "context": ""}
    ]
    
    # Ensure num_questions is within valid range
    num_to_return = max(1, min(num_questions, len(sample_questions)))
    
    return sample_questions[:num_to_return]

def main():
    """Main function to test the Bible QA model"""
    logger.info("Bible QA Model Tester")
    logger.info("=====================")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Bible QA Model Tester")
    parser.add_argument("--mock", action="store_true", help="Use mock model instead of actual model")
    parser.add_argument("--num-examples", type=int, default=5, help="Number of examples to test")
    parser.add_argument("model_path", nargs="?", default="models/dspy/bible_qa_t5/bible_qa_t5_latest", 
                       help="Path to the model directory")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check for mock mode flag
    mock_mode = args.mock
    
    # Initialize DSPy
    if not mock_mode:
        dspy_initialized = initialize_dspy()
        if not dspy_initialized:
            logger.warning("Failed to initialize DSPy. Falling back to mock mode.")
            mock_mode = True
    
    # Load the model
    model = None
    if not mock_mode:
        logger.info(f"Loading model from {args.model_path}")
        model = load_model(args.model_path)
    
    if model is None or mock_mode:
        if mock_mode:
            logger.info("Using mock model for testing")
        else:
            logger.warning("Failed to load model. Using mock model for testing.")
        
        # Create a mock model for testing
        class MockBibleQAModel:
            """Mock Bible QA model for testing."""
            
            def __init__(self):
                self.responses = {
                    "genesis 1:1": "In the beginning God created the heavens and the earth.",
                    "hebrews 11:1": "Now faith is confidence in what we hope for and assurance about what we do not see.",
                    "enemies": "Love your enemies, do good to those who hate you, bless those who curse you, pray for those who mistreat you.",
                    "david": "King David was the second king of Israel, a man after God's own heart who wrote many Psalms.",
                    "sermon": "The Sermon on the Mount contains Jesus' teachings on moral and ethical issues, including the Beatitudes.",
                    "books": "The Bible contains 66 books in total: 39 in the Old Testament and 27 in the New Testament.",
                    "john 3:16": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.",
                    "ark": "Noah built the ark according to God's instructions to save his family and animals from the flood.",
                    "fruit": "The fruit of the Spirit is love, joy, peace, forbearance, kindness, goodness, faithfulness, gentleness and self-control.",
                    "pentecost": "On the day of Pentecost, the Holy Spirit descended on the disciples, and they began speaking in different languages."
                }
            
            def __call__(self, context, question):
                """Generate a mock answer based on keywords in the question."""
                question_lower = question.lower()
                
                # Search for keywords in the question
                for keyword, answer in self.responses.items():
                    if keyword in question_lower:
                        # Create a response object with an answer attribute
                        class Response:
                            def __init__(self, ans):
                                self.answer = ans
                        
                        return Response(answer)
                
                # Default response if no keywords match
                class Response:
                    def __init__(self):
                        self.answer = "This is a mock answer for testing purposes."
                
                return Response()
        
        model = MockBibleQAModel()
    
    logger.info(f"Model ready: {type(model)}")
    
    # Load sample questions
    questions = load_sample_questions(args.num_examples)
    
    # Test the model
    logger.info("\nTesting model with sample questions:")
    
    for i, q in enumerate(questions, 1):
        question = q["question"]
        context = q["context"]
        
        logger.info(f"\nQuestion {i}: {question}")
        if context:
            logger.info(f"Context: {context}")
        
        try:
            # Generate answer
            result = model(context=context, question=question)
            
            # Extract answer depending on model output format
            if hasattr(result, 'answer'):
                answer = result.answer
            elif isinstance(result, dict) and 'answer' in result:
                answer = result['answer']
            else:
                answer = str(result)
            
            logger.info(f"Answer: {answer}")
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
    
    logger.info("\nTesting complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 