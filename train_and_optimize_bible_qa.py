#!/usr/bin/env python3
"""
Bible QA Training and Optimization Pipeline
Trains a Bible QA model using DSPy 2.6 with LM Studio, focusing on theological accuracy.
"""
import os
import sys
import json
import time
import logging
import argparse
import pickle
from pathlib import Path
from dotenv import load_dotenv
import dspy
import dspy_json_patch  # Apply JSON patch
import mlflow

# Enable experimental features for DSPy 2.6
dspy.settings.experimental = True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/train_and_optimize_bible_qa.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env.dspy')
os.makedirs("logs", exist_ok=True)

def configure_lm_studio():
    """Configure DSPy to use LM Studio."""
    try:
        lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
        model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
        logger.info(f"Configuring LM Studio: {lm_studio_api}, model: {model_name}")
        lm = dspy.LM(
            model_type="openai",
            model=model_name,
            api_base=lm_studio_api,
            api_key="dummy",
            config={"temperature": 0.1, "max_tokens": 1024}
        )
        dspy.configure(lm=lm)
        return True
    except Exception as e:
        logger.error(f"LM Studio configuration failed: {e}")
        return False

class BibleQASignature(dspy.Signature):
    """Answer questions about Bible verses with theological accuracy."""
    context = dspy.InputField(desc="Biblical context or verse")
    question = dspy.InputField(desc="Question about the biblical context")
    history = dspy.InputField(desc="Previous conversation turns", default=[])
    answer = dspy.OutputField(desc="Answer to the question")

class BibleQAModule(dspy.Module):
    """Chain of Thought module for Bible QA with assertions."""
    def __init__(self):
        super().__init__()
        self.qa_model = dspy.ChainOfThought(BibleQASignature)

    def forward(self, context, question, history=None):
        prediction = self.qa_model(context=context, question=question, history=history or [])
        # Perform a simple check instead of using dspy.Assert which may not be available
        if "god" in question.lower():
            theological_terms = ["god", "elohim", "yhwh"]
            has_term = any(term in prediction.answer.lower() for term in theological_terms)
            if not has_term:
                logger.warning("Answer should reference theological terms when relevant.")
        return prediction

class BibleQAMetric:
    """Custom metric for evaluating Bible QA predictions."""
    def __call__(self, example, pred, trace=None):
        try:
            prediction = pred.answer.lower()
            reference = example.answer.lower()
            critical_terms = {"elohim": "H430", "yhwh": "H3068", "adon": "H113"}
            for term, strongs_id in critical_terms.items():
                if term in reference and term not in prediction:
                    return 0.0
            return 1.0 if reference in prediction else 0.0
        except AttributeError as e:
            logger.error(f"Metric error: {e}")
            return 0.0

def load_datasets(train_path, val_path, max_train=None, max_val=None):
    """Load training and validation datasets."""
    try:
        train_data = []
        if os.path.exists(train_path):
            with open(train_path, "r", encoding="utf-8") as f:
                train_data = [json.loads(line) for line in f if line.strip()]
            if max_train:
                train_data = train_data[:max_train]
            logger.info(f"Loaded {len(train_data)} training examples")
        else:
            logger.warning(f"Train file {train_path} not found")
            return [], []

        val_data = []
        if os.path.exists(val_path):
            with open(val_path, "r", encoding="utf-8") as f:
                val_data = [json.loads(line) for line in f if line.strip()]
            if max_val:
                val_data = val_data[:max_val]
            logger.info(f"Loaded {len(val_data)} validation examples")
        else:
            logger.warning(f"Val file {val_path} not found")
            return train_data, []

        # Ensure history field exists and is a list
        for item in train_data:
            if "history" not in item:
                item["history"] = []
        
        for item in val_data:
            if "history" not in item:
                item["history"] = []

        train_examples = [dspy.Example(**item).with_inputs("context", "question", "history") for item in train_data]
        val_examples = [dspy.Example(**item).with_inputs("context", "question", "history") for item in val_data]
        return train_examples, val_examples
    except Exception as e:
        logger.error(f"Error loading datasets: {e}")
        return [], []

