#!/usr/bin/env python
"""
Train a T5 model for Bible Question Answering using DSPy.

Usage:
    python train_t5_bible_qa.py --lm "google/flan-t5-base" --track-with-mlflow
"""

import os
import sys
import json
import pickle
import logging
import argparse
from pathlib import Path
from datetime import datetime
import random
from typing import List, Dict, Any, Tuple
import numpy as np

# Import DSPy components
import dspy
import mlflow
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/t5_train.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define T5 model variants with better defaults
T5_MODELS = {
    "small": "google/flan-t5-small",     # 80M parameters
    "base": "google/flan-t5-base",       # 250M parameters 
    "large": "google/flan-t5-large",     # 800M parameters
    "xl": "google/flan-t5-xl",           # 3B parameters
}

# Load environment variables
if os.path.exists('.env.dspy'):
    load_dotenv('.env.dspy')
    logger.info("Loaded environment variables from .env.dspy")
else:
    load_dotenv()
    logger.info("Loaded environment variables from .env")

# Define the BibleQA signature with improved prompting
class BibleQA(dspy.Signature):
    """Answer questions about Bible passages with theological accuracy."""
    context = dspy.InputField(desc="Optional context from Bible passages")
    question = dspy.InputField(desc="A question about Bible content, history, or theology")
    answer = dspy.OutputField(desc="A comprehensive, accurate answer based on the Bible")

# Define a simple QA module (as top-level class for pickle compatibility)
class BibleQAModule(dspy.Module):
    """Module for Bible QA using a student model."""
    
    def __init__(self):
        super().__init__()
        self.qa_predictor = dspy.Predict(BibleQA)
    
    def forward(self, context, question):
        """Answer a question based on context."""
        # Format the input with explicit instruction to improve performance
        formatted_question = f"Answer this Bible question: {question}"
        if context and len(context.strip()) > 0:
            formatted_context = f"Based on this context: {context}"
            return self.qa_predictor(context=formatted_context, question=formatted_question)
        else:
            return self.qa_predictor(context="", question=formatted_question)

def load_dataset(path: str) -> List[Dict[str, Any]]:
    """Load dataset from a JSON file."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} examples from {path}")
        return data
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise

def augment_dataset(data: List[Dict[str, Any]], augmentation_factor: int = 2) -> List[Dict[str, Any]]:
    """Augment the dataset with variations of the same examples."""
    if augmentation_factor <= 1:
        return data
    
    logger.info(f"Augmenting dataset by factor of {augmentation_factor}")
    augmented_data = []
    
    for example in data:
        # Add the original example
        augmented_data.append(example)
        
        # Create augmented versions by modifying prompts
        for i in range(augmentation_factor - 1):
            question = example["question"]
            answer = example["answer"]
            context = example.get("context", "")
            
            # Apply different prompt variations
            if i % 4 == 0:
                # Format 1: Direct question
                new_question = question
            elif i % 4 == 1:
                # Format 2: More detailed question format
                new_question = f"Please answer in detail: {question}"
            elif i % 4 == 2:
                # Format 3: Scripture reference format
                new_question = f"According to the Bible, {question}"
            else:
                # Format 4: Theological inquiry
                new_question = f"From a biblical perspective, {question}"
            
            # Create new example
            new_example = {
                "question": new_question,
                "answer": answer,
                "context": context,
                "metadata": example.get("metadata", {})
            }
            
            augmented_data.append(new_example)
    
    logger.info(f"Dataset augmented to {len(augmented_data)} examples")
    return augmented_data

def split_dataset(data: List[Dict[str, Any]], train_pct: float = 0.7, dev_pct: float = 0.15, 
                 stratify_by_book: bool = True) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split dataset into train, dev, and test sets with improved stratification."""
    # Set random seed for reproducibility
    random.seed(42)
    
    if stratify_by_book and all("metadata" in ex and "book" in ex.get("metadata", {}) for ex in data):
        # Group examples by book
        book_examples = {}
        for ex in data:
            book = ex["metadata"]["book"]
            if book not in book_examples:
                book_examples[book] = []
            book_examples[book].append(ex)
        
        # Create stratified splits
        train_data, dev_data, test_data = [], [], []
        
        for book, examples in book_examples.items():
            random.shuffle(examples)
            n_examples = len(examples)
            
            # Calculate split indices
            train_idx = int(n_examples * train_pct)
            dev_idx = train_idx + int(n_examples * dev_pct)
            
            # Split data
            train_data.extend(examples[:train_idx])
            dev_data.extend(examples[train_idx:dev_idx])
            test_data.extend(examples[dev_idx:])
            
        logger.info(f"Created stratified splits by book: {len(train_data)} train, {len(dev_data)} dev, {len(test_data)} test")
    else:
        # Shuffle the data
        random.shuffle(data)
        
        # Calculate split points
        train_size = int(len(data) * train_pct)
        dev_size = int(len(data) * dev_pct)
        
        # Split the data
        train_data = data[:train_size]
        dev_data = data[train_size:train_size + dev_size]
        test_data = data[train_size + dev_size:]
        
        logger.info(f"Split dataset into {len(train_data)} train, {len(dev_data)} dev, {len(test_data)} test examples")
    
    return train_data, dev_data, test_data

