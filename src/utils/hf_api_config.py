"""
Hugging Face API Configuration

This module provides functionality for configuring and accessing Hugging Face
models via their API for DSPy training orchestration.
"""

import os
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default model configurations
DEFAULT_MODELS = {
    'embedding': 'sentence-transformers/all-MiniLM-L6-v2',
    'completion': 'mistralai/Mistral-7B-Instruct-v0.2',
    'optimizer': 'meta-llama/Llama-2-7b-chat-hf',
}

class HuggingFaceAPI:
    """Client for interacting with Hugging Face API."""
    
    def __init__(self, api_token=None):
        """Initialize the Hugging Face API client.
        
        Args:
            api_token (str, optional): Hugging Face API token. If not provided,
                                       looks for HF_API_TOKEN environment variable.
        """
        self.api_token = api_token or os.getenv('HF_API_TOKEN')
        if not self.api_token:
            logger.warning("No Hugging Face API token provided. Some features may be limited.")
        
        self.api_url = "https://api-inference.huggingface.co/models/"
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
    
    def query_model(self, model_id, payload):
        """Query a model with the given payload.
        
        Args:
            model_id (str): The Hugging Face model ID
            payload (dict): The payload to send to the model
            
        Returns:
            dict: The model response
        """
        try:
            response = requests.post(
                f"{self.api_url}{model_id}",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying model {model_id}: {e}")
            return {"error": str(e)}
    
    def get_embeddings(self, texts, model_id=None):
        """Get embeddings for the given texts.
        
        Args:
            texts (list): List of strings to embed
            model_id (str, optional): Model ID to use for embeddings
            
        Returns:
            list: List of embeddings
        """
        model = model_id or DEFAULT_MODELS['embedding']
        try:
            response = self.query_model(model, {"inputs": texts})
            if isinstance(response, list):
                return response
            elif "error" in response:
                logger.error(f"Error getting embeddings: {response['error']}")
                return None
            return response
        except Exception as e:
            logger.error(f"Exception during embedding: {e}")
            return None
    
    def generate_completion(self, prompt, model_id=None, **kwargs):
        """Generate a text completion.
        
        Args:
            prompt (str): The prompt to generate from
            model_id (str, optional): Model ID to use for generation
            **kwargs: Additional parameters for generation
            
        Returns:
            dict: Generated text and metadata
        """
        model = model_id or DEFAULT_MODELS['completion']
        payload = {
            "inputs": prompt,
            "parameters": kwargs
        }
        return self.query_model(model, payload)
    
    def test_connection(self, model_id=None):
        """Test the connection to the Hugging Face API.
        
        Args:
            model_id (str, optional): Model ID to test connection with
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        model = model_id or DEFAULT_MODELS['embedding']
        try:
            response = self.query_model(model, {"inputs": "Hello, world!"})
            if "error" in response:
                logger.error(f"Connection test failed: {response['error']}")
                return False
            logger.info(f"Successfully connected to Hugging Face API using model {model}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed with exception: {e}")
            return False

def save_api_token(token, env_file='.env'):
    """Save the Hugging Face API token to the .env file.
    
    Args:
        token (str): The API token
        env_file (str): Path to the .env file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read existing .env file
        env_path = Path(env_file)
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Check if token already exists
            token_exists = False
            for i, line in enumerate(lines):
                if line.startswith('HF_API_TOKEN='):
                    lines[i] = f'HF_API_TOKEN={token}\n'
                    token_exists = True
                    break
            
            # Add token if it doesn't exist
            if not token_exists:
                lines.append(f'HF_API_TOKEN={token}\n')
            
            # Write updated .env file
            with open(env_path, 'w') as f:
                f.writelines(lines)
        else:
            # Create new .env file
            with open(env_path, 'w') as f:
                f.write(f'HF_API_TOKEN={token}\n')
        
        logger.info(f"Successfully saved Hugging Face API token to {env_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving API token: {e}")
        return False

def get_available_models(category=None):
    """Get list of recommended models for DSPy training.
    
    Args:
        category (str, optional): Filter by category ('embedding', 'completion', 'optimizer')
        
    Returns:
        dict: Dictionary of recommended models by category
    """
    models = {
        'embedding': [
            {
                'id': 'sentence-transformers/all-MiniLM-L6-v2',
                'description': 'Fast, lightweight embedding model for general text similarity',
                'dimensions': 384,
                'recommended_for': 'General purpose text embeddings'
            },
            {
                'id': 'intfloat/e5-large-v2',
                'description': 'High quality text embeddings with 1024 dimensions',
                'dimensions': 1024,
                'recommended_for': 'High quality semantic search'
            },
            {
                'id': 'sentence-transformers/all-mpnet-base-v2',
                'description': 'Balance of quality and performance',
                'dimensions': 768,
                'recommended_for': 'Production use cases balancing quality and cost'
            }
        ],
        'completion': [
            {
                'id': 'mistralai/Mistral-7B-Instruct-v0.2',
                'description': 'Powerful instruction-following model, good balance of quality and speed',
                'parameters': '7B',
                'recommended_for': 'General instruction following, orchestration'
            },
            {
                'id': 'google/gemma-7b-it',
                'description': 'Google\'s lightweight instruction model',
                'parameters': '7B',
                'recommended_for': 'Instruction following, good for resource-constrained environments'
            },
            {
                'id': 'HuggingFaceH4/zephyr-7b-beta',
                'description': 'Fine-tuned LLaMA model optimized for instructions',
                'parameters': '7B',
                'recommended_for': 'DSPy optimization, instruction templates'
            }
        ],
        'optimizer': [
            {
                'id': 'meta-llama/Llama-2-7b-chat-hf',
                'description': 'Meta\'s powerful LLaMA 2 model, requires acceptance of use conditions',
                'parameters': '7B',
                'recommended_for': 'DSPy trace optimization, complex reasoning'
            },
            {
                'id': 'mistralai/Mistral-7B-Instruct-v0.2',
                'description': 'Versatile model for both completion and optimization',
                'parameters': '7B', 
                'recommended_for': 'Multi-purpose usage in DSPy pipelines'
            },
            {
                'id': 'databricks/dolly-v2-7b',
                'description': 'Instruction-tuned model with permissive license',
                'parameters': '7B',
                'recommended_for': 'Commercial applications with more permissive licensing'
            }
        ]
    }
    
    if category and category in models:
        return {category: models[category]}
    
    return models

# Initialize with the provided token if available
def initialize_with_token(token):
    """Initialize the HuggingFace API with the given token.
    
    Args:
        token (str): The API token
        
    Returns:
        HuggingFaceAPI: Initialized API client
    """
    save_api_token(token)
    return HuggingFaceAPI(token) 