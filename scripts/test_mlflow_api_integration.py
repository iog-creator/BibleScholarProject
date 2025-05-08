#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for MLflow integration with Bible QA API.

This script demonstrates how to:
1. List available MLflow runs
2. Register a model from MLflow in the API
3. Promote a model to production
4. Test questions with different model versions

Usage:
    python scripts/test_mlflow_api_integration.py
"""

import os
import sys
import json
import requests
import argparse
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

# API URL
API_BASE_URL = "http://localhost:5006"

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

def list_mlflow_runs(experiment_name="bible_qa_t5", max_runs=5):
    """List the most recent MLflow runs."""
    client = MlflowClient()
    
    # Find the experiment
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if not experiment:
        logger.error(f"Experiment {experiment_name} not found")
        return []
    
    # Get runs
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["start_time DESC"],
        max_results=max_runs
    )
    
    # Print run information
    print(f"\nLatest {len(runs)} runs from experiment '{experiment_name}':")
    print("-" * 100)
    
    run_info = []
    for run in runs:
        run_id = run.info.run_id
        status = run.info.status
        start_time = run.info.start_time
        
        # Get parameters and metrics
        from datetime import datetime
        start_time_str = datetime.fromtimestamp(start_time/1000).strftime('%Y-%m-%d %H:%M:%S')
        base_model = run.data.params.get('base_model', 'N/A')
        optimizer = run.data.params.get('optimizer', 'N/A')
        accuracy = run.data.metrics.get('accuracy', 0)
        
        print(f"Run ID: {run_id}")
        print(f"  Status: {status}")
        print(f"  Started: {start_time_str}")
        print(f"  Model: {base_model}")
        print(f"  Optimizer: {optimizer}")
        print(f"  Accuracy: {accuracy:.4f}")
        print("-" * 100)
        
        run_info.append({
            "run_id": run_id,
            "status": status,
            "start_time": start_time_str,
            "base_model": base_model,
            "optimizer": optimizer,
            "accuracy": accuracy
        })
    
    return run_info

def register_model(run_id, description=None):
    """Register a model from MLflow in the API."""
    # Build URL for registration
    url = f"{API_BASE_URL}/api/models/register"
    
    # Build parameters
    params = {
        "run_id": run_id
    }
    
    if description:
        params["description"] = description
    
    # Register model
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Model registered: {result}")
        
        return result.get("version_id")
    except Exception as e:
        logger.error(f"Error registering model: {e}")
        return None

def promote_model(version_id):
    """Promote a model version to production."""
    # Build URL for promotion
    url = f"{API_BASE_URL}/api/models/{version_id}/promote"
    
    # Promote model
    try:
        response = requests.post(url)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Model promoted: {result}")
        
        return True
    except Exception as e:
        logger.error(f"Error promoting model: {e}")
        return False

def list_api_models():
    """List models registered in the API."""
    # Build URL
    url = f"{API_BASE_URL}/api/models"
    
    # Get models
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        result = response.json()
        
        print("\nAPI Registered Models:")
        print("-" * 100)
        
        for model in result.get("available_models", []):
            print(f"Version ID: {model['version_id']}")
            print(f"  Model Type: {model['model_type']}")
            print(f"  Created: {model['creation_time']}")
            print(f"  Description: {model['description']}")
            print(f"  Production: {'Yes' if model['is_production'] else 'No'}")
            print("-" * 100)
        
        print(f"Current Production: {result.get('current_production')}")
        print(f"Latest Version: {result.get('latest')}")
        
        return result
    except Exception as e:
        logger.error(f"Error listing API models: {e}")
        return None

def test_question(question, context=""):
    """Test a question with the API."""
    # Build URL
    url = f"{API_BASE_URL}/api/question"
    
    # Build request
    data = {
        "question": question,
        "context": context
    }
    
    # Send question
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"\nQuestion: {question}")
        if context:
            print(f"Context: {context}")
        print(f"Answer: {result['answer']}")
        
        return result
    except Exception as e:
        logger.error(f"Error testing question: {e}")
        return None

def run_full_integration_test():
    """Run a full integration test."""
    # 1. List MLflow runs
    print("\n=== Step 1: List recent MLflow runs ===")
    runs = list_mlflow_runs()
    
    if not runs:
        logger.error("No MLflow runs found, exiting test")
        return
    
    # 2. List current API models
    print("\n=== Step 2: List current API models ===")
    list_api_models()
    
    # 3. Register best model
    print("\n=== Step 3: Register best model from MLflow ===")
    # Sort runs by accuracy and get the best one
    best_run = sorted(runs, key=lambda x: x["accuracy"], reverse=True)[0]
    best_run_id = best_run["run_id"]
    
    print(f"Registering model from run {best_run_id} with accuracy {best_run['accuracy']}")
    version_id = register_model(
        best_run_id, 
        f"Best model with accuracy {best_run['accuracy']:.4f}, optimizer: {best_run['optimizer']}"
    )
    
    if not version_id:
        logger.error("Failed to register model, exiting test")
        return
    
    # 4. List API models again
    print("\n=== Step 4: List API models after registration ===")
    list_api_models()
    
    # 5. Promote model to production
    print(f"\n=== Step 5: Promote model {version_id} to production ===")
    promote_model(version_id)
    
    # 6. List API models after promotion
    print("\n=== Step 6: List API models after promotion ===")
    list_api_models()
    
    # 7. Test questions with the new model
    print("\n=== Step 7: Test questions with the new model ===")
    test_questions = [
        {"question": "Who was the first king of Israel?", "context": ""},
        {"question": "What did Jesus say about loving your enemies?", "context": ""},
        {"question": "Who created the heavens and the earth?", "context": "In the beginning God created the heavens and the earth."}
    ]
    
    for q in test_questions:
        test_question(q["question"], q["context"])

def main():
    """Main function to parse arguments and execute commands."""
    # Load environment variables
    load_environment()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="MLflow API Integration Test")
    parser.add_argument("--run-id", type=str, help="MLflow run ID to register")
    parser.add_argument("--list-runs", action="store_true", help="List MLflow runs")
    parser.add_argument("--list-models", action="store_true", help="List API models")
    parser.add_argument("--register", action="store_true", help="Register a model from MLflow")
    parser.add_argument("--promote", type=str, help="Promote a model version to production")
    parser.add_argument("--test-question", type=str, help="Test a question with the API")
    parser.add_argument("--full-test", action="store_true", help="Run full integration test")
    
    args = parser.parse_args()
    
    # Execute command
    if args.list_runs:
        list_mlflow_runs()
    elif args.list_models:
        list_api_models()
    elif args.register and args.run_id:
        register_model(args.run_id)
    elif args.promote:
        promote_model(args.promote)
    elif args.test_question:
        test_question(args.test_question)
    elif args.full_test:
        run_full_integration_test()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 