def configure_lm(args):
    """Configure the DSPy language model based on environment and arguments."""
    # Check for Hugging Face API key
    hf_api_key = os.environ.get("HUGGINGFACE_API_KEY", "")
    
    # Check for LM Studio configuration
    lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
    lm_studio_model = os.environ.get("LM_STUDIO_CHAT_MODEL", "")
    
    # Determine which backend to use
    if args.use_huggingface and hf_api_key:
        logger.info(f"Using Hugging Face API with model: {args.lm}")
        lm = dspy.LM(
            provider="hf",
            model=args.lm,
            api_key=hf_api_key,
            max_tokens=args.max_tokens,
            temperature=args.temperature
        )
    elif lm_studio_api and lm_studio_model:
        logger.info(f"Using LM Studio API at {lm_studio_api} with model {lm_studio_model}")
        
        # Set environment variables for openai compatibility
        os.environ["OPENAI_API_KEY"] = "dummy-key"
        os.environ["OPENAI_API_BASE"] = lm_studio_api
        
        # Try the simplest approach: use the OpenAI provider directly
        # Use OpenAI provider which is most compatible with LM Studio
        lm = dspy.LM(
            provider="openai",
            model=lm_studio_model,
            api_base=lm_studio_api,
            api_key="dummy-key",
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            model_engine=lm_studio_model  # Explicitly set model engine 
        )
    else:
        logger.warning("No API configuration found. Using default DSPy model loading.")
        logger.info(f"Loading model: {args.lm}")
        
        # Try to use local model as fallback
        try:
            lm = dspy.LM(
                provider="local",
                model=args.lm,
                max_tokens=args.max_tokens,
                temperature=args.temperature
            )
        except:
            # Last resort, try with HF
            logger.warning("Falling back to HuggingFace provider with no API key")
            lm = dspy.LM(
                provider="hf",
                model=args.lm,
                max_tokens=args.max_tokens,
                temperature=args.temperature
            )
    
    # Configure DSPy with our LM
    dspy.settings.configure(lm=lm)
    return lm

