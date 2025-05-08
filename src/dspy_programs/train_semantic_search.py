#!/usr/bin/env python3
"""
Train DSPy models for the semantic search system

This module trains specialized DSPy models for Bible semantic search:
- Query expansion model: Expands search queries with relevant theological concepts
- Reranking model: Reranks search results based on relevance
- Topic hopping model: Identifies related Bible topics for multi-hop search

Uses MLflow for experiment tracking and model versioning.
"""

import os
import sys
import json
import logging
import pickle
import random
from datetime import datetime
from typing import List, Dict, Any, Tuple
import dspy
import mlflow
from dotenv import load_dotenv

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/semantic_search_training.log", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env.dspy')  # Use DSPy-specific env file if available
load_dotenv()  # Fall back to standard .env file

def init_mlflow():
    """Initialize MLflow tracking."""
    try:
        # Set up MLflow
        mlflow.set_tracking_uri("file:./mlruns")
        experiment_name = "semantic-search-training"
        
        # Create or get the experiment
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(experiment_name)
            else:
                experiment_id = experiment.experiment_id
        except Exception as e:
            logger.error(f"Error setting up MLflow experiment: {e}")
            experiment_id = None
        
        return experiment_id
    except Exception as e:
        logger.error(f"Error initializing MLflow: {e}")
        return None

def initialize_dspy():
    """Initialize DSPy with LM Studio configuration."""
    try:
        # Configure DSPy with LM Studio
        lm_studio_api = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
        lm_studio_model = os.getenv("LM_STUDIO_CHAT_MODEL", "llama3")
        
        logger.info(f"Initializing DSPy with LM Studio at {lm_studio_api} using model {lm_studio_model}")
        
        # Set environment variables for openai compatibility
        os.environ["OPENAI_API_KEY"] = "dummy-key"
        os.environ["OPENAI_API_BASE"] = lm_studio_api
        
        # Configure with the OpenAI-compatible endpoint
        lm = dspy.LM(
            provider="openai",
            model=lm_studio_model,
            api_base=lm_studio_api,
            api_key="dummy-key"
        )
        dspy.settings.configure(lm=lm)
        
        # Try a simple prediction to verify setup
        class SimpleSignature(dspy.Signature):
            """Simple signature for testing."""
            input_text = dspy.InputField()
            output_text = dspy.OutputField()
        
        simple_model = dspy.Predict(SimpleSignature)
        result = simple_model(input_text="Say hello")
        
        if not hasattr(result, 'output_text') or not result.output_text:
            logger.error("DSPy test prediction failed - no output generated")
            return False
        
        logger.info("DSPy initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing DSPy: {e}")
        return False

def load_training_examples():
    """
    Load training examples for semantic search models.
    
    Returns:
        Dictionary of training examples for each model type
    """
    try:
        examples_file = "data/processed/dspy_training_data/bible_corpus/dspy/semantic_search_examples.json"
        
        # Check if file exists
        if not os.path.exists(examples_file):
            logger.error(f"Training examples file not found: {examples_file}")
            
            # Create an empty examples file with the expected structure
            default_examples = {
                "query_expansion": [],
                "reranking": [],
                "topic_hopping": []
            }
            
            # Save the default structure
            os.makedirs(os.path.dirname(examples_file), exist_ok=True)
            with open(examples_file, "w") as f:
                json.dump(default_examples, f, indent=2)
            
            return default_examples
        
        # Load examples from file
        with open(examples_file, "r") as f:
            examples = json.load(f)
        
        # Verify the structure
        required_keys = ["query_expansion", "reranking", "topic_hopping"]
        for key in required_keys:
            if key not in examples:
                examples[key] = []
        
        logger.info(f"Loaded {sum(len(examples[k]) for k in examples)} training examples")
        return examples
    except Exception as e:
        logger.error(f"Error loading training examples: {e}")
        return {
            "query_expansion": [],
            "reranking": [],
            "topic_hopping": []
        }

