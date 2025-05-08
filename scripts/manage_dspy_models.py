#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DSPy Model Management Utility

This script provides utilities for managing DSPy models tracked with MLflow,
including listing, comparing, and loading models.

Usage:
    python scripts/manage_dspy_models.py list-runs --experiment bible_qa_t5
    python scripts/manage_dspy_models.py compare-runs --runs run_id1 run_id2
    python scripts/manage_dspy_models.py load-model --run-id run_id1 --output model.pkl
"""

import os
import sys
import json
import pickle
import argparse
import pandas as pd
from dotenv import load_dotenv
import mlflow
from mlflow.tracking import MlflowClient

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env.dspy or .env"""
    if os.path.exists('.env.dspy'):
        load_dotenv('.env.dspy')
        logger.info("Loaded environment from .env.dspy")
    else:
        load_dotenv()
        logger.info("Loaded environment from .env")

    # Set up MLflow
    tracking_uri = os.getenv('MLFLOW_TRACKING_URI', './mlruns')
    mlflow.set_tracking_uri(tracking_uri)
    logger.info(f"MLflow tracking URI: {tracking_uri}")

def list_experiments():
    """List all MLflow experiments."""
    client = MlflowClient()
    experiments = client.search_experiments()
    
    if not experiments:
        logger.info("No experiments found.")
        return
    
    print("\nAvailable Experiments:")
    print("=" * 80)
    print(f"{'ID':<10} {'Name':<30} {'Creation Time':<20} {'# Runs':<10}")
    print("-" * 80)
    
    for exp in experiments:
        # Count runs in this experiment
        runs = client.search_runs(experiment_ids=[exp.experiment_id])
        run_count = len(runs)
        
        print(f"{exp.experiment_id:<10} {exp.name:<30} {exp.creation_time:<20} {run_count:<10}")

def list_runs(experiment_name):
    """List all runs for a given experiment."""
    client = MlflowClient()
    
    # Find experiment by name
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if not experiment:
        logger.error(f"Experiment '{experiment_name}' not found.")
        return
    
    # Get all runs for this experiment
    runs = client.search_runs(experiment_ids=[experiment.experiment_id])
    
    if not runs:
        logger.info(f"No runs found for experiment '{experiment_name}'.")
        return
    
    print(f"\nRuns for Experiment: {experiment_name}")
    print("=" * 100)
    print(f"{'Run ID':<40} {'Status':<10} {'Start Time':<20} {'Base Model':<20} {'Accuracy':<10}")
    print("-" * 100)
    
    for run in runs:
        # Get parameters and metrics
        run_id = run.info.run_id
        status = run.info.status
        start_time = run.info.start_time
        
        # Format timestamp
        from datetime import datetime
        start_time_str = datetime.fromtimestamp(start_time/1000).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get parameters and metrics
        base_model = run.data.params.get('base_model', 'N/A')
        accuracy = run.data.metrics.get('accuracy', 'N/A')
        
        print(f"{run_id:<40} {status:<10} {start_time_str:<20} {base_model:<20} {accuracy:<10.4f}")

def compare_runs(run_ids):
    """Compare multiple runs by metrics and parameters."""
    if len(run_ids) < 2:
        logger.error("Please provide at least two run IDs to compare.")
        return
    
    client = MlflowClient()
    
    # Collect data from each run
    runs_data = []
    
    for run_id in run_ids:
        try:
            run = client.get_run(run_id)
            
            # Basic run info
            run_info = {
                'run_id': run_id,
                'status': run.info.status,
                'start_time': datetime.fromtimestamp(run.info.start_time/1000).strftime('%Y-%m-%d %H:%M:%S'),
                'experiment_id': run.info.experiment_id
            }
            
            # Parameters
            for name, value in run.data.params.items():
                run_info[f"param_{name}"] = value
            
            # Metrics
            for name, value in run.data.metrics.items():
                run_info[f"metric_{name}"] = value
            
            runs_data.append(run_info)
            
        except Exception as e:
            logger.error(f"Error fetching run {run_id}: {e}")
    
    if not runs_data:
        logger.error("No valid runs found.")
        return
    
    # Convert to DataFrame for easier comparison
    df = pd.DataFrame(runs_data)
    
    # Display comparison
    print("\nRun Comparison:")
    print("=" * 100)
    
    # Basic info
    basic_cols = [col for col in df.columns if not col.startswith('param_') and not col.startswith('metric_')]
    print("\nBasic Information:")
    print(df[basic_cols].to_string(index=False))
    
    # Parameters
    param_cols = [col for col in df.columns if col.startswith('param_')]
    if param_cols:
        print("\nParameters:")
        print(df[param_cols].to_string(index=False))
    
    # Metrics
    metric_cols = [col for col in df.columns if col.startswith('metric_')]
    if metric_cols:
        print("\nMetrics:")
        print(df[metric_cols].to_string(index=False))