def train_model(args, train_data, dev_data):
    """Train a DSPy model for Bible QA with improved techniques."""
    # Configure the language model
    lm = configure_lm(args)
    
    # Create the base model
    model = BibleQAModule()
    
    # Prepare data for DSPy format with explicitly set input keys
    train_examples = [
        dspy.Example(
            context=ex.get("context", ""), 
            question=ex["question"], 
            answer=ex["answer"]
        ).with_inputs("context", "question") 
        for ex in train_data
    ]
    
    dev_examples = [
        dspy.Example(
            context=ex.get("context", ""), 
            question=ex["question"], 
            answer=ex["answer"]
        ).with_inputs("context", "question")
        for ex in dev_data
    ]
    
    # Define improved accuracy metric
    def enhanced_accuracy(example, pred, trace=None):
        """Enhanced accuracy metric with better semantic matching."""
        gold_answer = example.answer.lower()
        pred_answer = pred.answer.lower()
        
        # Exact match (best case)
        if gold_answer == pred_answer:
            return 1.0
        
        # Check for containment with normalization
        gold_normalized = ' '.join(gold_answer.split())
        pred_normalized = ' '.join(pred_answer.split())
        
        if gold_normalized in pred_normalized or pred_normalized in gold_normalized:
            return 0.8
        
        # Calculate word overlap score
        gold_words = set(gold_normalized.split())
        pred_words = set(pred_normalized.split())
        
        if len(gold_words) > 0:
            overlap = len(gold_words.intersection(pred_words)) / len(gold_words)
            
            # Apply thresholds
            if overlap > 0.8:
                return 0.9  # High overlap
            elif overlap > 0.6:
                return 0.7  # Good overlap
            elif overlap > 0.4:
                return 0.5  # Medium overlap
            elif overlap > 0.2:
                return 0.3  # Low overlap
        
        return 0.0  # No significant overlap
    
    # Create optimizer based on arguments
    if args.optimizer == "bootstrap":
        logger.info("Using BootstrapFewShot optimizer with validation")
        from dspy.teleprompt import BootstrapFewShot
        
        # Create BootstrapFewShot optimizer with validation set
        # Note: Check parameter names for compatibility with the current version
        optimizer = BootstrapFewShot(
            metric=enhanced_accuracy,
            max_bootstrapped_demos=args.max_demos,
            # Remove unsupported parameters for current version of DSPy
            # num_candidate_programs=8, 
            # device="cuda" if args.use_gpu else "cpu"
        )
        
        # Optimize using the entire training set or a large subset
        training_subset = train_examples if len(train_examples) <= 100 else train_examples[:100]
        
        # Optimize the model - removed valset which is not supported in this DSPy version
        optimized_model = optimizer.compile(
            student=model,
            trainset=training_subset
        )
        
    elif args.optimizer == "rm":
        logger.info("Using RewardModel optimizer with improved configuration")
        from dspy.teleprompt import BootstrapFewShot, RewardModelRM
        
        # First bootstrap some examples
        bootstrap = BootstrapFewShot(
            metric=enhanced_accuracy,
            max_bootstrapped_demos=3,
            # Remove unsupported parameters
            # device="cuda" if args.use_gpu else "cpu"
        )
        
        # Use more examples for bootstrapping
        bootstrap_subset = train_examples if len(train_examples) <= 50 else train_examples[:50]
        
        bootstrapped_model = bootstrap.compile(
            student=model,
            trainset=bootstrap_subset
        )
        
        # Then use RM to optimize
        rm_optimizer = RewardModelRM(
            metric=enhanced_accuracy,
            # Remove unsupported parameters 
            # num_candidate_programs=10,
            # device="cuda" if args.use_gpu else "cpu"
        )
        
        # Use more examples for RM optimization
        rm_subset = train_examples[50:] if len(train_examples) > 50 else train_examples
        if len(rm_subset) > 100:
            rm_subset = rm_subset[:100]
            
        optimized_model = rm_optimizer.compile(
            student=bootstrapped_model,
            trainset=rm_subset
        )
        
    else:
        logger.info("Using LabeledFewShot with increased number of examples")
        # Use LabeledFewShot with more examples
        from dspy.teleprompt import LabeledFewShot
        teleprompter = LabeledFewShot(k=args.max_demos)
        
        # Use the teleprompter to compile the model with examples
        subset_size = min(10, len(train_examples))
        optimized_model = teleprompter.compile(
            student=model,
            trainset=train_examples[:subset_size]
        )
    
    return optimized_model, train_examples, dev_examples

