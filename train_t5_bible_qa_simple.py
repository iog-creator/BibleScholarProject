#!/usr/bin/env python
"""
Simplified T5 Bible QA Training Script

This script trains a T5 model on Bible question-answering data without
relying on DSPy, using the transformers library directly.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import torch
from tqdm import tqdm
from sklearn.model_selection import train_test_split

# Load environment variables
if os.path.exists('.env.dspy'):
    load_dotenv('.env.dspy')
    print("Loaded environment variables from .env.dspy")
else:
    load_dotenv()
    print("Loaded environment variables from .env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/t5_train_simple.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
Path('logs').mkdir(exist_ok=True)

try:
    from transformers import (
        AutoModelForSeq2SeqLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
        DataCollatorForSeq2Seq
    )
    import mlflow
    import datasets
    import numpy as np
except ImportError as e:
    logger.error(f"Required package not found: {e}")
    logger.error("Please install required packages: pip install transformers datasets mlflow torch")
    sys.exit(1)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Train a T5 Bible QA model directly with Transformers")
    
    # Basic configuration
    parser.add_argument("--model", type=str, default="google/flan-t5-small", 
                       help="Base language model to use (default: google/flan-t5-small)")
    
    # Data configuration
    parser.add_argument("--dataset-path", type=str, 
                       default="data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json",
                       help="Path to existing dataset file")
    
    # Training configuration
    parser.add_argument("--batch-size", type=int, default=8, 
                       help="Batch size for training")
    parser.add_argument("--epochs", type=int, default=3,
                       help="Number of training epochs")
    parser.add_argument("--learning-rate", type=float, default=5e-5,
                       help="Learning rate for training")
    parser.add_argument("--max-length", type=int, default=512, 
                       help="Maximum sequence length")
    
    # Output configuration
    parser.add_argument("--output-dir", type=str, default="models/transformers/bible_qa_t5", 
                       help="Directory to save model")
    parser.add_argument("--track-with-mlflow", action="store_true",
                       help="Track experiment with MLflow")
    
    return parser.parse_args()

def load_dataset(dataset_path):
    """Load dataset from JSON file."""
    logger.info(f"Loading dataset from {dataset_path}")
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} examples")
        
        # Split into train/dev/test
        train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)
        test_data, dev_data = train_test_split(test_data, test_size=0.5, random_state=42)
        
        logger.info(f"Train: {len(train_data)}, Dev: {len(dev_data)}, Test: {len(test_data)}")
        
        return train_data, dev_data, test_data
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise

def prepare_dataset_for_transformers(data, tokenizer, max_length):
    """Convert data to format usable by transformers."""
    features = []
    
    for item in data:
        context = item.get("context", "")
        question = item["question"]
        answer = item["answer"]
        
        # Combine context and question for input
        if context:
            input_text = f"context: {context} question: {question}"
        else:
            input_text = f"question: {question}"
            
        # Tokenize input and target
        model_inputs = tokenizer(
            input_text, 
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        # Tokenize the answers
        with tokenizer.as_target_tokenizer():
            labels = tokenizer(
                answer,
                max_length=max_length,
                padding="max_length",
                truncation=True,
                return_tensors="pt"
            )
            
        # Convert to dict and add to features
        model_inputs = {k: v.squeeze(0) for k, v in model_inputs.items()}
        model_inputs["labels"] = labels["input_ids"].squeeze(0)
        features.append(model_inputs)
    
    # Convert to dataset
    return datasets.Dataset.from_dict({
        "input_ids": [feature["input_ids"] for feature in features],
        "attention_mask": [feature["attention_mask"] for feature in features],
        "labels": [feature["labels"] for feature in features]
    })

def setup_mlflow(args):
    """Set up MLflow tracking."""
    if args.track_with_mlflow:
        tracking_uri = os.environ.get('MLFLOW_TRACKING_URI', './mlruns')
        mlflow.set_tracking_uri(tracking_uri)
        
        experiment_name = os.environ.get('MLFLOW_EXPERIMENT_NAME', 'bible_qa_t5')
        mlflow.set_experiment(experiment_name)
        
        run_name = f"t5_{args.model.split('/')[-1]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return run_name
    
    return None

def compute_metrics(eval_pred):
    """Compute metrics for evaluation."""
    predictions, labels = eval_pred
    
    # Replace -100 (padding token) with tokenizer.pad_token_id
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    
    # Decode the predictions and labels
    decoded_preds = tokenizer.batch_decode(predictions, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    
    # Simple exact match accuracy
    exact_matches = sum(1 for pred, label in zip(decoded_preds, decoded_labels) if pred.strip() == label.strip())
    accuracy = exact_matches / len(decoded_preds)
    
    # Also compute partial match (containment)
    partial_matches = sum(1 for pred, label in zip(decoded_preds, decoded_labels) 
                         if pred.strip() in label.strip() or label.strip() in pred.strip())
    partial_accuracy = partial_matches / len(decoded_preds)
    
    return {
        "exact_match_accuracy": accuracy,
        "partial_match_accuracy": partial_accuracy
    }

def train_model(args, train_data, dev_data, test_data):
    """Train the T5 model using transformers directly."""
    global tokenizer  # Make tokenizer available to compute_metrics
    
    # Get HF API token
    hf_api_key = os.environ.get("HUGGINGFACE_API_KEY", "")
    
    # Initialize tokenizer and model
    logger.info(f"Loading model and tokenizer: {args.model}")
    tokenizer = AutoTokenizer.from_pretrained(args.model, token=hf_api_key)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model, token=hf_api_key)
    
    # Prepare datasets
    logger.info("Preparing datasets")
    train_dataset = prepare_dataset_for_transformers(train_data, tokenizer, args.max_length)
    eval_dataset = prepare_dataset_for_transformers(dev_data, tokenizer, args.max_length)
    test_dataset = prepare_dataset_for_transformers(test_data, tokenizer, args.max_length)
    
    # Set up data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding="max_length",
        max_length=args.max_length
    )
    
    # Set up training arguments
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output_dir, f"bible_qa_t5_{timestamp}")
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=0.01,
        logging_dir=f"{output_dir}/logs",
        logging_steps=10,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="exact_match_accuracy",
        push_to_hub=False,
        report_to="mlflow" if args.track_with_mlflow else "none",
        run_name=setup_mlflow(args) if args.track_with_mlflow else None
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics
    )
    
    # Train the model
    logger.info("Starting training")
    trainer.train()
    
    # Save the model
    logger.info(f"Saving model to {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    # Evaluate on test set
    logger.info("Evaluating on test set")
    test_results = trainer.evaluate(test_dataset)
    
    # Log model info
    model_info = {
        "model": args.model,
        "created_at": timestamp,
        "dataset": args.dataset_path,
        "train_examples": len(train_data),
        "dev_examples": len(dev_data),
        "test_examples": len(test_data),
        "epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "test_results": test_results
    }
    
    with open(f"{output_dir}/model_info.json", "w") as f:
        json.dump(model_info, f, indent=2)
    
    logger.info(f"Test results: {test_results}")
    return model, tokenizer, test_results

def main():
    """Main function for training the T5 model."""
    args = parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Load dataset
        train_data, dev_data, test_data = load_dataset(args.dataset_path)
        
        # Train model
        model, tokenizer, test_results = train_model(args, train_data, dev_data, test_data)
        
        logger.info("Training complete!")
        return 0
    
    except Exception as e:
        logger.error(f"Error during training: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main()) 