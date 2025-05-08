#!/usr/bin/env python3
"""
MLflow DSPy Example

This script demonstrates how to use MLflow with DSPy and LM Studio for Bible QA.
It provides a minimal working example showing:
1. How to configure DSPy with LM Studio
2. How to track experiments with MLflow
3. How to save and load optimized models

Usage:
    python examples/mlflow_dspy_example.py
"""

import os
import sys
import logging
import mlflow
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/mlflow_dspy_example.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env.dspy
load_dotenv('.env.dspy')

# Import DSPy after loading environment variables
import dspy
dspy.settings.experimental = True
import dspy_json_patch  # Apply JSON patch for LM Studio compatibility

def configure_lm_studio():
    """Configure DSPy with LM Studio."""
    lm_studio_api = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
    model_name = os.getenv("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
    
    logger.info(f"Using LM Studio API: {lm_studio_api}")
    logger.info(f"Using model: {model_name}")
    
    # Configure DSPy with LM Studio
    lm = dspy.LM(
        model_type="openai",
        model=model_name,
        api_base=lm_studio_api,
        api_key="dummy",  # LM Studio doesn't need a real key
        config={
            # Do not use response_format with LM Studio
            "temperature": 0.1,
            "max_tokens": 512
        }
    )
    
    dspy.configure(lm=lm)
    logger.info("DSPy configured with LM Studio")

# Define a basic signature for Bible QA
class BibleQASignature(dspy.Signature):
    """Signature for Bible QA."""
    context = dspy.InputField(desc="Context from Bible passages")
    question = dspy.InputField(desc="Question about the Bible")
    answer = dspy.OutputField(desc="Answer to the question based on the context")

# Define a simple QA module
class SimpleBibleQA(dspy.Module):
    """Simple Bible QA module."""
    def __init__(self):
        super().__init__()
        self.qa = dspy.Predict(BibleQASignature)
    
    def forward(self, context, question):
        """Forward pass through the module."""
        return self.qa(context=context, question=question)

class BibleQAMetric:
    """Metric for evaluating Bible QA responses."""
    def __call__(self, example, prediction, trace=None):
        """Calculate score for a prediction."""
        if not hasattr(prediction, 'answer'):
            return 0.0
        
        expected = example.answer.lower().strip()
        predicted = prediction.answer.lower().strip()
        
        # Simple exact match scoring
        if predicted == expected:
            return 1.0
        
        # Partial match scoring
        if expected in predicted or predicted in expected:
            return 0.5
        
        return 0.0

def create_sample_dataset():
    """Create a simple dataset for optimization."""
    examples = [
        dspy.Example(
            context="Genesis 1:1: In the beginning God created the heaven and the earth.",
            question="What did God create according to Genesis 1:1?",
            answer="the heaven and the earth"
        ),
        dspy.Example(
            context="John 3:16: For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
            question="What does John 3:16 say about how to receive everlasting life?",
            answer="by believing in God's only begotten Son"
        ),
        dspy.Example(
            context="Psalm 23:1: The LORD is my shepherd; I shall not want.",
            question="What metaphor is used to describe the LORD in Psalm 23:1?",
            answer="shepherd"
        ),
        dspy.Example(
            context="Matthew 5:44: But I say unto you, Love your enemies, bless them that curse you, do good to them that hate you, and pray for them which despitefully use you, and persecute you;",
            question="What does Jesus command regarding enemies in Matthew 5:44?",
            answer="Love your enemies, bless them that curse you, do good to them that hate you, and pray for them which despitefully use you"
        ),
        dspy.Example(
            context="Romans 3:23: For all have sinned, and come short of the glory of God;",
            question="According to Romans 3:23, what is the condition of humanity?",
            answer="all have sinned and come short of the glory of God"
        )
    ]
    
    return examples

def optimize_with_mlflow():
    """Optimize a model and track with MLflow."""
    # Set up MLflow experiment
    mlflow.set_experiment("bible_qa_example")
    
    # Get or create model
    model = SimpleBibleQA()
    
    # Create dataset
    dataset = create_sample_dataset()
    train_data = dataset[:3]
    val_data = dataset[3:]
    
    # Test model before optimization
    metric = BibleQAMetric()
    base_scores = []
    
    logger.info("Testing base model...")
    for example in val_data:
        pred = model(context=example.context, question=example.question)
        score = metric(example, pred)
        base_scores.append(score)
    
    base_accuracy = sum(base_scores) / len(base_scores)
    logger.info(f"Base accuracy: {base_accuracy:.4f}")
    
    # Start MLflow run
    with mlflow.start_run(run_name="bootstrap_example"):
        # Log parameters
        mlflow.log_params({
            "optimizer": "bootstrap_few_shot",
            "max_bootstrapped_demos": 3, 
            "trainset_size": len(train_data),
            "valset_size": len(val_data)
        })
        
        # Log base accuracy
        mlflow.log_metric("base_accuracy", base_accuracy)
        
        # Optimize model
        logger.info("Optimizing model with BootstrapFewShot...")
        optimizer = dspy.BootstrapFewShot(metric=metric, max_labeled_demos=2)
        
        optimized_model = optimizer.compile(
            student=model,
            trainset=train_data
        )
        
        # Test optimized model
        optimized_scores = []
        logger.info("Testing optimized model...")
        
        for example in val_data:
            pred = optimized_model(context=example.context, question=example.question)
            score = metric(example, pred)
            optimized_scores.append(score)
        
        optimized_accuracy = sum(optimized_scores) / len(optimized_scores)
        improvement = optimized_accuracy - base_accuracy
        
        # Log metrics
        mlflow.log_metrics({
            "optimized_accuracy": optimized_accuracy,
            "improvement": improvement
        })
        
        # Log model with MLflow
        logger.info("Saving model to MLflow...")
        model_info = mlflow.dspy.log_model(
            optimized_model,
            artifact_path="model"
        )
        
        # Return relevant information
        return {
            "base_accuracy": base_accuracy,
            "optimized_accuracy": optimized_accuracy,
            "improvement": improvement,
            "model_uri": model_info.model_uri
        }

def test_loaded_model(model_uri, examples):
    """Test a model loaded from MLflow."""
    # Load model from MLflow
    logger.info(f"Loading model from: {model_uri}")
    loaded_model = mlflow.dspy.load_model(model_uri)
    
    # Test model
    metric = BibleQAMetric()
    scores = []
    
    logger.info("Testing loaded model...")
    for example in examples:
        pred = loaded_model(context=example.context, question=example.question)
        score = metric(example, pred)
        scores.append(score)
        
        print(f"\nQuestion: {example.question}")
        print(f"Context: {example.context}")
        print(f"Expected: {example.answer}")
        print(f"Predicted: {pred.answer}")
        print(f"Score: {score}")
    
    accuracy = sum(scores) / len(scores)
    print(f"\nLoaded model accuracy: {accuracy:.4f}")
    
    return accuracy

def main():
    """Main function."""
    try:
        # Configure DSPy with LM Studio
        configure_lm_studio()
        
        # Check if MLflow server is running
        try:
            mlflow.set_tracking_uri("http://localhost:5000")
            mlflow.search_experiments()
            logger.info("Connected to MLflow server at http://localhost:5000")
        except Exception as e:
            logger.warning(f"Could not connect to MLflow server: {e}")
            logger.warning("Start MLflow server with 'mlflow ui --port 5000' in another terminal")
            
            # Fallback to local tracking
            logger.info("Using local MLflow tracking (./mlruns)")
            mlflow.set_tracking_uri("")

        # Enable MLflow DSPy autologging
        mlflow.dspy.autolog()
        
        # Run optimization
        logger.info("Starting optimization with MLflow tracking...")
        results = optimize_with_mlflow()
        
        # Display results
        print("\n===== Optimization Results =====")
        print(f"Base accuracy: {results['base_accuracy']:.4f}")
        print(f"Optimized accuracy: {results['optimized_accuracy']:.4f}")
        print(f"Improvement: {results['improvement']:.4f}")
        print(f"Model URI: {results['model_uri']}")
        
        # Test loaded model
        print("\n===== Testing Loaded Model =====")
        test_dataset = create_sample_dataset()
        loaded_accuracy = test_loaded_model(results['model_uri'], test_dataset)
        
        return 0
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 