def create_synthetic_examples():
    """
    Create synthetic training examples if no examples are available.
    
    Returns:
        Dictionary of synthetic examples for each model type
    """
    logger.info("Creating synthetic training examples")
    
    # Synthetic examples for query expansion
    query_expansion_examples = [
        {
            "query": "Love your enemies",
            "expanded_queries": [
                "Love your enemies",
                "Forgiveness in the Bible",
                "Jesus teachings on forgiveness",
                "How to treat those who persecute you",
                "Bible verses about loving your enemies"
            ]
        },
        {
            "query": "Creation of the world",
            "expanded_queries": [
                "Creation of the world",
                "Genesis creation account",
                "God created the heavens and the earth",
                "Six days of creation",
                "In the beginning God created"
            ]
        },
        {
            "query": "Faith definition",
            "expanded_queries": [
                "Faith definition",
                "Hebrews 11:1 faith",
                "What is faith in the Bible",
                "Biblical definition of faith",
                "Faith without works is dead"
            ]
        }
    ]
    
    # Synthetic examples for reranking
    reranking_examples = [
        {
            "query": "Love your enemies",
            "verses": [
                "Matthew 5:44: But I say to you, Love your enemies and pray for those who persecute you",
                "Luke 6:27: But I say to you who hear, Love your enemies, do good to those who hate you",
                "Romans 12:20: To the contrary, if your enemy is hungry, feed him; if he is thirsty, give him something to drink",
                "Proverbs 25:21: If your enemy is hungry, give him bread to eat, and if he is thirsty, give him water to drink",
                "1 John 4:20: If anyone says, I love God, and hates his brother, he is a liar"
            ],
            "reranked_verses": [
                {"reference": "Matthew 5:44", "score": 0.95},
                {"reference": "Luke 6:27", "score": 0.92},
                {"reference": "Romans 12:20", "score": 0.85},
                {"reference": "Proverbs 25:21", "score": 0.78},
                {"reference": "1 John 4:20", "score": 0.65}
            ]
        },
        {
            "query": "Faith is the substance of things hoped for",
            "verses": [
                "Hebrews 11:1: Now faith is the substance of things hoped for, the evidence of things not seen",
                "Romans 10:17: So then faith comes by hearing, and hearing by the word of God",
                "2 Corinthians 5:7: For we walk by faith, not by sight",
                "Ephesians 2:8: For by grace you have been saved through faith",
                "James 2:26: For as the body without the spirit is dead, so faith without works is dead also"
            ],
            "reranked_verses": [
                {"reference": "Hebrews 11:1", "score": 0.98},
                {"reference": "2 Corinthians 5:7", "score": 0.82},
                {"reference": "Romans 10:17", "score": 0.75},
                {"reference": "James 2:26", "score": 0.71},
                {"reference": "Ephesians 2:8", "score": 0.68}
            ]
        }
    ]
    
    # Synthetic examples for topic hopping
    topic_hopping_examples = [
        {
            "query": "How did Jesus teach us to pray?",
            "related_topics": [
                "Lord's Prayer",
                "Prayer in the Bible",
                "Jesus teaching on prayer",
                "How to pray effectively",
                "Matthew 6:9-13"
            ]
        },
        {
            "query": "What does the Bible say about salvation?",
            "related_topics": [
                "Salvation through faith",
                "Jesus as savior",
                "Eternal life",
                "John 3:16",
                "Romans road to salvation"
            ]
        }
    ]
    
    # Combine all examples
    return {
        "query_expansion": query_expansion_examples,
        "reranking": reranking_examples,
        "topic_hopping": topic_hopping_examples
    }

def prepare_training_data(examples_dict):
    """
    Prepare training data for each model type.
    
    Args:
        examples_dict: Dictionary of examples for each model type
        
    Returns:
        Dictionary of prepared training data for each model type
    """
    try:
        # Import required signatures
        from .semantic_search import BibleQueryExpansion, BibleVerseReranker, TopicHopping
        
        # Handle case when no examples are available
        if (not examples_dict["query_expansion"] and 
            not examples_dict["reranking"] and 
            not examples_dict["topic_hopping"]):
            logger.warning("No training examples found, using synthetic examples")
            examples_dict = create_synthetic_examples()
        
        # Prepare query expansion training data
        query_expansion_data = []
        for example in examples_dict["query_expansion"]:
            if "query" in example and "expanded_queries" in example:
                query_expansion_data.append(
                    dspy.Example(
                        query=example["query"],
                        expanded_queries=example["expanded_queries"]
                    ).with_inputs("query")
                )
        
        # Prepare reranking training data
        reranking_data = []
        for example in examples_dict["reranking"]:
            if "query" in example and "verses" in example and "reranked_verses" in example:
                reranking_data.append(
                    dspy.Example(
                        query=example["query"],
                        verses=example["verses"],
                        reranked_verses=example["reranked_verses"]
                    ).with_inputs("query", "verses")
                )
        
        # Prepare topic hopping training data
        topic_hopping_data = []
        for example in examples_dict["topic_hopping"]:
            if "query" in example and "related_topics" in example:
                topic_hopping_data.append(
                    dspy.Example(
                        query=example["query"],
                        related_topics=example["related_topics"]
                    ).with_inputs("query")
                )
        
        logger.info(f"Prepared {len(query_expansion_data)} query expansion examples")
        logger.info(f"Prepared {len(reranking_data)} reranking examples")
        logger.info(f"Prepared {len(topic_hopping_data)} topic hopping examples")
        
        return {
            "query_expansion": query_expansion_data,
            "reranking": reranking_data,
            "topic_hopping": topic_hopping_data
        }
    except Exception as e:
        logger.error(f"Error preparing training data: {e}")
        return {
            "query_expansion": [],
            "reranking": [],
            "topic_hopping": []
        }