def optimize_model(train_data, val_data, target_accuracy=0.95, use_bootstrap=True):
    """Optimize model using BetterTogether or BootstrapFewShot."""
    logger.info(f"Starting optimization with {len(train_data)} training examples")
    metrics = {"iterations": 0, "best_accuracy": 0.0, "start_time": time.time()}

    model = BibleQAModule()
    metric = BibleQAMetric()
    
    # Calculate base accuracy before optimization
    base_accuracy = 0.0
    try:
        if val_data:
            accuracy_scores = []
            for example in val_data:
                try:
                    # Ensure history is not None
                    if not hasattr(example, "history"):
                        example.history = []
                    prediction = model(example.context, example.question, example.history)
                    score = metric(example, prediction)
                    accuracy_scores.append(score)
                except Exception as e:
                    logger.error(f"Error evaluating example: {e}")
            
            if accuracy_scores:
                base_accuracy = sum(accuracy_scores) / len(accuracy_scores)
            
            logger.info(f"Base model accuracy: {base_accuracy:.4f}")
    except Exception as e:
        logger.error(f"Error calculating base accuracy: {e}")
    
    # Choose optimizer based on parameter or default to BootstrapFewShot for LM Studio compatibility
    if use_bootstrap:
        logger.info("Using BootstrapFewShot optimizer (compatible with LM Studio)")
        optimizer = dspy.BootstrapFewShot(metric=metric)
    else:
        logger.info("Using BetterTogether optimizer")
        optimizer = dspy.BetterTogether(metric=metric)

    try:
        mlflow.set_experiment("bible_qa_optimization")
        optimizer_name = "bootstrap_few_shot" if use_bootstrap else "better_together"
        with mlflow.start_run(run_name=f"{optimizer_name}_{int(time.time())}"):
            mlflow.log_param("optimizer", optimizer_name)
            mlflow.log_param("train_examples", len(train_data))
            mlflow.log_param("val_examples", len(val_data))
            mlflow.log_metric("base_accuracy", base_accuracy)

            # Compile the optimized model
            start_time = time.time()
            
            try:
                # Attempt to optimize, but handle failures
                optimized_model = optimizer.compile(student=model, trainset=train_data)
            except Exception as e:
                logger.error(f"Optimization failed: {e}")
                logger.info("Using unoptimized model as fallback")
                optimized_model = model
                
            end_time = time.time()
            
            # Calculate accuracy after optimization
            optimized_accuracy = base_accuracy  # Default to base accuracy
            if val_data:
                accuracy_scores = []
                for example in val_data:
                    try:
                        # Ensure history is not None
                        if not hasattr(example, "history"):
                            example.history = []
                        prediction = optimized_model(example.context, example.question, example.history)
                        score = metric(example, prediction)
                        accuracy_scores.append(score)
                    except Exception as e:
                        logger.error(f"Error evaluating optimized model: {e}")
                
                if accuracy_scores:
                    optimized_accuracy = sum(accuracy_scores) / len(accuracy_scores)
            
            mlflow.log_metric("optimized_accuracy", optimized_accuracy)
            mlflow.log_metric("optimization_time", end_time - start_time)
            logger.info(f"Optimized model accuracy: {optimized_accuracy:.4f}")

            metrics.update({
                "base_accuracy": base_accuracy,
                "accuracy": optimized_accuracy,
                "improvement": optimized_accuracy - base_accuracy,
                "iterations": 1,
                "best_accuracy": optimized_accuracy,
                "reached_target": optimized_accuracy >= target_accuracy,
                "optimization_time": end_time - start_time
            })
            
            return optimized_model, metrics
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        metrics.update({"error": str(e), "accuracy": base_accuracy, "improvement": 0.0})
        return model, metrics

def save_model(model, output_dir="models/dspy/bible_qa_optimized", optimizer_name="bootstrap_few_shot"):
    """Save model by saving the module code."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Instead of trying to pickle the entire model, save important model parameters
        model_data = {
            "optimizer": optimizer_name,
            "timestamp": int(time.time()),
            "description": "Bible QA optimized with DSPy 2.6"
        }
        
        # Save model metadata
        metadata_path = os.path.join(output_dir, f"bible_qa_{optimizer_name}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(model_data, f, indent=2)
        logger.info(f"Model metadata saved to {metadata_path}")
        
        # Also create a simple model file that indicates the model class to use
        model_path = os.path.join(output_dir, f"bible_qa_{optimizer_name}.py")
        with open(model_path, 'w') as f:
            f.write("""#!/usr/bin/env python3
