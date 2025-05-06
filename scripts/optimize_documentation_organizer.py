#!/usr/bin/env python
"""
Documentation Organizer Optimizer

This script optimizes a DSPy model for documentation organization
using the latest optimization techniques.

Usage:
    python scripts/optimize_documentation_organizer.py [--optimizer OPTIMIZER] [--model MODEL_PATH] [--test-problem PROBLEM]
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Make sure the project's src directory is in the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the documentation organizer module
from src.utils.documentation_organizer import (
    load_training_examples,
    train_documentation_organizer,
    generate_solution,
    DocumentationOrganizer
)

import dspy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/documentation_optimizer.log', 'w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Optimize a DSPy documentation organizer")
    
    parser.add_argument(
        "--optimizer", 
        type=str, 
        default="bootstrap",
        choices=["bootstrap", "dsp", "simba"],
        help="DSPy optimizer to use (bootstrap, dsp, or simba)"
    )
    
    parser.add_argument(
        "--model", 
        type=str,
        default="models/dspy/documentation_organizer.dspy",
        help="Path to save the optimized model"
    )
    
    parser.add_argument(
        "--test-problem",
        type=str,
        default="API documentation is inconsistent across different endpoints",
        help="Test problem to solve after optimization"
    )
    
    parser.add_argument(
        "--log-trace",
        action="store_true",
        help="Log the complete trace of model execution"
    )
    
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Custom dataset file path (if not using the default)"
    )
    
    parser.add_argument(
        "--track-metrics",
        action="store_true",
        help="Track metrics using the model metrics tracking system"
    )
    
    return parser.parse_args()

def configure_language_model():
    """Configure a language model for DSPy."""
    try:
        # Try to use OpenAI first (better quality)
        from dspy.openai import OpenAI
        lm = OpenAI(model="gpt-3.5-turbo", max_tokens=1000)
        dspy.settings.configure(lm=lm)
        return "OpenAI GPT-3.5 Turbo"
    except:
        try:
            # Fall back to Anthropic
            from dspy.anthropic import Anthropic
            lm = Anthropic(model="claude-instant-1", max_tokens=1000)
            dspy.settings.configure(lm=lm)
            return "Anthropic Claude Instant"
        except:
            logger.error("Failed to configure a language model - check your API keys")
            sys.exit(1)

def evaluate_model(model, valset):
    """Evaluate model performance on validation set."""
    if not valset:
        return {"accuracy": 0.0, "pattern_quality": 0.0}
    
    correct = 0
    pattern_quality_sum = 0.0
    
    for example in valset:
        # Generate solution
        prediction = model(problem=example.problem)
        
        # Check for solution presence
        has_solution = bool(prediction.solution and prediction.solution.strip())
        
        # Calculate pattern quality
        pred_patterns = set(p.lower() for p in prediction.patterns if p)
        gold_patterns = set(p.lower() for p in example.patterns if p)
        
        # Calculate pattern overlap
        if pred_patterns and gold_patterns:
            intersection = len(pred_patterns.intersection(gold_patterns))
            union = len(pred_patterns.union(gold_patterns))
            pattern_quality = intersection / union
        else:
            pattern_quality = 0.0
            
        pattern_quality_sum += pattern_quality
        
        # Count as correct if has solution and pattern quality > 0.5
        if has_solution and pattern_quality > 0.5:
            correct += 1
    
    # Calculate metrics
    accuracy = correct / len(valset) if valset else 0
    avg_pattern_quality = pattern_quality_sum / len(valset) if valset else 0
    
    return {
        "accuracy": accuracy,
        "pattern_quality": avg_pattern_quality
    }

def track_model_metrics(model_name, metrics_data):
    """Track model metrics using the metrics tracking system."""
    try:
        # Try to import the tracking script
        from scripts.track_dspy_model_metrics import save_metrics
        
        # Call the save_metrics function
        version = save_metrics(model_name, metrics_data)
        logger.info(f"Tracked metrics for {model_name} version {version}")
        return version
    except ImportError:
        # Fall back to direct file writing if import fails
        metrics_dir = Path('data/processed/dspy_training_data/metrics')
        os.makedirs(metrics_dir, exist_ok=True)
        
        metrics_path = metrics_dir / f"{model_name}_metrics.jsonl"
        
        # Add timestamp if not present
        if 'timestamp' not in metrics_data:
            metrics_data['timestamp'] = datetime.now().isoformat()
        
        # Write metrics to file
        with open(metrics_path, 'a', encoding='utf-8') as f:
            if metrics_path.stat().st_size == 0:
                f.write(f"// DSPy model metrics for {model_name}\n")
                f.write(f"// First recorded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(json.dumps(metrics_data, ensure_ascii=False) + '\n')
        
        logger.info(f"Tracked metrics for {model_name} in {metrics_path}")
        return metrics_data.get('version', 1)

def main():
    """Main function to optimize and test the documentation organizer."""
    # Parse arguments
    args = parse_args()
    
    # Create logs and models directories if they don't exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs(os.path.dirname(args.model), exist_ok=True)
    
    # Configure language model
    lm_name = configure_language_model()
    logger.info(f"Using language model: {lm_name}")
    
    # Load training examples
    examples = load_training_examples(args.dataset)
    if not examples:
        logger.error("No training examples found")
        sys.exit(1)
    
    logger.info(f"Loaded {len(examples)} documentation organization examples")
    
    # Split into training and validation sets (80/20)
    split_point = int(0.8 * len(examples))
    trainset, valset = examples[:split_point], examples[split_point:]
    
    logger.info(f"Training set: {len(trainset)} examples")
    logger.info(f"Validation set: {len(valset)} examples")
    
    # Start optimization
    start_time = datetime.now()
    logger.info(f"Starting optimization with {args.optimizer} optimizer at {start_time}")
    
    # Train the model
    optimized_model = train_documentation_organizer(
        trainset=trainset,
        valset=valset,
        optimizer_name=args.optimizer,
        save_path=args.model
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Optimization completed in {duration:.2f} seconds")
    
    # Test the model with the provided problem
    logger.info(f"Testing with problem: {args.test_problem}")
    solution = generate_solution(optimized_model, args.test_problem)
    
    # Evaluate model performance
    eval_metrics = evaluate_model(optimized_model, valset)
    logger.info(f"Model evaluation metrics: {eval_metrics}")
    
    # Track metrics if requested
    if args.track_metrics:
        model_name = os.path.basename(args.model).split('.')[0]
        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "model_name": model_name,
            "metrics": {
                "val_accuracy": eval_metrics["accuracy"],
                "pattern_quality": eval_metrics["pattern_quality"],
                "training_duration_seconds": duration
            },
            "parameters": {
                "optimizer": args.optimizer,
                "lm_model": lm_name,
                "trainset_size": len(trainset),
                "valset_size": len(valset)
            },
            "description": f"Optimized with {args.optimizer}"
        }
        
        track_model_metrics(model_name, metrics_data)
    
    # Print the result
    print("\n" + "="*60)
    print("DOCUMENTATION PROBLEM SOLUTION")
    print("="*60)
    print(f"Problem: {solution['problem']}")
    print(f"\nSolution: {solution['solution']}")
    print("\nImplementation Steps:")
    for i, step in enumerate(solution['steps'], 1):
        print(f"{i}. {step}")
    print("\nDocumentation Patterns:")
    for pattern in solution['patterns']:
        print(f"- {pattern}")
    print("="*60)
    
    # Log model trace if requested
    if args.log_trace and hasattr(dspy.settings.lm, 'inspect_history'):
        try:
            trace = dspy.settings.lm.inspect_history(n=1)
            logger.info(f"Model execution trace:\n{trace}")
        except Exception as e:
            logger.warning(f"Could not log model trace: {e}")
    
    logger.info(f"Optimized model saved to {args.model}")
    print(f"\nOptimized model saved to {args.model}")
    
    if args.track_metrics:
        print(f"Model metrics tracked in data/processed/dspy_training_data/metrics/")

if __name__ == "__main__":
    main() 