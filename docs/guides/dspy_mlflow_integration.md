# DSPy MLflow Integration Guide

This guide explains how to use MLflow for tracking DSPy model experiments in the BibleScholarProject.

## Overview

MLflow integration allows us to track training metrics, parameters, and model artifacts for DSPy models, making it easier to compare different approaches and configurations over time.

## Prerequisites

- MLflow installed (`pip install mlflow>=2.20`)
- A trained Bible QA model (see [DSPy Training Guide](dspy_training_guide.md))
- Environment variables configured in `.env.dspy`

## Starting the MLflow Server

Always start the MLflow server before running any training scripts:

```bash
# Start the MLflow UI server on port 5000
mlflow ui --port 5000
```

This will display a message like:
```
INFO:waitress:Serving on http://127.0.0.1:5000
```

The server will continue running in your terminal. Keep this terminal open while you run your training scripts in another terminal.

## Environment Configuration

Add these MLflow-specific settings to your `.env.dspy` file:

```bash
# MLflow configuration
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=dspy_bible_qa
```

The `MLFLOW_TRACKING_URI` can be:
- HTTP URL (`http://localhost:5000`) - Recommended for active development
- Local directory (`./mlruns`) - For offline work
- SQLite database (`sqlite:///mlflow.db`)
- Remote server (`http://mlflow-server:5000`)

## Direct Connection Configuration

For the most reliable connection to MLflow, set the tracking URI directly in your Python code:

```python
import mlflow

# Set the tracking URI to the running MLflow server
mlflow.set_tracking_uri("http://localhost:5000")
logger.info(f"Set MLflow tracking URI to: http://localhost:5000")

# Set the experiment name
mlflow.set_experiment("dspy_bible_qa")
logger.info(f"Set MLflow experiment to: dspy_bible_qa")
```

## Tracking Bible QA Model Training

When training a Bible QA model, use the `--track-with-mlflow` flag:

```bash
python train_dspy_bible_qa.py --lm-studio --model-format chat
```

Our scripts will automatically track:
- **Parameters**: Model name, optimizer, number of training examples, etc.
- **Metrics**: Accuracy, theological concept scores
- **Artifacts**: Model files and metadata

## Structure of MLflow Logging

Our MLflow integration follows this pattern:

```python
import mlflow

# Configure MLflow
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("dspy_bible_qa")

# Create a timestamp for the run name
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model_name = args.model.split("/")[-1] if "/" in args.model else args.model
run_name = f"bible_qa_{model_name}_{timestamp}"

# Start tracking run
with mlflow.start_run(run_name=run_name):
    # Log parameters
    mlflow.log_params({
        "model": args.model,
        "optimizer": args.optimizer,
        "num_train_examples": len(train_data),
        "temperature": args.temperature,
        "max_tokens": args.max_tokens
    })
    
    # Log metrics 
    mlflow.log_metrics({
        "accuracy": metrics["accuracy"],
        "theological_match_score": metrics.get("theological_match_score", 0.0)
    })
    
    # Log model artifacts
    mlflow.log_artifact(model_path)
```

## Viewing Experiment Results

After running training scripts with MLflow enabled, open http://localhost:5000 in your browser to view:

1. A list of all experiment runs organized by experiment name
2. Parameter comparisons across different runs
3. Metric trends and visualizations
4. Saved model artifacts and files

Click on any run to see detailed information including:
- Run parameters
- Metrics over time
- Model artifacts
- System information

## Using MLflow with LM Studio

Our system supports tracking MLflow metrics when using LM Studio for local model inference:

```bash
# Train with LM Studio integration and MLflow tracking
python train_dspy_bible_qa.py --lm-studio --model-format chat
```

This will automatically log:
- Which LM Studio model was used
- Inference API details
- Performance metrics

## Logging Custom Metrics

To track theological accuracy or other custom metrics:

```python
# Define a custom theological metric
def theological_match_score(pred_answer, expected_answer):
    """Measures accuracy of theological content."""
    # Calculate theological concept matches
    match_score = calculate_match_score(pred_answer, expected_answer)
    return match_score
    
# Log the metric during training
with mlflow.start_run():
    # Other logging...
    mlflow.log_metric("theological_match_score", theological_match_score)
```

## Native DSPy Integration with MLflow

For DSPy-specific tracking with MLflow:

```python
# Enable automatic DSPy tracing
mlflow.dspy.autolog()

# Log your model directly
with mlflow.start_run(run_name="optimized_bible_qa"):
    model_info = mlflow.dspy.log_model(
        optimized_module,
        artifact_path="model",
    )

# Load the model back from MLflow
loaded = mlflow.dspy.load_model(model_info.model_uri)
```

## Loading Models from MLflow

To load a model tracked in MLflow:

```python
import mlflow
import pickle

# Get the run ID from MLflow UI or API
run_id = "your_run_id_here"

# Load the model
client = mlflow.tracking.MlflowClient()
artifact_path = client.download_artifacts(run_id, "model.pkl", ".")
with open(artifact_path, "rb") as f:
    model = pickle.load(f)
```

## Best Practices

1. **Name runs consistently**: Include model type, size, timestamp
2. **Track all hyperparameters**: Document anything that might affect results
3. **Save information files**: Include readable descriptions with each model
4. **Tag important runs**: Use tags to highlight baseline or production models
5. **Compare multiple metrics**: Don't rely on a single performance measure

## Troubleshooting

- **Connection errors**: Make sure the MLflow server is running at the URI specified
- **"URI required" errors**: Ensure you've set `mlflow.set_tracking_uri()` before any other MLflow calls
- **Missing artifacts**: Check file paths and permissions
- **Artifact storage issues**: Ensure storage location has sufficient space
- **Run failures**: Check logs for error messages

## MLflow with Multiple DSPy Components

For projects using multiple DSPy components (QA, retrieval, etc.), create separate experiments:

```python
# For Bible QA models
mlflow.set_experiment("dspy_bible_qa")

# For retrieval models
mlflow.set_experiment("dspy_retrieval")

# For semantic search components
mlflow.set_experiment("dspy_semantic_search")
```

## Related Resources

- [DSPy Training Guide](dspy_training_guide.md)
- [DSPy Usage Documentation](../features/dspy_usage.md)
- [Official MLflow Documentation](https://mlflow.org/docs/latest/index.html) 
- [DSPy MLflow API Reference](https://docs.dspy.ai/docs/mlflow) 