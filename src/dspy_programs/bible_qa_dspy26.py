#!/usr/bin/env python3
"""
Bible QA DSPy 2.6 Training Script

This script implements the DSPy 2.6 features for Bible Question Answering:
- Multi-turn conversation history
- Enhanced optimizers (GRPO)
- MLflow integration
- Assertion-based backtracking for theological accuracy

Usage:
    python -m src.dspy_programs.bible_qa_dspy26 --teacher-category highest --student-model "google/flan-t5-small" --optimizer grpo
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
import dspy
import mlflow
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dspy_train.log"),
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
        configure_teacher_model,
        configure_local_student_model,
        TEACHER_MODELS
    )
except ImportError as e:
    logger.error(f"Error importing huggingface_integration: {e}")
    sys.exit(1)

def load_data(data_path):
    """
    Load QA pairs with conversation history from JSONL files.
    
    Args:
        data_path (str): Path to the data directory
    
    Returns:
        tuple: Train and validation data sets
    """
    try:
        train_path = os.path.join(data_path, "qa_dataset_train.jsonl")
        val_path = os.path.join(data_path, "qa_dataset_val.jsonl")
        
        # Check if files exist
        if not os.path.exists(train_path):
            # Fall back to standard dataset
            standard_path = os.path.join(data_path, "..", "qa_dataset.jsonl")
            if os.path.exists(standard_path):
                logger.info(f"Train dataset not found at {train_path}, using {standard_path}")
                with open(standard_path, 'r', encoding='utf-8') as f:
                    all_data = [json.loads(line) for line in f if line.strip() and not line.startswith('//')]
                
                # Create train/val split
                split_idx = int(len(all_data) * 0.8)
                train_data = all_data[:split_idx]
                val_data = all_data[split_idx:]
                
                # Create directory if needed
                os.makedirs(os.path.dirname(train_path), exist_ok=True)
                
                # Write split files
                with open(train_path, 'w', encoding='utf-8') as f:
                    for item in train_data:
                        f.write(json.dumps(item) + '\n')
                
                with open(val_path, 'w', encoding='utf-8') as f:
                    for item in val_data:
                        f.write(json.dumps(item) + '\n')
                
                # Add empty history field if not present
                for item in train_data:
                    if 'history' not in item:
                        item['history'] = []
                
                for item in val_data:
                    if 'history' not in item:
                        item['history'] = []
                
                return dspy.Example.from_multiple(train_data), dspy.Example.from_multiple(val_data)
            else:
                logger.error(f"No datasets found at {train_path} or {standard_path}")
                return [], []
        else:
            # Load from split files
            with open(train_path, 'r', encoding='utf-8') as f:
                train_data = [json.loads(line) for line in f if line.strip() and not line.startswith('//')]
            
            with open(val_path, 'r', encoding='utf-8') as f:
                val_data = [json.loads(line) for line in f if line.strip() and not line.startswith('//')]
                
            # Add empty history field if not present
            for item in train_data:
                if 'history' not in item:
                    item['history'] = []
            
            for item in val_data:
                if 'history' not in item:
                    item['history'] = []
            
            return dspy.Example.from_multiple(train_data), dspy.Example.from_multiple(val_data)
            
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return [], []

# Define our Bible QA signature with history support
class BibleQASignature(dspy.Signature):
    """Signature for Bible Question Answering that supports conversation history."""
    context = dspy.InputField(desc="Biblical context or verse")
    question = dspy.InputField(desc="Question about the biblical context")
    history = dspy.InputField(desc="Previous conversation turns as a list of questions and answers", default=[])
    answer = dspy.OutputField(desc="Answer to the question based on the biblical context")

# Define a QA module that uses assertions for theological accuracy
class BibleQAModule(dspy.Module):
    """Module for Bible QA with multi-turn support and theological assertions."""
    
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
        prediction = self.qa_model(
            context=context,
            question=question,
            history=formatted_history
        )
        
        # Add theological assertions
        if "god" in question.lower() and "god" not in prediction.answer.lower():
            # Check if an assertion about God should be made
            dspy.Assert(
                "god" in prediction.answer.lower(),
                "Answer must reference God when questions are about God."
            )
            
        if "jesus" in question.lower() and "jesus" not in prediction.answer.lower() and "christ" not in prediction.answer.lower():
            # Check if an assertion about Jesus should be made
            dspy.Assert(
                any(term in prediction.answer.lower() for term in ["jesus", "christ", "messiah"]),
                "Answer must reference Jesus/Christ when questions are about Jesus."
            )
            
        return prediction

def configure_optimizer(optimizer_name):
    """
    Configure the DSPy optimizer based on name.
    
    Args:
        optimizer_name (str): Optimizer name ('dsp', 'grpo', etc.)
        
    Returns:
        dspy.Optimizer: Configured optimizer instance
    """
    if optimizer_name == "grpo":
        return dspy.optimizers.GRPO()
    elif optimizer_name == "simba":
        return dspy.optimizers.SIMBA()
    else:
        # Default to BootstrapFewShot
        return dspy.optimizers.BootstrapFewShot()

def train_model(args):
    """Train the model with the specified optimizer."""
    # Enable MLflow tracking
    mlflow.dspy.autolog()
    
    # Generate a unique run name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"bible_qa_{args.student_model.split('/')[-1]}_{timestamp}"
    
    # Start MLflow run
    with mlflow.start_run(run_name=run_name):
        # Log parameters
        mlflow.log_param("teacher_category", args.teacher_category)
        mlflow.log_param("student_model", args.student_model)
        mlflow.log_param("optimizer", args.optimizer)
        
        # Load training and validation data
        train_data, val_data = load_data(args.data_path)
        
        if not train_data:
            logger.error("No training data available. Exiting.")
            return None
            
        logger.info(f"Loaded {len(train_data)} training examples and {len(val_data)} validation examples")
        
        # Configure the teacher model
        teacher = configure_teacher_model(model_category=args.teacher_category)
        
        # Configure the student model
        student = configure_local_student_model(model_name=args.student_model)
        
        # Create and configure optimizer
        optimizer = configure_optimizer(args.optimizer)
        
        # Initialize the module
        qa_module = BibleQAModule()
        
        # Define evaluation metric
        def theological_accuracy(example, pred, trace=None):
            """
            Measure theological accuracy of predictions.
            
            Higher score for:
            1. Mentions of key theological concepts when relevant
            2. Biblical accuracy
            3. Handling conversation history correctly
            """
            score = 0.0
            
            # Check if the answer is somewhat relevant
            if any(word in pred.answer.lower() for word in example.answer.lower().split()):
                score += 0.5
                
            # Check for exact match
            if pred.answer.lower() == example.answer.lower():
                score += 1.0
                
            # If question contains "god" or "jesus", check for theological reference
            if "god" in example.question.lower() and "god" in pred.answer.lower():
                score += 0.2
                
            if "jesus" in example.question.lower() and any(term in pred.answer.lower() for term in ["jesus", "christ"]):
                score += 0.2
                
            # Check for history awareness
            if example.history and any(
                h_q.lower() in pred.answer.lower() or h_a.lower() in pred.answer.lower() 
                for h_q, h_a in example.history
            ):
                score += 0.1
                
            return score
        
        # Train the model
        logger.info(f"Starting training with {args.optimizer} optimizer")
        try:
            trained_model = optimizer.compile(
                qa_module,
                train_data=train_data,
                val_data=val_data,
                metric=theological_accuracy,
                max_bootstrapped_demos=4,
                max_labeled_demos=4,
                teacher_settings={"temperature": 0.3},
                student_settings={"temperature": 0.1}
            )
            
            # Save the trained model
            save_path = f"models/dspy/bible_qa_{args.student_model.split('/')[-1]}_{timestamp}.dspy"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            trained_model.save(save_path)
            
            # Log the model with MLflow
            mlflow.dspy.log_model(
                trained_model,
                artifact_path="model"
            )
            
            logger.info(f"Training completed and model saved to {save_path}")
            
            # Test on a simple example
            test_result = trained_model(
                context="In the beginning God created the heavens and the earth.",
                question="Who created the heavens and the earth?",
                history=[("What is the first verse in the Bible?", "Genesis 1:1")]
            )
            
            logger.info(f"Test result: {test_result.answer}")
            
            return trained_model
            
        except Exception as e:
            logger.error(f"Error during training: {e}")
            return None

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Train a Bible QA model with DSPy 2.6 features.")
    parser.add_argument("--teacher-category", default="highest", choices=list(TEACHER_MODELS.keys()),
                      help="Teacher model category.")
    parser.add_argument("--student-model", default="google/flan-t5-small", 
                      help="Student model name.")
    parser.add_argument("--data-path", default="data/processed/dspy_training_data/bible_corpus/dspy",
                      help="Path to training data.")
    parser.add_argument("--optimizer", default="dsp", choices=["dsp", "grpo", "simba"],
                      help="Optimizer type.")
    
    args = parser.parse_args()
    
    # Train the model
    trained_model = train_model(args)
    
    if trained_model:
        logger.info("Training completed successfully")
    else:
        logger.error("Training failed")
        sys.exit(1)
    
if __name__ == "__main__":
    main() 