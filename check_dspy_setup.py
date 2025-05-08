#!/usr/bin/env python3
"""
DSPy and MLflow Setup Verification Script

This script checks if the DSPy environment is correctly set up with:
1. DSPy library installed and configured
2. MLflow tracking configured
3. LM Studio connection working (if enabled)
4. Training data available
"""

import os
import sys
import json
import logging
from pathlib import Path
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_libraries():
    """Check if required libraries are installed."""
    print("\n=== Checking Required Libraries ===")
    
    # Check Python version
    python_version = sys.version.split()[0]
    print(f"Python version: {python_version}")
    
    # Check DSPy
    try:
        import dspy
        print(f"DSPy version: {dspy.__version__}")
    except ImportError:
        print("❌ DSPy not installed. Install it with: pip install dspy")
        return False
    
    # Check MLflow
    try:
        import mlflow
        print(f"MLflow version: {mlflow.__version__}")
    except ImportError:
        print("❌ MLflow not installed. Install it with: pip install mlflow")
        return False
    
    # Check dotenv
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv installed")
    except ImportError:
        print("❌ python-dotenv not installed. Install it with: pip install python-dotenv")
        return False
    
    print("✅ All required libraries installed")
    return True

def check_environment_variables():
    """Check if environment variables are properly configured."""
    print("\n=== Checking Environment Variables ===")
    
    # Load environment variables
    from dotenv import load_dotenv
    
    if os.path.exists(".env.dspy"):
        load_dotenv(".env.dspy")
        print("✅ .env.dspy file found and loaded")
    else:
        print("⚠️ .env.dspy file not found, checking for .env")
        if os.path.exists(".env"):
            load_dotenv()
            print("✅ .env file found and loaded")
        else:
            print("❌ No environment files found (.env.dspy or .env)")
            return False
    
    # Check critical environment variables
    critical_vars = {
        "LM_STUDIO_API_URL": "http://localhost:1234/v1",
        "LM_STUDIO_EMBEDDING_MODEL": "text-embedding-nomic-embed-text-v1.5@q8_0",
        "LM_STUDIO_CHAT_MODEL": None,
        "MLFLOW_TRACKING_URI": "./mlruns",
        "MLFLOW_EXPERIMENT_NAME": "dspy_bible_qa",
    }
    
    all_ok = True
    for var, default in critical_vars.items():
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        elif default:
            print(f"⚠️ {var} not set, using default: {default}")
        else:
            print(f"❌ {var} not set and no default available")
            all_ok = False
    
    return all_ok