def train_model(model_type, training_data, experiment_id=None):
    """
    Train a specific DSPy model.
    
    Args:
        model_type: Type of model to train ("query_expansion", "reranking", or "topic_hopping")
        training_data: List of DSPy examples for training
        experiment_id: MLflow experiment ID for tracking
        
    Returns:
        Trained model or None if training fails
    """
    if not training_data:
        logger.warning(f"No training data available for {model_type}")
        return None
    
    # Set up MLflow run
    with mlflow.start_run(experiment_id=experiment_id, run_name=f"{model_type}_training") as run:
        try:
            # Import required signatures
            from .semantic_search import (
                BibleQueryExpansion, 
                BibleVerseReranker, 
                TopicHopping
            )
            
            # Log parameters
            mlflow.log_param("model_type", model_type)
            mlflow.log_param("num_examples", len(training_data))
            mlflow.log_param("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
            
            # Create the appropriate predictor based on model type
            if model_type == "query_expansion":
                base_predictor = dspy.Predict(BibleQueryExpansion)
                signature = BibleQueryExpansion
            elif model_type == "reranking":
                base_predictor = dspy.Predict(BibleVerseReranker)
                signature = BibleVerseReranker
            elif model_type == "topic_hopping":
                base_predictor = dspy.Predict(TopicHopping)
                signature = TopicHopping
            else:
                logger.error(f"Unknown model type: {model_type}")
                return None
            
            # Split data into train/test sets
            random.shuffle(training_data)
            split_idx = max(1, int(len(training_data) * 0.8))
            train_data = training_data[:split_idx]
            test_data = training_data[split_idx:]
            
            if len(test_data) == 0 and len(train_data) > 1:
                # If we only have training data, use one example for testing
                test_data = [train_data[-1]]
                train_data = train_data[:-1]
            
            # Log the split
            mlflow.log_param("train_size", len(train_data))
            mlflow.log_param("test_size", len(test_data))
            
            # Define optimizer
            teleprompter = dspy.teleprompt.BootstrapFewShot(k=min(3, len(train_data)))
            
            # Train the model
            logger.info(f"Training {model_type} model with {len(train_data)} examples")
            trained_model = teleprompter.compile(
                base_predictor,
                train_data=train_data,
                eval_data=test_data if test_data else None
            )
            
            # Save the model to disk
            model_dir = "models/dspy/semantic_search"
            os.makedirs(model_dir, exist_ok=True)
            model_path = f"{model_dir}/{model_type}.pkl"
            
            with open(model_path, "wb") as f:
                pickle.dump(trained_model, f)
            
            # Log the model artifact
            mlflow.log_artifact(model_path)
            
            logger.info(f"Successfully trained and saved {model_type} model to {model_path}")
            return trained_model
        except Exception as e:
            logger.error(f"Error training {model_type} model: {e}")
            mlflow.log_param("error", str(e))
            return None

def train_all_models(experiment_id=None):
    """
    Train all semantic search models.
    
    Args:
        experiment_id: MLflow experiment ID for tracking
        
    Returns:
        Dictionary of trained models
    """
    # Load and prepare training data
    examples_dict = load_training_examples()
    training_data = prepare_training_data(examples_dict)
    
    # Train each model
    models = {}
    
    # Query expansion model
    logger.info("Training query expansion model")
    query_expansion_model = train_model(
        "query_expander", 
        training_data["query_expansion"],
        experiment_id
    )
    if query_expansion_model:
        models["query_expander"] = query_expansion_model
    
    # Reranking model
    logger.info("Training reranking model")
    reranking_model = train_model(
        "reranker", 
        training_data["reranking"],
        experiment_id
    )
    if reranking_model:
        models["reranker"] = reranking_model
    
    # Topic hopping model
    logger.info("Training topic hopping model")
    topic_hopping_model = train_model(
        "topic_hopper", 
        training_data["topic_hopping"],
        experiment_id
    )
    if topic_hopping_model:
        models["topic_hopper"] = topic_hopping_model
    
    return models

def main():
    """Main function for training semantic search models."""
    logger.info("Starting semantic search model training")
    
    # Initialize DSPy
    dspy_initialized = initialize_dspy()
    if not dspy_initialized:
        logger.error("Failed to initialize DSPy, aborting training")
        return 1
    
    # Initialize MLflow
    experiment_id = init_mlflow()
    
    # Train all models
    models = train_all_models(experiment_id)
    
    # Report results
    if models:
        logger.info(f"Successfully trained {len(models)} models")
        for model_name in models:
            logger.info(f"- {model_name}")
        return 0
    else:
        logger.error("No models were successfully trained")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 