def evaluate_model(model, test_data):
    """Evaluate a trained model on test data with detailed metrics."""
    # Prepare test data
    test_examples = [
        dspy.Example(
            context=ex.get("context", ""), 
            question=ex["question"]
        ).with_inputs("context", "question")
        for ex in test_data
    ]
    gold_answers = [ex["answer"] for ex in test_data]
    
    # Make predictions
    logger.info(f"Evaluating model on {len(test_examples)} test examples")
    predictions = []
    correct = 0
    partial_correct = 0
    
    # Track examples by type for error analysis
    correct_examples = []
    incorrect_examples = []
    
    for i, example in enumerate(test_examples):
        try:
            # Get the gold answer before any potential errors
            gold = gold_answers[i].lower()
            
            # Predict
            pred = model(context=example.context, question=example.question)
            predictions.append(pred.answer)
            
            # Check accuracy with different thresholds
            predicted = pred.answer.lower()
            
            # Normalize whitespace
            gold_norm = ' '.join(gold.split())
            pred_norm = ' '.join(predicted.split())
            
            # Exact match
            if gold_norm == pred_norm:
                correct += 1
                correct_examples.append((example, pred.answer, gold))
            # Containment match
            elif gold_norm in pred_norm or pred_norm in gold_norm:
                correct += 1
                correct_examples.append((example, pred.answer, gold))
            else:
                # Word overlap
                gold_words = set(gold_norm.split())
                pred_words = set(pred_norm.split())
                
                if len(gold_words) > 0:
                    overlap = len(gold_words.intersection(pred_words)) / len(gold_words)
                    if overlap > 0.6:  # Sufficient overlap
                        partial_correct += 1
                    else:
                        incorrect_examples.append((example, pred.answer, gold))
                else:
                    incorrect_examples.append((example, pred.answer, gold))
                
        except Exception as e:
            logger.error(f"Error evaluating example {i}: {e}")
            predictions.append("ERROR")
            # Make sure we have the gold answer for the error case
            if i < len(gold_answers):
                gold = gold_answers[i].lower()
                incorrect_examples.append((example, "ERROR", gold))
            else:
                incorrect_examples.append((example, "ERROR", "UNKNOWN"))
    
    # Calculate metrics
    total_examples_evaluated = len(test_examples) - predictions.count("ERROR")
    accuracy = correct / len(test_examples) if test_examples else 0
    partial_accuracy = (correct + partial_correct) / len(test_examples) if test_examples else 0
    
    logger.info(f"Strict Accuracy: {accuracy:.4f} ({correct}/{len(test_examples)})")
    logger.info(f"Lenient Accuracy: {partial_accuracy:.4f} ({correct + partial_correct}/{len(test_examples)})")
    logger.info(f"Error count: {predictions.count('ERROR')}/{len(test_examples)}")
    
    # Sample error analysis
    if incorrect_examples:
        logger.info("Error Analysis: Sample of 3 incorrect predictions")
        for i, (ex, pred, gold) in enumerate(incorrect_examples[:3]):
            logger.info(f"Example {i+1}:")
            logger.info(f"  Question: {ex.question}")
            logger.info(f"  Gold: {gold}")
            logger.info(f"  Pred: {pred}")
    
    return accuracy, predictions, {
        'strict_accuracy': accuracy,
        'lenient_accuracy': partial_accuracy,
        'num_correct': correct,
        'num_partial': partial_correct,
        'num_examples': len(test_examples),
        'num_errors': predictions.count("ERROR")
    }

def save_model(model, path: str):
    """Save a trained model to disk."""
    model_dir = os.path.dirname(path)
    if not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)
    
    # Use pickling to save the optimized module
    try:
        model_file = f"{path}.pkl"
        config_file = f"{path}.json"
        info_file = f"{path}.info"
        
        # Save the model using pickle
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        
        # Also save a JSON configuration file with metadata
        config = {
            'model_type': 'bible_qa_t5',
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'version': '1.0.0'
        }
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        # Add an info file for MLflow tracking
        with open(info_file, 'w') as f:
            f.write(f"Bible QA Model\n")
            f.write(f"Version: 1.0.0\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y%m%d_%H%M%S')}\n")
            
        logger.info(f"Successfully saved model to {path}")
        return True
    except Exception as e:
        logger.error(f"Error saving model: {e}")
        return False

