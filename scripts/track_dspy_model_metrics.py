#!/usr/bin/env python3
"""
DSPy Model Metrics Tracker

This script tracks metrics for DSPy models over time, including:
1. Training/validation performance
2. Model versions and parameters
3. Dataset versions used for training
4. Evaluation metrics on test sets

Usage:
  python scripts/track_dspy_model_metrics.py record --model-name doc_organizer --metrics metrics.json
  python scripts/track_dspy_model_metrics.py report --model-name doc_organizer
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/dspy_model_metrics.log', 'w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Constants
METRICS_DIR = Path('data/processed/dspy_training_data/metrics')
MODELS_DIR = Path('models/dspy')

def ensure_directories():
    """Ensure necessary directories exist."""
    os.makedirs(METRICS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

def get_metrics_path(model_name):
    """Get path to the metrics file for a model."""
    return METRICS_DIR / f"{model_name}_metrics.jsonl"

def get_model_path(model_name, version=None):
    """Get path to a model file."""
    if version:
        return MODELS_DIR / f"{model_name}_v{version}.dspy"
    return MODELS_DIR / f"{model_name}.dspy"

def load_metrics(model_name):
    """Load metrics history for a model."""
    metrics_path = get_metrics_path(model_name)
    metrics = []
    
    if not metrics_path.exists():
        return metrics
    
    with open(metrics_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() and not line.startswith('//'):
                metrics.append(json.loads(line))
    
    return metrics

def save_metrics(model_name, metrics_data):
    """Save metrics for a model run."""
    metrics_path = get_metrics_path(model_name)
    
    # Make sure metrics has timestamp and version info
    if 'timestamp' not in metrics_data:
        metrics_data['timestamp'] = datetime.now().isoformat()
    
    if 'version' not in metrics_data:
        # Get latest version number and increment
        existing_metrics = load_metrics(model_name)
        if existing_metrics:
            latest_version = max(m.get('version', 0) for m in existing_metrics)
            metrics_data['version'] = latest_version + 1
        else:
            metrics_data['version'] = 1
    
    # Add dataset versions
    data_dir = Path('data/processed/dspy_training_data')
    dataset_hashes = {}
    for file in data_dir.glob("*.jsonl"):
        if file.name != f"{model_name}_metrics.jsonl":
            # Calculate file hash
            with open(file, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            dataset_hashes[file.name] = file_hash
    
    metrics_data['dataset_versions'] = dataset_hashes
    
    # Append to metrics file
    with open(metrics_path, 'a', encoding='utf-8') as f:
        if metrics_path.stat().st_size == 0:
            f.write(f"// DSPy model metrics for {model_name}\n")
            f.write(f"// First recorded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(json.dumps(metrics_data, ensure_ascii=False) + '\n')
    
    logger.info(f"Recorded metrics for {model_name} v{metrics_data['version']}")
    
    # Save model version
    model_src = get_model_path(model_name)
    if model_src.exists():
        model_dest = get_model_path(model_name, metrics_data['version'])
        if not model_dest.exists():
            import shutil
            shutil.copy2(model_src, model_dest)
            logger.info(f"Saved model version: {model_dest}")
    
    return metrics_data['version']

def load_metrics_from_file(file_path):
    """Load metrics from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading metrics file {file_path}: {e}")
        return {}

def generate_report(model_name):
    """Generate a report of model metrics over time."""
    metrics = load_metrics(model_name)
    
    if not metrics:
        logger.warning(f"No metrics found for model {model_name}")
        return
    
    print(f"\nMetrics Report for {model_name}")
    print("="*50)
    print(f"Total versions: {len(metrics)}")
    print(f"Latest version: {max(m.get('version', 0) for m in metrics)}")
    print(f"First recorded: {metrics[0]['timestamp']}")
    print(f"Last recorded: {metrics[-1]['timestamp']}")
    
    # Show performance trend
    print("\nPerformance Trend:")
    print("-"*50)
    print(f"{'Version':<10} {'Date':<20} {'Train Acc':<10} {'Val Acc':<10} {'Test Acc':<10}")
    print("-"*50)
    
    for m in sorted(metrics, key=lambda x: x.get('version', 0)):
        version = m.get('version', 'N/A')
        date = datetime.fromisoformat(m['timestamp']).strftime('%Y-%m-%d %H:%M')
        train_acc = m.get('metrics', {}).get('train_accuracy', 'N/A')
        val_acc = m.get('metrics', {}).get('val_accuracy', 'N/A')
        test_acc = m.get('metrics', {}).get('test_accuracy', 'N/A')
        
        if isinstance(train_acc, float):
            train_acc = f"{train_acc:.4f}"
        if isinstance(val_acc, float):
            val_acc = f"{val_acc:.4f}"
        if isinstance(test_acc, float):
            test_acc = f"{test_acc:.4f}"
            
        print(f"{version:<10} {date:<20} {train_acc:<10} {val_acc:<10} {test_acc:<10}")
    
    # Show latest metrics in detail
    latest_metrics = max(metrics, key=lambda x: x.get('version', 0))
    print("\nLatest Metrics Detail:")
    print("-"*50)
    
    for key, value in latest_metrics.get('metrics', {}).items():
        if isinstance(value, dict):
            print(f"{key}:")
            for subkey, subvalue in value.items():
                print(f"  {subkey}: {subvalue}")
        else:
            print(f"{key}: {value}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Track and report on DSPy model metrics")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Record command
    record_parser = subparsers.add_parser("record", help="Record metrics for a model")
    record_parser.add_argument("--model-name", required=True, help="Name of the model")
    record_parser.add_argument("--metrics", required=True, help="Path to metrics JSON file")
    record_parser.add_argument("--description", help="Optional description for this version")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate a report of model metrics")
    report_parser.add_argument("--model-name", required=True, help="Name of the model")
    
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    ensure_directories()
    
    if args.command == "record":
        metrics_data = load_metrics_from_file(args.metrics)
        if args.description:
            metrics_data['description'] = args.description
        version = save_metrics(args.model_name, metrics_data)
        print(f"Recorded metrics for {args.model_name} v{version}")
        
    elif args.command == "report":
        generate_report(args.model_name)
        
    else:
        parse_args()

if __name__ == "__main__":
    main() 