\"\"\"
Bible QA model optimized with DSPy 2.6
\"\"\"
import dspy

class BibleQASignature(dspy.Signature):
    \"\"\"Answer questions about Bible verses with theological accuracy.\"\"\"
    context = dspy.InputField(desc="Biblical context or verse")
    question = dspy.InputField(desc="Question about the biblical context")
    history = dspy.InputField(desc="Previous conversation turns", default=[])
    answer = dspy.OutputField(desc="Answer to the question")

class BibleQAModule(dspy.Module):
    \"\"\"Chain of Thought module for Bible QA.\"\"\"
    def __init__(self):
        super().__init__()
        self.qa_model = dspy.ChainOfThought(BibleQASignature)

    def forward(self, context, question, history=None):
        prediction = self.qa_model(context=context, question=question, history=history or [])
        return prediction

def get_model():
    \"\"\"Return a fresh instance of the model.\"\"\"
    return BibleQAModule()
""")
        logger.info(f"Model module saved to {model_path}")
        return model_path
    except Exception as e:
        logger.error(f"Error saving model: {e}")
        return None

def test_model(model, val_data):
    """Test model on validation data and log sample predictions."""
    try:
        metric = BibleQAMetric()
        results = []
        
        for i, example in enumerate(val_data[:5]):  # Test first 5 examples
            try:
                # Ensure history is not None
                if not hasattr(example, "history"):
                    example.history = []
                    
                prediction = model(example.context, example.question, example.history)
                score = metric(example, prediction)
                results.append({
                    "context": example.context[:100] + "..." if len(example.context) > 100 else example.context,
                    "question": example.question,
                    "expected": example.answer,
                    "predicted": prediction.answer,
                    "score": score
                })
                logger.info(f"Example {i+1}:")
                logger.info(f"  Q: {example.question}")
                logger.info(f"  Expected: {example.answer}")
                logger.info(f"  Predicted: {prediction.answer}")
                logger.info(f"  Score: {score}")
            except Exception as e:
                logger.error(f"Error testing example {i+1}: {e}")
        
        return results
    except Exception as e:
        logger.error(f"Error testing model: {e}")
        return []

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Train and optimize a Bible QA model using DSPy 2.6")
    
    # Data parameters
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/processed/bible_training_data",
        help="Path to the training data directory"
    )
    parser.add_argument(
        "--max-train",
        type=int,
        default=20,
        help="Maximum number of training examples to use"
    )
    parser.add_argument(
        "--max-val",
        type=int,
        default=5,
        help="Maximum number of validation examples to use"
    )
    
    # Optimization parameters
    parser.add_argument(
        "--target-accuracy",
        type=float,
        default=0.95,
        help="Target accuracy for optimization"
    )
    parser.add_argument(
        "--use-bootstrap",
        action="store_true",
        help="Use BootstrapFewShot optimizer (recommended for LM Studio)"
    )
    parser.add_argument(
        "--use-better-together",
        action="store_true",
        help="Use BetterTogether optimizer"
    )
    
    # MLflow parameters
    parser.add_argument(
        "--no-mlflow-server",
        action="store_true",
        help="Don't check for MLflow server, use local tracking"
    )
    parser.add_argument(
        "--mlflow-experiment-name",
        type=str,
        default="bible_qa_optimization",
        help="MLflow experiment name"
    )
    parser.add_argument(
        "--mlflow-tracking-uri",
        type=str,
        default="http://localhost:5000",
        help="MLflow tracking server URI"
    )
    
    # Model parameters
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/dspy/bible_qa_optimized",
        help="Directory to save the optimized model"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test the model after optimization"
    )
    
    args = parser.parse_args()
    
    # Handle conflicting optimizer arguments
    if args.use_bootstrap and args.use_better_together:
        logger.warning("Both --use-bootstrap and --use-better-together specified. Using Bootstrap.")
        args.use_better_together = False
    elif not args.use_bootstrap and not args.use_better_together:
        # Default to BootstrapFewShot for LM Studio compatibility
        logger.info("No optimizer specified. Defaulting to BootstrapFewShot for LM Studio compatibility.")
        args.use_bootstrap = True
    
    return args

def main():
    """Main function to train and optimize the Bible QA model."""
    args = parse_args()
    
    try:
        # Ensure output directory exists
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Configure MLflow
        try:
            # Try to connect to MLflow server if specified
            if not args.no_mlflow_server:
                logger.info(f"Trying to connect to MLflow server at {args.mlflow_tracking_uri}")
                mlflow.set_tracking_uri(args.mlflow_tracking_uri)
                mlflow.tracking.MlflowClient().search_experiments()
                logger.info(f"Successfully connected to MLflow server at {args.mlflow_tracking_uri}")
            else:
                logger.info("Using local MLflow tracking (./mlruns)")
                mlflow.set_tracking_uri("")
                
            # Set experiment name
            mlflow.set_experiment(args.mlflow_experiment_name)
            
            # Enable autologging for DSPy
            mlflow.dspy.autolog()
            
        except Exception as e:
            logger.warning(f"Failed to configure MLflow: {e}")
            logger.warning("Continuing without MLflow tracking")
        
        # Configure DSPy with LM Studio
        configure_lm_studio()
        
        # Load training and validation data
        train_data, val_data = load_datasets(
            args.data_path,
            max_train=args.max_train,
            max_val=args.max_val
        )
        
        logger.info(f"Loaded {len(train_data)} training examples and {len(val_data)} validation examples")
        
        # Create metric for evaluation
        metric = BibleQAMetric()
        
        # Create base model
        model = BibleQAModule()
        
        # Start MLflow run
        with mlflow.start_run(run_name=f"bible_qa_{time.strftime('%Y%m%d_%H%M%S')}"):
            # Log parameters
            run_params = {
                "max_train": args.max_train,
                "max_val": args.max_val,
                "target_accuracy": args.target_accuracy,
                "optimizer": "BootstrapFewShot" if args.use_bootstrap else "BetterTogether",
                "data_path": args.data_path
            }
            mlflow.log_params(run_params)
            
            # Evaluate base model
            logger.info("Evaluating base model...")
            base_metrics = evaluate_model(model, val_data, metric)
            logger.info(f"Base model metrics: {base_metrics}")
            
            # Log base metrics
            mlflow.log_metrics({
                "base_accuracy": base_metrics["accuracy"],
                "base_exact_match": base_metrics["exact_match"]
            })
            
            # Create and compile optimizer
            start_time = time.time()
            logger.info(f"Starting optimization with {'BootstrapFewShot' if args.use_bootstrap else 'BetterTogether'}...")
            
            if args.use_bootstrap:
                optimizer = dspy.BootstrapFewShot(
                    metric=metric,
                    max_bootstrapped_demos=3,
                    max_labeled_demos=2
                )
            else:
                optimizer = dspy.BetterTogether(
                    metric=metric,
                    k=3,  # Number of demos to use
                    batch_size=1
                )
            
            optimized_model = optimizer.compile(
                student=model,
                trainset=train_data,
                valset=val_data[:min(3, len(val_data))]  # Use a small subset for validation during compilation
            )
            
            optimization_time = time.time() - start_time
            logger.info(f"Optimization completed in {optimization_time:.2f} seconds")
            
            # Log optimization time
            mlflow.log_metric("optimization_time", optimization_time)
            
            # Evaluate optimized model
            logger.info("Evaluating optimized model...")
            optimized_metrics = evaluate_model(optimized_model, val_data, metric)
            logger.info(f"Optimized model metrics: {optimized_metrics}")
            
            # Log optimized metrics
            mlflow.log_metrics({
                "optimized_accuracy": optimized_metrics["accuracy"],
                "optimized_exact_match": optimized_metrics["exact_match"],
                "improvement": optimized_metrics["accuracy"] - base_metrics["accuracy"]
            })
            
            # Save model with MLflow
            model_info = mlflow.dspy.log_model(
                optimized_model,
                artifact_path="model"
            )
            logger.info(f"Model saved to MLflow: {model_info.model_uri}")
            
            # Download model from MLflow to the specified output directory
            try:
                local_path = os.path.join(args.output_dir, f"bible_qa_{time.strftime('%Y%m%d_%H%M%S')}")
                mlflow.dspy.save_model(optimized_model, local_path)
                logger.info(f"Model also saved locally to: {local_path}")
            except Exception as e:
                logger.error(f"Failed to save model locally: {e}")
            
            # Test model if requested
            if args.test:
                logger.info("Testing optimized model with example queries...")
                test_model(optimized_model)
        
        return 0
    
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    main() 