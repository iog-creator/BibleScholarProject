#!/usr/bin/env python3
"""
Test MLflow Connection

This script tests the connection to MLflow and shows information
about tracked experiments.

Usage:
    python test_mlflow_connection.py [--uri URI]
"""

import os
import sys
import argparse
import logging
import time
import mlflow
from mlflow.tracking import MlflowClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test MLflow connection")
    parser.add_argument(
        "--uri", 
        type=str, 
        default="http://localhost:5000",
        help="MLflow tracking server URI"
    )
    parser.add_argument(
        "--list-experiments",
        action="store_true",
        help="List all experiments and their details"
    )
    parser.add_argument(
        "--list-runs",
        type=str,
        help="List all runs for the specified experiment name"
    )
    return parser.parse_args()

def test_connection(tracking_uri):
    """Test connection to MLflow tracking server."""
    try:
        logger.info(f"Attempting to connect to MLflow at {tracking_uri}")
        start_time = time.time()
        
        mlflow.set_tracking_uri(tracking_uri)
        client = MlflowClient()
        
        # Try to list experiments to confirm connection
        experiments = client.search_experiments()
        
        end_time = time.time()
        logger.info(f"Successfully connected to MLflow server in {end_time - start_time:.2f}s")
        logger.info(f"Found {len(experiments)} experiments")
        
        return True, experiments
    except Exception as e:
        logger.error(f"Failed to connect to MLflow: {e}")
        return False, None

def list_experiments(experiments):
    """List all experiments and their metadata."""
    print("\n===== MLflow Experiments =====")
    print(f"{'ID':<10} {'Name':<30} {'Artifact Location':<50}")
    print("-" * 90)
    
    for experiment in experiments:
        print(f"{experiment.experiment_id:<10} {experiment.name:<30} {experiment.artifact_location:<50}")

def list_runs(experiment_name):
    """List all runs for a given experiment."""
    try:
        # Get experiment by name
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if not experiment:
            logger.error(f"Experiment '{experiment_name}' not found")
            return
        
        # Get runs for experiment
        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
        
        if len(runs) == 0:
            logger.info(f"No runs found for experiment '{experiment_name}'")
            return
        
        print(f"\n===== Runs for Experiment: {experiment_name} =====")
        print(f"Found {len(runs)} runs")
        
        for i, (index, run) in enumerate(runs.iterrows()):
            print(f"\nRun {i+1}: {run.run_id}")
            print(f"Status: {run.status}")
            print(f"Start time: {run.start_time}")
            print(f"End time: {run.end_time if hasattr(run, 'end_time') else 'N/A'}")
            
            # Print parameters
            params = {k.replace('params.', ''): v for k, v in run.items() if k.startswith('params.')}
            if params:
                print("\nParameters:")
                for param, value in params.items():
                    print(f"  {param}: {value}")
            
            # Print metrics
            metrics = {k.replace('metrics.', ''): v for k, v in run.items() if k.startswith('metrics.')}
            if metrics:
                print("\nMetrics:")
                for metric, value in metrics.items():
                    print(f"  {metric}: {value}")
            
            print("-" * 50)
    
    except Exception as e:
        logger.error(f"Error listing runs: {e}")

def main():
    """Main function."""
    args = parse_args()
    
    # Test connection
    success, experiments = test_connection(args.uri)
    
    if not success:
        logger.info("Tips for fixing MLflow connection issues:")
        logger.info("1. Start MLflow server with 'mlflow ui --port 5000'")
        logger.info("2. Make sure the port is not blocked by firewall")
        logger.info("3. Check network connectivity if using a remote server")
        return 1
    
    # List experiments if requested
    if args.list_experiments and experiments:
        list_experiments(experiments)
    
    # List runs if experiment name provided
    if args.list_runs:
        list_runs(args.list_runs)
    
    logger.info("MLflow connection test completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 