def create_model_info_file(model_path, args, train_data_size, metrics=None):
    """Create a separate info file for MLflow tracking with detailed metrics."""
    info_file = f"{model_path}.info"
    try:
        with open(info_file, 'w') as f:
            f.write(f"Bible QA Model\n")
            f.write(f"Version: 1.0.0\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y%m%d_%H%M%S')}\n")
            f.write(f"Base Model: {args.lm}\n")
            f.write(f"Optimizer: {args.optimizer}\n")
            f.write(f"Training Examples: {train_data_size}\n")
            
            if metrics:
                f.write(f"\nPerformance Metrics:\n")
                for k, v in metrics.items():
                    f.write(f"{k}: {v}\n")
            
        return info_file
    except Exception as e:
        logger.error(f"Error creating info file: {e}")
        return None

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Train a T5 model for Bible QA using DSPy")
    parser.add_argument("--lm", type=str, default="google/flan-t5-base", help="Base language model")
    parser.add_argument("--teacher", type=str, default="gpt-3.5-turbo", help="Teacher model for optimization")
    parser.add_argument("--use-custom-data", action="store_true", help="Generate data from database")
    parser.add_argument("--dataset-path", type=str, 
                       default="data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json",
                       help="Path to dataset file")
    parser.add_argument("--optimizer", type=str, choices=["bootstrap", "rm", "none"], default="bootstrap",
                       help="DSPy optimizer to use")
    parser.add_argument("--max-tokens", type=int, default=512, help="Maximum tokens for generation")
    parser.add_argument("--temperature", type=float, default=0.1, help="Temperature for generation (0.1 for better accuracy)")
    parser.add_argument("--output-dir", type=str, default="models/dspy/bible_qa_t5", 
                       help="Directory to save model")
    parser.add_argument("--max-demos", type=int, default=5, help="Maximum number of demonstrations")
    parser.add_argument("--augment-factor", type=int, default=2, help="Data augmentation factor (0 for none)")
    parser.add_argument("--use-gpu", action="store_true", help="Use GPU for training if available")
    parser.add_argument("--stratify-split", action="store_true", help="Stratify dataset split by book")
    parser.add_argument("--track-with-mlflow", action="store_true", help="Track with MLflow")
    parser.add_argument("--use-huggingface", action="store_true", help="Use HuggingFace API for inference")
    
    args = parser.parse_args()
    
    # Verify T5 model if specified by key
    if args.lm in T5_MODELS:
        args.lm = T5_MODELS[args.lm]
    
    # Load dataset
    data = load_dataset(args.dataset_path)
    
    # Optionally augment dataset
    if args.augment_factor > 0:
        data = augment_dataset(data, args.augment_factor)
    
    # Split dataset
    train_data, dev_data, test_data = split_dataset(data, stratify_by_book=args.stratify_split)
    
    # Create model directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_dir = os.path.join(args.output_dir, f"bible_qa_t5_{timestamp}")
    model_path = os.path.join(model_dir, "model")
    os.makedirs(model_dir, exist_ok=True)
    
    # Train model
    model, train_examples, dev_examples = train_model(args, train_data, dev_data)
    
    # Evaluate model
    accuracy, predictions, metrics = evaluate_model(model, test_data)
    
    # Save model
    save_model(model, model_path)
    
    # Create a model info file for MLflow
    info_file = create_model_info_file(model_path, args, len(train_data), metrics)
    
    # Create a latest symlink
    latest_dir = os.path.join(args.output_dir, "bible_qa_t5_latest")
    if os.path.exists(latest_dir):
        try:
            os.remove(latest_dir)
        except:
            logger.warning(f"Could not remove existing symlink {latest_dir}")
    
    try:
        # For Windows, need to use directory junction
        if sys.platform == "win32":
            import subprocess
            subprocess.run(f'mklink /J "{latest_dir}" "{model_dir}"', shell=True)
        else:
            os.symlink(model_dir, latest_dir, target_is_directory=True)
    except Exception as e:
        logger.warning(f"Could not create latest symlink: {e}")
    
    # Track with MLflow if requested
    if args.track_with_mlflow and info_file:
        try:
            # Set MLflow tracking URI
            mlflow.set_tracking_uri(os.environ.get('MLFLOW_TRACKING_URI', './mlruns'))
            mlflow.set_experiment(os.environ.get('MLFLOW_EXPERIMENT_NAME', 'bible_qa_t5'))
            
            with mlflow.start_run(run_name=f"t5_{args.lm.split('/')[-1]}_{timestamp}"):
                # Log parameters
                mlflow.log_param("base_model", args.lm)
                mlflow.log_param("optimizer", args.optimizer)
                mlflow.log_param("num_train_examples", len(train_data))
                mlflow.log_param("max_tokens", args.max_tokens)
                mlflow.log_param("temperature", args.temperature)
                mlflow.log_param("max_demos", args.max_demos)
                mlflow.log_param("augment_factor", args.augment_factor)
                
                # Log metrics
                mlflow.log_metric("strict_accuracy", metrics['strict_accuracy'])
                mlflow.log_metric("lenient_accuracy", metrics['lenient_accuracy'])
                
                # Log artifacts (use the info file instead of trying to use the model directly)
                mlflow.log_artifact(info_file)
                
                logger.info(f"Logged run to MLflow: {mlflow.active_run().info.run_id}")
        except Exception as e:
            logger.error(f"Error logging to MLflow: {e}")
    
    logger.info("Training complete!")
    return model, accuracy

if __name__ == "__main__":
    main() 