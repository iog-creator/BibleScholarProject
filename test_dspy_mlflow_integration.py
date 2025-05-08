#!/usr/bin/env python3
"""
Test DSPy with MLflow Integration

This script tests the integration between DSPy, MLflow, and LM Studio,
verifying all components work together correctly.

Usage:
    python test_dspy_mlflow_integration.py [--no-mlflow-server]
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_dspy_mlflow_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test DSPy with MLflow Integration")
    parser.add_argument(
        "--no-mlflow-server", 
        action="store_true",
        help="Skip checking for MLflow server (use local tracking)"
    )
    return parser.parse_args()

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import dspy
        import mlflow
        from mlflow.tracking import MlflowClient
        
        logger.info(f"DSPy version: {dspy.__version__}")
        logger.info(f"MLflow version: {mlflow.__version__}")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.info("Install with: pip install dspy-ai mlflow")
        return False

def load_environment():
    """Load environment variables from .env.dspy file."""
    # Load from .env.dspy for DSPy-specific configuration
    load_dotenv('.env.dspy')
    
    # Check required environment variables
    required_vars = [
        "LM_STUDIO_API_URL",
        "LM_STUDIO_CHAT_MODEL"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Please check your .env.dspy file and set these variables")
        return False
    
    logger.info(f"LM Studio API URL: {os.environ.get('LM_STUDIO_API_URL')}")
    logger.info(f"LM Studio Chat Model: {os.environ.get('LM_STUDIO_CHAT_MODEL')}")
    
    return True

def configure_mlflow(check_server=True):
    """Configure MLflow for tracking."""
    import mlflow
    
    if check_server:
        # Try to connect to MLflow tracking server
        try:
            mlflow.set_tracking_uri("http://localhost:5000")
            client = mlflow.tracking.MlflowClient()
            client.search_experiments()  # Will fail if server is not running
            logger.info("Successfully connected to MLflow server at http://localhost:5000")
        except Exception as e:
            logger.warning(f"Could not connect to MLflow server: {e}")
            logger.warning("Using local MLflow tracking (./mlruns)")
            mlflow.set_tracking_uri("")  # Use local file-based tracking
    else:
        logger.info("Using local MLflow tracking as specified (./mlruns)")
        mlflow.set_tracking_uri("")
    
    # Create or set experiment
    experiment_name = "dspy_mlflow_test"
    mlflow.set_experiment(experiment_name)
    
    # Enable MLflow autologging for DSPy
    mlflow.dspy.autolog()
    
    return True

def configure_dspy():
    """Configure DSPy to use LM Studio."""
    import dspy
    import dspy_json_patch  # Apply JSON patch for LM Studio compatibility
    
    # Enable experimental features for DSPy 2.6
    dspy.settings.experimental = True
    
    lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://localhost:1234/v1")
    model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
    
    logger.info(f"Configuring DSPy with LM Studio: {lm_studio_api}, model: {model_name}")
    
    lm = dspy.LM(
        model_type="openai",
        model=model_name,
        api_base=lm_studio_api,
        api_key="dummy",  # LM Studio doesn't check API keys
        config={"temperature": 0.1, "max_tokens": 512}
    )
    
    dspy.configure(lm=lm)
    logger.info("DSPy configured with LM Studio successfully")
    return True

def create_bible_qa_model():
    """Create a simple Bible QA model."""
    import dspy
    
    # Define the signature
    class BibleQA(dspy.Signature):
        """Answer questions about Bible verses."""
        context = dspy.InputField(desc="Biblical context or verse")
        question = dspy.InputField(desc="Question about the biblical context")
        reasoning = dspy.OutputField(desc="Reasoning about the question based on the context")
        answer = dspy.OutputField(desc="Answer to the question")
    
    # Create a simple module
    class BibleQAModule(dspy.Module):
        """Chain of Thought module for Bible QA."""
        def __init__(self):
            super().__init__()
            self.qa_model = dspy.ChainOfThought(BibleQA)
        
        def forward(self, context, question):
            return self.qa_model(context=context, question=question)
    
    return BibleQAModule()

def create_sample_dataset():
    """Create a sample dataset for optimization."""
    import dspy
    
    examples = [
        dspy.Example(
            context="Genesis 1:1: In the beginning God created the heaven and the earth.",
            question="What did God create according to Genesis 1:1?",
            reasoning="The verse states that God created the heaven and the earth.",
            answer="The heaven and the earth."
        ),
        dspy.Example(
            context="John 3:16: For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
            question="What does John 3:16 say about how to receive everlasting life?",
            reasoning="The verse states that whoever believes in God's only begotten Son will have everlasting life.",
            answer="By believing in God's only begotten Son."
        ),
        dspy.Example(
            context="Psalm 23:1: The LORD is my shepherd; I shall not want.",
            question="What metaphor is used to describe the LORD in Psalm 23:1?",
            reasoning="In this verse, the psalmist describes the LORD using the metaphor of a shepherd.",
            answer="Shepherd."
        )
    ]
    
    return examples

def test_model(model, examples):
    """Test the model on examples."""
    scores = []
    
    for example in examples:
        try:
            prediction = model(context=example.context, question=example.question)
            # Simple exact match scoring
            score = 1.0 if example.answer.lower() in prediction.answer.lower() else 0.0
            scores.append(score)
            
            print(f"\nQuestion: {example.question}")
            print(f"Predicted: {prediction.answer}")
            print(f"Expected: {example.answer}")
            print(f"Score: {score}")
        except Exception as e:
            logger.error(f"Error testing example: {e}")
            scores.append(0.0)
    
    accuracy = sum(scores) / len(scores) if scores else 0.0
    logger.info(f"Model accuracy: {accuracy:.4f}")
    return accuracy

def optimize_with_mlflow():
    """Run an optimization with MLflow tracking."""
    import dspy
    import mlflow
    
    # Create model and dataset
    model = create_bible_qa_model()
    dataset = create_sample_dataset()
    
    # Split dataset
    train_data = dataset[:2]
    test_data = dataset[2:]
    
    # Test model before optimization
    logger.info("Testing base model...")
    base_accuracy = test_model(model, test_data)
    
    # Start MLflow run
    with mlflow.start_run(run_name="test_dspy_bootstrap"):
        # Log parameters
        mlflow.log_params({
            "optimizer": "bootstrap_few_shot",
            "train_examples": len(train_data),
            "test_examples": len(test_data),
            "model_type": model.__class__.__name__
        })
        
        # Log base accuracy
        mlflow.log_metric("base_accuracy", base_accuracy)
        
        # Define metric
        class SimpleMetric:
            def __call__(self, example, prediction, trace=None):
                try:
                    if example.answer.lower() in prediction.answer.lower():
                        return 1.0
                    return 0.0
                except:
                    return 0.0
        
        # Create optimizer
        logger.info("Optimizing model...")
        optimizer = dspy.BootstrapFewShot(metric=SimpleMetric())
        
        # Track start time
        start_time = time.time()
        
        # Optimize model
        optimized_model = optimizer.compile(
            student=model,
            trainset=train_data
        )
        
        # Track end time
        end_time = time.time()
        
        # Test optimized model
        logger.info("Testing optimized model...")
        optimized_accuracy = test_model(optimized_model, test_data)
        
        # Log metrics
        mlflow.log_metrics({
            "optimized_accuracy": optimized_accuracy,
            "improvement": optimized_accuracy - base_accuracy,
            "optimization_time": end_time - start_time
        })
        
        # Log model
        logger.info("Logging model to MLflow...")
        model_info = mlflow.dspy.log_model(optimized_model, "model")
        
        # Print results
        logger.info(f"Base accuracy: {base_accuracy:.4f}")
        logger.info(f"Optimized accuracy: {optimized_accuracy:.4f}")
        logger.info(f"Improvement: {optimized_accuracy - base_accuracy:.4f}")
        logger.info(f"Model URI: {model_info.model_uri}")
        
        # Return the model info
        return {
            "base_accuracy": base_accuracy,
            "optimized_accuracy": optimized_accuracy,
            "model_uri": model_info.model_uri
        }

def test_loaded_model(model_uri):
    """Test a model loaded from MLflow."""
    import mlflow
    
    logger.info(f"Loading model from MLflow: {model_uri}")
    loaded_model = mlflow.dspy.load_model(model_uri)
    
    dataset = create_sample_dataset()
    logger.info("Testing loaded model...")
    accuracy = test_model(loaded_model, dataset)
    
    logger.info(f"Loaded model accuracy: {accuracy:.4f}")
    return accuracy

def main():
    """Main function."""
    args = parse_args()
    
    try:
        # Check dependencies
        if not check_dependencies():
            return 1
        
        # Load environment
        if not load_environment():
            return 1
        
        # Configure MLflow
        if not configure_mlflow(check_server=not args.no_mlflow_server):
            return 1
        
        # Configure DSPy
        if not configure_dspy():
            return 1
        
        # Optimize model with MLflow tracking
        logger.info("Starting optimization with MLflow tracking...")
        results = optimize_with_mlflow()
        
        # Test loaded model
        logger.info("Testing model loaded from MLflow...")
        test_loaded_model(results["model_uri"])
        
        logger.info("Test completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 