def load_model(run_id, output_path=None):
    """Load a model from an MLflow run."""
    client = MlflowClient()
    
    try:
        # Get run info
        run = client.get_run(run_id)
        experiment = client.get_experiment(run.info.experiment_id)
        
        logger.info(f"Loading model from run {run_id} (Experiment: {experiment.name})")
        
        # Download model artifact
        artifact_path = "model.pkl"
        local_path = client.download_artifacts(run_id, artifact_path, ".")
        
        logger.info(f"Downloaded model artifact to {local_path}")
        
        # Load the model
        with open(local_path, 'rb') as f:
            model = pickle.load(f)
        
        logger.info(f"Successfully loaded model: {type(model)}")
        
        # Save to output path if specified
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, 'wb') as f:
                pickle.dump(model, f)
            logger.info(f"Saved model to {output_path}")
        
        return model
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None

def promote_to_production(run_id, model_name):
    """Tag a run as production and create a symbolic link to the latest production model."""
    client = MlflowClient()
    
    try:
        # Tag the run as production
        client.set_tag(run_id, "production", "true")
        client.set_tag(run_id, "promotion_time", datetime.now().isoformat())
        
        # Download model artifacts
        model_path = client.download_artifacts(run_id, "model.pkl", ".")
        config_path = client.download_artifacts(run_id, "config.json", ".")
        
        # Create production directory if it doesn't exist
        prod_dir = os.path.join("models", "production", model_name)
        os.makedirs(prod_dir, exist_ok=True)
        
        # Copy artifacts to production directory
        import shutil
        shutil.copy2(model_path, os.path.join(prod_dir, "model.pkl"))
        shutil.copy2(config_path, os.path.join(prod_dir, "config.json"))
        
        # Create a version file
        with open(os.path.join(prod_dir, "version.json"), 'w') as f:
            json.dump({
                "run_id": run_id,
                "promotion_time": datetime.now().isoformat(),
                "model_name": model_name
            }, f, indent=2)
        
        logger.info(f"Model from run {run_id} promoted to production as {model_name}")
        logger.info(f"Production model available at: {prod_dir}")
        
    except Exception as e:
        logger.error(f"Error promoting model to production: {e}")

def main():
    """Main function to parse arguments and execute commands."""
    # Load environment variables
    load_environment()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="DSPy Model Management Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Experiments command
    exp_parser = subparsers.add_parser("list-experiments", help="List all experiments")
    
    # Runs command
    runs_parser = subparsers.add_parser("list-runs", help="List runs for an experiment")
    runs_parser.add_argument("--experiment", type=str, required=True, help="Experiment name")
    
    # Compare runs command
    compare_parser = subparsers.add_parser("compare-runs", help="Compare multiple runs")
    compare_parser.add_argument("--runs", type=str, nargs="+", required=True, help="Run IDs to compare")
    
    # Load model command
    load_parser = subparsers.add_parser("load-model", help="Load a model from an MLflow run")
    load_parser.add_argument("--run-id", type=str, required=True, help="Run ID to load model from")
    load_parser.add_argument("--output", type=str, help="Output path to save model")
    
    # Promote model command
    promote_parser = subparsers.add_parser("promote", help="Promote a model to production")
    promote_parser.add_argument("--run-id", type=str, required=True, help="Run ID to promote")
    promote_parser.add_argument("--model-name", type=str, required=True, help="Production model name")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "list-experiments":
        list_experiments()
    elif args.command == "list-runs":
        list_runs(args.experiment)
    elif args.command == "compare-runs":
        compare_runs(args.runs)
    elif args.command == "load-model":
        load_model(args.run_id, args.output)
    elif args.command == "promote":
        promote_to_production(args.run_id, args.model_name)
    else:
        parser.print_help()

if __name__ == "__main__":
    from datetime import datetime
    main() 