def check_data_availability():
    """Check if training data is available."""
    print("\n=== Checking Data Availability ===")
    
    data_paths = [
        "data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json",
        "data/processed/dspy_training_data/bible_corpus/dspy/qa_dataset.jsonl",
        "data/processed/dspy_training_data/bible_corpus/dspy/qa_dataset_train.jsonl",
        "data/processed/dspy_training_data/bible_corpus/dspy/qa_dataset_val.jsonl",
    ]
    
    found_any = False
    found_all = True
    example_counts = {}
    
    for path in data_paths:
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"✅ Found {path} ({size_mb:.2f} MB)")
            found_any = True
            
            # Count examples
            try:
                if path.endswith(".json"):
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        example_counts[path] = len(data)
                elif path.endswith(".jsonl"):
                    count = 0
                    with open(path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('//'):
                                count += 1
                    example_counts[path] = count
            except Exception as e:
                print(f"⚠️ Error counting examples in {path}: {e}")
        else:
            print(f"❌ Missing {path}")
            found_all = False
    
    if not found_any:
        print("❌ No training data found. Run the data expansion script first.")
        return False
    
    # Print example counts
    print("\nExample counts:")
    for path, count in example_counts.items():
        print(f"- {os.path.basename(path)}: {count} examples")
    
    if not found_all:
        print("\n⚠️ Some data files are missing. Consider running the data expansion script.")
    
    return found_any

def check_lm_studio():
    """Check if LM Studio is running and accessible."""
    print("\n=== Checking LM Studio Connection ===")
    
    import requests
    
    lm_studio_url = os.environ.get("LM_STUDIO_API_URL", "http://localhost:1234/v1")
    models_url = f"{lm_studio_url}/models"
    
    try:
        response = requests.get(models_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ LM Studio is running at {lm_studio_url}")
            
            # Check available models
            models = response.json()
            print(f"Available models: {len(models)} found")
            for model in models:
                print(f"- {model.get('id', 'Unknown')}")
            
            # Test embedding
            embedding_model = os.environ.get("LM_STUDIO_EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5@q8_0")
            
            print(f"\nTesting embedding model: {embedding_model}")
            embed_url = f"{lm_studio_url}/embeddings"
            
            try:
                embed_response = requests.post(
                    embed_url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": embedding_model,
                        "input": "Test embedding for Bible text"
                    },
                    timeout=10
                )
                
                if embed_response.status_code == 200:
                    result = embed_response.json()
                    if "data" in result and len(result["data"]) > 0:
                        embedding = result["data"][0]["embedding"]
                        print(f"✅ Embedding test successful (dimension: {len(embedding)})")
                    else:
                        print(f"❌ Unexpected embedding response format: {result}")
                else:
                    print(f"❌ Embedding test failed: {embed_response.status_code} - {embed_response.text}")
            except Exception as e:
                print(f"❌ Error testing embedding: {e}")
            
            return True
        else:
            print(f"❌ LM Studio API returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to LM Studio at {lm_studio_url}")
        print("Make sure LM Studio is running and the API server is enabled.")
        return False
    except Exception as e:
        print(f"❌ Error checking LM Studio: {e}")
        return False

def check_mlflow():
    """Check if MLflow is configured properly."""
    print("\n=== Checking MLflow Configuration ===")
    
    try:
        import mlflow
        
        # Check tracking URI
        tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "./mlruns")
        mlflow.set_tracking_uri(tracking_uri)
        
        print(f"MLflow tracking URI: {mlflow.get_tracking_uri()}")
        
        # Check if directory exists
        if tracking_uri.startswith("./") or tracking_uri.startswith("/"):
            if os.path.exists(tracking_uri.replace("./", "")):
                print(f"✅ MLflow tracking directory exists")
            else:
                print(f"⚠️ MLflow tracking directory does not exist, it will be created when needed")
        
        # Try to list experiments
        experiments = mlflow.search_experiments()
        print(f"Found {len(experiments)} MLflow experiments")
        
        for experiment in experiments:
            print(f"- {experiment.name}")
        
        # Create test experiment if needed
        experiment_name = os.environ.get("MLFLOW_EXPERIMENT_NAME", "dspy_bible_qa")
        
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment:
            print(f"✅ Found experiment '{experiment_name}'")
        else:
            print(f"⚠️ Experiment '{experiment_name}' not found, it will be created when needed")
        
        # Try to autoload DSPy
        mlflow.dspy.autolog()
        print("✅ MLflow DSPy autologging enabled")
        
        return True
    except Exception as e:
        print(f"❌ Error checking MLflow: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all checks."""
    print("DSPy and MLflow Setup Verification")
    print("==================================")
    
    # Create logs directory if needed
    os.makedirs("logs", exist_ok=True)
    
    # Run checks
    libraries_ok = check_libraries()
    env_vars_ok = check_environment_variables()
    data_ok = check_data_availability()
    lm_studio_ok = check_lm_studio()
    mlflow_ok = check_mlflow()
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Required Libraries: {'✅' if libraries_ok else '❌'}")
    print(f"Environment Variables: {'✅' if env_vars_ok else '⚠️'}")
    print(f"Training Data: {'✅' if data_ok else '❌'}")
    print(f"LM Studio Connection: {'✅' if lm_studio_ok else '❌'}")
    print(f"MLflow Configuration: {'✅' if mlflow_ok else '❌'}")
    
    # Overall status
    critical_checks = [libraries_ok, env_vars_ok, data_ok, lm_studio_ok, mlflow_ok]
    if all(critical_checks):
        print("\n✅ All checks passed! The system is ready for training.")
        return 0
    elif libraries_ok and (data_ok or env_vars_ok):
        print("\n⚠️ Some checks failed, but you may be able to proceed with caution.")
        return 0
    else:
        print("\n❌ Critical checks failed. Please resolve the issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 