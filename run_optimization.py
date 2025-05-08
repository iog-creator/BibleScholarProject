#!/usr/bin/env python3
"""
Run Bible QA Optimization Script

This script runs the complete Bible QA optimization workflow in Python,
avoiding batch file issues.

Usage:
    python run_optimization.py --method better_together --iterations 10 --target 0.95
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/run_optimization.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run Bible QA optimization")
    parser.add_argument(
        "--method",
        type=str,
        default="better_together",
        choices=["better_together", "infer_rules", "ensemble"],
        help="Optimization method to use"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Maximum number of optimization iterations"
    )
    parser.add_argument(
        "--target",
        type=float,
        default=0.95,
        help="Target accuracy to achieve (0.0-1.0)"
    )
    return parser.parse_args()

def verify_lm_studio():
    """Verify that LM Studio is running."""
    logger.info("Verifying LM Studio API...")
    try:
        import requests
        response = requests.get("http://127.0.0.1:1234/v1/models", timeout=5)
        if response.status_code == 200:
            logger.info("LM Studio API is running")
            return True
        else:
            logger.error(f"LM Studio API returned status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error connecting to LM Studio API: {e}")
        return False

def run_verify_dspy_model():
    """Run the DSPy model verification."""
    logger.info("Verifying DSPy model...")
    try:
        # Import directly to avoid subprocess issues
        sys.path.append(os.path.join(os.getcwd(), "scripts"))
        import verify_dspy_model
        result = verify_dspy_model.main()
        if result == 0:
            logger.info("DSPy model verification successful")
            return True
        else:
            logger.error("DSPy model verification failed")
            return False
    except Exception as e:
        logger.error(f"Error running DSPy model verification: {e}")
        return False

def expand_validation_dataset():
    """Expand the validation dataset."""
    logger.info("Expanding validation dataset...")
    try:
        result = subprocess.run(
            ["python", "expand_validation_dataset.py", "--sample-theological"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Validation dataset expanded successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error expanding validation dataset: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error expanding validation dataset: {e}")
        return False

def start_mlflow_server():
    """Start the MLflow tracking server."""
    logger.info("Starting MLflow tracking server...")
    try:
        # Start MLflow server in a separate process
        if os.name == 'nt':  # Windows
            process = subprocess.Popen(
                ["start", "MLflow Server", "mlflow", "ui", "--host", "127.0.0.1", "--port", "5000"],
                shell=True
            )
        else:  # Unix/Linux/Mac
            process = subprocess.Popen(
                ["mlflow", "ui", "--host", "127.0.0.1", "--port", "5000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
        
        # Wait a moment for MLflow to start
        logger.info("Waiting for MLflow server to start...")
        time.sleep(5)
        return True
    except Exception as e:
        logger.error(f"Error starting MLflow server: {e}")
        return False

def run_optimization(method, iterations, target):
    """Run the optimization script."""
    logger.info(f"Running optimization with method: {method}, iterations: {iterations}, target: {target}")
    try:
        result = subprocess.run(
            [
                "python", "train_and_optimize_bible_qa.py",
                "--optimization-method", method,
                "--max-iterations", str(iterations),
                "--target-accuracy", str(target)
            ],
            check=False,  # Don't raise exception on non-zero exit
            capture_output=True,
            text=True
        )
        
        logger.info(f"Optimization completed with exit code: {result.returncode}")
        if result.returncode != 0:
            logger.warning(f"Optimization returned non-zero exit code: {result.returncode}")
            logger.warning(f"STDOUT: {result.stdout}")
            logger.warning(f"STDERR: {result.stderr}")
        
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running optimization: {e}")
        return False

def analyze_results():
    """Analyze the optimization results."""
    logger.info("Analyzing optimization results...")
    try:
        # Create output directory if it doesn't exist
        os.makedirs("analysis_results", exist_ok=True)
        
        result = subprocess.run(
            [
                "python", "-m", "scripts.analyze_mlflow_results",
                "--experiment-name", "bible_qa_optimization",
                "--output-dir", "analysis_results"
            ],
            check=False,
            capture_output=True,
            text=True
        )
        
        logger.info(f"Analysis completed with exit code: {result.returncode}")
        if result.returncode != 0:
            logger.warning(f"Analysis returned non-zero exit code: {result.returncode}")
            logger.warning(f"STDOUT: {result.stdout}")
            logger.warning(f"STDERR: {result.stderr}")
        
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error analyzing results: {e}")
        return False

def main():
    """Main function to run the optimization workflow."""
    args = parse_args()
    
    logger.info("===== Complete Bible QA Optimization Workflow =====")
    logger.info(f"Method: {args.method}, Iterations: {args.iterations}, Target: {args.target}")
    
    # Create output directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("analysis_results", exist_ok=True)
    os.makedirs("models/dspy/bible_qa_optimized", exist_ok=True)
    
    # Step 1: Verify LM Studio
    if not verify_lm_studio():
        logger.error("LM Studio verification failed")
        return 1
    
    # Step 2: Verify DSPy model
    if not run_verify_dspy_model():
        logger.error("DSPy model verification failed")
        return 1
    
    # Step 3: Expand validation dataset
    if not expand_validation_dataset():
        logger.error("Validation dataset expansion failed")
        return 1
    
    # Step 4: Start MLflow server
    start_mlflow_server()  # Continue even if this fails
    
    # Step 5: Run optimization
    success = run_optimization(args.method, args.iterations, args.target)
    
    # Step 6: Analyze results
    analyze_results()  # Continue even if this fails
    
    logger.info("===== Optimization Workflow Completed =====")
    logger.info("Results saved to analysis_results directory")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 