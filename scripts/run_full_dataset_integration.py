#!/usr/bin/env python3
"""
Full Dataset Integration Pipeline Runner

This script orchestrates the complete pipeline for:
1. Fetching external Bible datasets
2. Integrating them with internal data
3. Training the Bible QA model with the integrated dataset

Usage:
    python scripts/run_full_dataset_integration.py --train
"""

import os
import sys
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/dataset_integration_pipeline.log", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Define paths
BASE_DIR = Path(os.getcwd())
SCRIPTS_DIR = BASE_DIR / "scripts"
FETCH_SCRIPT = SCRIPTS_DIR / "fetch_external_bible_datasets.py"
INTEGRATE_SCRIPT = SCRIPTS_DIR / "integrate_external_datasets.py"
TRAIN_SCRIPT = BASE_DIR / "train_dspy_bible_qa.py"

def run_command(command: List[str], description: str) -> bool:
    """
    Run a command and log its output.
    
    Args:
        command: Command to run
        description: Description for logging
        
    Returns:
        bool: Success or failure
    """
    try:
        logger.info(f"Running {description}: {' '.join(command)}")
        
        # Run the command and capture output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Process output in real-time
        for line in iter(process.stdout.readline, ""):
            logger.info(line.strip())
        
        # Wait for process to complete
        process.wait()
        
        # Check for errors
        if process.returncode != 0:
            stderr_output = process.stderr.read()
            logger.error(f"{description} failed with return code {process.returncode}")
            logger.error(f"Error output: {stderr_output}")
            return False
        
        logger.info(f"{description} completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error running {description}: {e}")
        return False

def fetch_external_datasets(output_dir: Optional[str] = None) -> bool:
    """
    Run the external dataset fetcher script.
    
    Args:
        output_dir: Output directory for datasets
        
    Returns:
        bool: Success or failure
    """
    command = [sys.executable, str(FETCH_SCRIPT)]
    
    if output_dir:
        command.extend(["--output-dir", output_dir])
    
    return run_command(command, "External dataset fetcher")

def integrate_datasets(output_dir: Optional[str] = None, no_split: bool = False) -> bool:
    """
    Run the dataset integration script.
    
    Args:
        output_dir: Output directory for integrated dataset
        no_split: Don't create train/val split
        
    Returns:
        bool: Success or failure
    """
    command = [sys.executable, str(INTEGRATE_SCRIPT)]
    
    if output_dir:
        command.extend(["--output-dir", output_dir])
    
    if no_split:
        command.append("--no-split")
    
    return run_command(command, "Dataset integration")

def train_model(optimizer: str = "bootstrap", model: str = "google/flan-t5-small", 
               lm_studio: bool = False, max_demos: int = 8) -> bool:
    """
    Run the DSPy training script with the integrated dataset.
    
    Args:
        optimizer: DSPy optimizer to use
        model: Model to use for training
        lm_studio: Whether to use LM Studio for inference
        max_demos: Maximum number of demos to use
        
    Returns:
        bool: Success or failure
    """
    command = [
        sys.executable, 
        str(TRAIN_SCRIPT),
        "--optimizer", optimizer,
        "--model", model,
        "--max-demos", str(max_demos),
        "--data-dir", "data/processed/dspy_training_data/bible_corpus/integrated",
        "--use-integrated-data"
    ]
    
    if lm_studio:
        command.append("--lm-studio")
    
    return run_command(command, "DSPy training with integrated data")

