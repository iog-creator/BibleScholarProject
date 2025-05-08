#!/usr/bin/env python3
"""
Load trained semantic search models for Bible search enhancement

This module handles loading of DSPy-trained models for the semantic search system:
- Query expansion model
- Search result reranking model
- Topic hopping model
"""

import os
import logging
import pickle
from typing import Dict, Any, Optional
import dspy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/semantic_search_models.log", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_model(model_name, default_module=None):
    """
    Load a DSPy model from disk.
    
    Args:
        model_name: Name of the model to load
        default_module: Default module to use if model can't be loaded
        
    Returns:
        Loaded model or default module
    """
    try:
        model_path = f"models/dspy/semantic_search/{model_name}.pkl"
        
        # Check if model file exists
        if not os.path.exists(model_path):
            logger.warning(f"Model file not found: {model_path}")
            return default_module
        
        # Load the model from pickle
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        
        logger.info(f"Successfully loaded model: {model_name}")
        return model
    except Exception as e:
        logger.error(f"Error loading model {model_name}: {e}")
        return default_module

def load_models():
    """
    Load all trained semantic search models.
    
    Returns:
        Dictionary of loaded models or None if loading fails
    """
    try:
        # Set up DSPy environment
        from .semantic_search import BibleQueryExpansion, BibleVerseReranker, TopicHopping
        
        # Ensure models directory exists
        os.makedirs("models/dspy/semantic_search", exist_ok=True)
        
        # Create default modules
        default_query_expander = dspy.Predict(BibleQueryExpansion)
        default_reranker = dspy.Predict(BibleVerseReranker)
        default_topic_hopper = dspy.Predict(TopicHopping)
        
        # Try to load trained models
        query_expander = load_model("query_expander", default_query_expander)
        reranker = load_model("reranker", default_reranker)
        topic_hopper = load_model("topic_hopper", default_topic_hopper)
        
        # Check if at least one model was loaded successfully
        if (query_expander is default_query_expander and
            reranker is default_reranker and
            topic_hopper is default_topic_hopper):
            logger.warning("No trained models were loaded successfully")
            # Return None to indicate that no models were loaded
            return None
        
        # Create models dictionary
        models = {
            "query_expander": query_expander,
            "reranker": reranker,
            "topic_hopper": topic_hopper
        }
        
        logger.info("Semantic search models loaded successfully")
        return models
    except Exception as e:
        logger.error(f"Error loading semantic search models: {e}")
        return None

def configure_semantic_search(search_module, models):
    """
    Configure a semantic search module with loaded models.
    
    Args:
        search_module: EnhancedSemanticSearch instance
        models: Dictionary of loaded models
        
    Returns:
        Configured search module
    """
    try:
        if not models:
            logger.warning("No models provided for configuration")
            return search_module
        
        # Replace predictors with trained models
        if "query_expander" in models and models["query_expander"]:
            search_module.query_expander = models["query_expander"]
        
        if "reranker" in models and models["reranker"]:
            search_module.reranker = models["reranker"]
        
        if "topic_hopper" in models and models["topic_hopper"]:
            search_module.topic_hopper = models["topic_hopper"]
        
        logger.info("Search module configured with trained models")
        return search_module
    except Exception as e:
        logger.error(f"Error configuring search module: {e}")
        return search_module

# For testing
if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Try to load models
    loaded_models = load_models()
    
    # Display results
    if loaded_models:
        print("\nLoaded models:")
        for name, model in loaded_models.items():
            print(f"- {name}: {type(model).__name__}")
    else:
        print("\nNo models were loaded.") 