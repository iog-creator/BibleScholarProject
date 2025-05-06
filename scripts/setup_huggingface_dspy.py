#!/usr/bin/env python3
"""
Set up Hugging Face API for DSPy Training

This script:
1. Sets up the Hugging Face API token
2. Tests connection to various recommended models
3. Selects the best models for DSPy training
4. Configures the DSPy environment to use the selected models
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the Hugging Face API configuration
from src.utils.hf_api_config import (
    HuggingFaceAPI,
    save_api_token,
    get_available_models,
    initialize_with_token
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/huggingface_setup.log', 'w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def setup_directory_structure():
    """Create the necessary directories for DSPy and Hugging Face integration."""
    directories = [
        'logs',
        'models/huggingface',
        'data/processed/dspy_training_data/huggingface',
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def test_model_connection(hf_api, model_id):
    """Test connection to a specific model.
    
    Args:
        hf_api (HuggingFaceAPI): The API client
        model_id (str): The model ID to test
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    logger.info(f"Testing connection to model: {model_id}")
    
    if 'embedding' in model_id.lower() or model_id == 'sentence-transformers/all-MiniLM-L6-v2':
        # Test embedding model
        try:
            result = hf_api.get_embeddings(["Test connection to Hugging Face API"], model_id=model_id)
            if result is not None:
                logger.info(f"✓ Successfully connected to embedding model: {model_id}")
                return True
            logger.error(f"× Failed to connect to embedding model: {model_id}")
            return False
        except Exception as e:
            logger.error(f"× Error testing embedding model {model_id}: {e}")
            return False
    else:
        # Test completion model
        try:
            result = hf_api.generate_completion(
                "Complete this sentence: The Bible contains",
                model_id=model_id,
                max_length=20
            )
            if result and not isinstance(result, dict) and not "error" in result:
                logger.info(f"✓ Successfully connected to completion model: {model_id}")
                return True
            logger.error(f"× Failed to connect to completion model: {model_id}")
            return False
        except Exception as e:
            logger.error(f"× Error testing completion model {model_id}: {e}")
            return False

def select_best_models(hf_api):
    """Test and select the best models for DSPy training.
    
    Args:
        hf_api (HuggingFaceAPI): The API client
        
    Returns:
        dict: Selected models by category
    """
    logger.info("Testing and selecting best models for DSPy training...")
    
    all_models = get_available_models()
    selected_models = {}
    
    # Test embedding models
    logger.info("Testing embedding models...")
    for model in all_models['embedding']:
        if test_model_connection(hf_api, model['id']):
            selected_models.setdefault('embedding', []).append(model)
    
    # Test completion models
    logger.info("Testing completion models...")
    for model in all_models['completion']:
        if test_model_connection(hf_api, model['id']):
            selected_models.setdefault('completion', []).append(model)
    
    # Test optimizer models
    logger.info("Testing optimizer models...")
    for model in all_models['optimizer']:
        if test_model_connection(hf_api, model['id']):
            selected_models.setdefault('optimizer', []).append(model)
    
    # Save selected models
    with open('models/huggingface/selected_models.json', 'w') as f:
        json.dump(selected_models, f, indent=2)
    
    logger.info(f"Selected models saved to: models/huggingface/selected_models.json")
    
    # Return best model for each category
    best_models = {}
    for category, models in selected_models.items():
        if models:
            best_models[category] = models[0]['id']
    
    return best_models

def create_dspy_config(best_models):
    """Create DSPy configuration for the selected models.
    
    Args:
        best_models (dict): The best models by category
    """
    try:
        config = {
            "model_provider": "huggingface",
            "api_base": "https://api-inference.huggingface.co/models",
            "models": best_models,
            "environment": "production",
            "cache_dir": "models/huggingface/cache",
            "telemetry": False
        }
        
        # Save config to JSON
        config_path = 'models/huggingface/dspy_config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"DSPy configuration saved to: {config_path}")
        
        # Create DSPy initialization script
        init_script = f"""#!/usr/bin/env python3
\"\"\"
DSPy Initialization with Hugging Face

This module initializes DSPy with the selected Hugging Face models.
\"\"\"

import os
import dspy
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_dspy():
    \"\"\"Initialize DSPy with Hugging Face models.\"\"\"
    # Get API token from environment
    hf_token = os.getenv('HF_API_TOKEN')
    if not hf_token:
        logger.warning("No Hugging Face API token found in environment")
        return False
    
    # Load model configuration
    config_path = Path('models/huggingface/dspy_config.json')
    if not config_path.exists():
        logger.error(f"DSPy configuration not found at: {{config_path}}")
        return False
    
    # Initialize DSPy with Hugging Face models
    try:
        # Set up Hugging Face client
        hf_client = dspy.HFClientWithCache(
            model="{best_models.get('completion', 'mistralai/Mistral-7B-Instruct-v0.2')}",
            api_key=hf_token
        )
        
        # Configure DSPy to use Hugging Face
        dspy.settings.configure(lm=hf_client)
        
        # Set up embedding model for optimizers
        embedding_model = "{best_models.get('embedding', 'sentence-transformers/all-MiniLM-L6-v2')}"
        dspy.settings.configure(embedding_model=embedding_model)
        
        logger.info("DSPy successfully initialized with Hugging Face models")
        return True
    except Exception as e:
        logger.error(f"Error initializing DSPy with Hugging Face: {{e}}")
        return False

# Auto-initialize when imported
if __name__ == "__main__":
    initialize_dspy()
"""
        
        # Save initialization script
        init_script_path = 'src/utils/dspy_hf_init.py'
        with open(init_script_path, 'w') as f:
            f.write(init_script)
        
        logger.info(f"DSPy initialization script saved to: {init_script_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating DSPy configuration: {e}")
        return False

def main():
    """Main function to set up the Hugging Face API for DSPy."""
    parser = argparse.ArgumentParser(description='Set up Hugging Face API for DSPy training')
    parser.add_argument('--token', help='Hugging Face API token')
    parser.add_argument('--test-all', action='store_true', help='Test all recommended models')
    args = parser.parse_args()
    
    token = args.token or os.getenv('HF_API_TOKEN')
    
    # Create necessary directories
    setup_directory_structure()
    
    if not token:
        logger.error("No Hugging Face API token provided. Please provide a token using --token or set the HF_API_TOKEN environment variable.")
        return False
    
    # Initialize the API client
    hf_api = initialize_with_token(token)
    
    # Test API connection
    if not hf_api.test_connection():
        logger.error("Failed to connect to Hugging Face API. Please check your token and try again.")
        return False
    
    logger.info("Successfully connected to Hugging Face API!")
    
    # Select best models
    best_models = select_best_models(hf_api)
    
    if not best_models:
        logger.error("No suitable models found. Please check your internet connection and Hugging Face account permissions.")
        return False
    
    logger.info(f"Selected best models: {best_models}")
    
    # Create DSPy configuration
    if create_dspy_config(best_models):
        logger.info("Successfully configured DSPy with Hugging Face models!")
        
        # Print recommendations
        print("\n=== Hugging Face Integration Complete ===")
        print("\nSelected models:")
        for category, model_id in best_models.items():
            print(f"- {category}: {model_id}")
        
        print("\nNext steps:")
        print("1. Import the DSPy initialization in your training scripts:")
        print("   from src.utils.dspy_hf_init import initialize_dspy")
        print("2. Run your DSPy training scripts with the configured models")
        print("3. Check the logs directory for detailed information")
        
        return True
    else:
        logger.error("Failed to configure DSPy with Hugging Face models.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 