def main():
    """Main function to run the full integration pipeline."""
    parser = argparse.ArgumentParser(description="Run the full dataset integration pipeline")
    
    # Pipeline control options
    parser.add_argument("--skip-fetch", action="store_true", 
                      help="Skip fetching external datasets")
    parser.add_argument("--skip-integrate", action="store_true", 
                      help="Skip dataset integration")
    parser.add_argument("--train", action="store_true", 
                      help="Run DSPy training after integration")
    
    # Dataset options
    parser.add_argument("--external-data-dir", type=str,
                      default="data/processed/dspy_training_data/external",
                      help="Directory for external datasets")
    parser.add_argument("--integrated-data-dir", type=str,
                      default="data/processed/dspy_training_data/bible_corpus/integrated",
                      help="Directory for integrated dataset")
    parser.add_argument("--no-split", action="store_true",
                      help="Don't create train/val split")
    
    # Training options
    parser.add_argument("--optimizer", type=str, 
                      default="bootstrap",
                      choices=["bootstrap", "grpo", "simba", "miprov2", "none"],
                      help="DSPy optimizer to use for training")
    parser.add_argument("--model", type=str,
                      default="google/flan-t5-small",
                      help="Model to use for training")
    parser.add_argument("--lm-studio", action="store_true",
                      help="Use LM Studio for inference")
    parser.add_argument("--max-demos", type=int,
                      default=8,
                      help="Maximum number of demos to use")
    
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs(args.external_data_dir, exist_ok=True)
    os.makedirs(args.integrated_data_dir, exist_ok=True)
    
    # Check for script existence
    if not FETCH_SCRIPT.exists():
        logger.error(f"External dataset fetcher script not found: {FETCH_SCRIPT}")
        return
    
    if not INTEGRATE_SCRIPT.exists():
        logger.error(f"Dataset integration script not found: {INTEGRATE_SCRIPT}")
        return
    
    # Log the start of the pipeline
    logger.info("Starting full dataset integration pipeline")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Fetch external datasets
    if not args.skip_fetch:
        logger.info("=== Step 1: Fetching External Datasets ===")
        if not fetch_external_datasets(args.external_data_dir):
            logger.error("Dataset fetching failed. Aborting pipeline.")
            return
    else:
        logger.info("Skipping dataset fetching as requested")
    
    # Integrate datasets
    if not args.skip_integrate:
        logger.info("=== Step 2: Integrating Datasets ===")
        if not integrate_datasets(args.integrated_data_dir, args.no_split):
            logger.error("Dataset integration failed. Aborting pipeline.")
            return
    else:
        logger.info("Skipping dataset integration as requested")
    
    # Train model if requested
    if args.train:
        logger.info("=== Step 3: Training Model with Integrated Data ===")
        # Check if training script exists
        if not TRAIN_SCRIPT.exists():
            logger.error(f"Training script not found: {TRAIN_SCRIPT}")
            return
        
        # Update train_dspy_bible_qa.py to support integrated data
        try:
            # First check if the script needs modification (only if --use-integrated-data isn't already supported)
            update_needed = True
            with open(TRAIN_SCRIPT, 'r', encoding='utf-8') as f:
                if '--use-integrated-data' in f.read():
                    update_needed = False
            
            if update_needed:
                logger.info("Updating train_dspy_bible_qa.py to support integrated data")
                patch_training_script(TRAIN_SCRIPT)
        except Exception as e:
            logger.error(f"Error updating training script: {e}")
            logger.warning("Will try to run training without modifications")
        
        # Run training
        if not train_model(args.optimizer, args.model, args.lm_studio, args.max_demos):
            logger.error("Model training failed.")
            return
    else:
        logger.info("Skipping model training as requested")
    
    logger.info("Full dataset integration pipeline completed successfully")

def patch_training_script(script_path: Path):
    """
    Patch the training script to support using integrated data.
    
    Args:
        script_path: Path to the training script
    """
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add command-line argument for integrated data
        if 'parser.add_argument(' in content:
            parser_block_end = content.find('return parser.parse_args()')
            if parser_block_end > 0:
                integrated_arg = '''
    parser.add_argument(
        "--use-integrated-data",
        action="store_true",
        help="Use integrated dataset from data/processed/dspy_training_data/bible_corpus/integrated"
    )'''
                content = content[:parser_block_end] + integrated_arg + content[parser_block_end:]
        
        # Update data loading to check for integrated data
        if 'def load_data(' in content:
            load_data_start = content.find('def load_data(')
            if load_data_start > 0:
                # Find the function body
                func_body_start = content.find(':', load_data_start) + 1
                # Find indentation level
                next_line = content.find('\n', func_body_start) + 1
                indentation = ''
                for char in content[next_line:]:
                    if char.isspace():
                        indentation += char
                    else:
                        break
                
                # Add check for integrated data
                integrated_check = f'''
{indentation}# Check for integrated data if requested
{indentation}if hasattr(args, 'use_integrated_data') and args.use_integrated_data:
{indentation}    integrated_dir = Path("data/processed/dspy_training_data/bible_corpus/integrated")
{indentation}    train_path = integrated_dir / "qa_dataset_train.jsonl"
{indentation}    val_path = integrated_dir / "qa_dataset_val.jsonl"
{indentation}    
{indentation}    if train_path.exists() and val_path.exists():
{indentation}        logger.info(f"Loading integrated dataset from {{train_path}} and {{val_path}}")
{indentation}        
{indentation}        train_data = []
{indentation}        with open(train_path, 'r', encoding='utf-8') as f:
{indentation}            for line in f:
{indentation}                line = line.strip()
{indentation}                if line and not line.startswith('//'):
{indentation}                    train_data.append(json.loads(line))
{indentation}        
{indentation}        val_data = []
{indentation}        with open(val_path, 'r', encoding='utf-8') as f:
{indentation}            for line in f:
{indentation}                line = line.strip()
{indentation}                if line and not line.startswith('//'):
{indentation}                    val_data.append(json.loads(line))
{indentation}        
{indentation}        logger.info(f"Loaded {{len(train_data)}} training examples and {{len(val_data)}} validation examples from integrated dataset")
{indentation}        return train_data, val_data'''
                
                # Insert after function declaration
                content = content[:func_body_start] + integrated_check + content[func_body_start:]
        
        # Write updated content back
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Successfully updated {script_path} to support integrated data")
    
    except Exception as e:
        logger.error(f"Error patching training script: {e}")
        raise

if __name__ == "__main__":
    main() 