# MLflow Integration with DSPy

This document explains the MLflow integration with DSPy components in the BibleScholarProject, focusing on practical implementation.

## Overview

MLflow provides experiment tracking, model versioning, and run comparison tools that are essential for managing DSPy model development. Our project uses MLflow to track:

- Training parameters
- Performance metrics
- Theological accuracy scores
- Model artifacts

## Quick Start Guide

1. **Start the MLflow server**:
   ```bash
   mlflow ui --port 5000
   ```

2. **Configure your training script**:
   ```python
   import mlflow
   from datetime import datetime
   
   # Direct server connection (preferred)
   mlflow.set_tracking_uri("http://localhost:5000")
   mlflow.set_experiment("dspy_bible_qa")
   
   # Create a unique run name
   timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
   run_name = f"bible_qa_model_{timestamp}"
   
   # Start MLflow run
   with mlflow.start_run(run_name=run_name):
       # Log parameters
       mlflow.log_params({
           "model": "mistral-nemo-instruct-2407",
           "optimizer": "bootstrap",
           "num_examples": 150
       })
       
       # Train your model...
       
       # Log metrics
       mlflow.log_metrics({
           "accuracy": 0.85,
           "theological_match_score": 0.76
       })
       
       # Log model artifacts
       mlflow.log_artifact("models/bible_qa/model.pkl")
   ```

3. **Run the training script**:
   ```bash
   python train_dspy_bible_qa.py --lm-studio
   ```

4. **View results** at http://localhost:5000

## LM Studio Integration

When using LM Studio for local inference in DSPy, log these additional parameters:

```python
mlflow.log_params({
    "lm_studio": True,
    "lm_studio_model": "mistral-nemo-instruct-2407@q4_k_m",
    "lm_studio_api_url": "http://localhost:1234/v1",
    "model_format": "chat"
})
```

## Specialized DSPy Tracking

DSPy has native MLflow tracking capabilities:

```python
# Enable automatic DSPy tracing
mlflow.dspy.autolog()

# Train your model
optimized_module = optimizer.optimize(program, trainset=train_examples)

# Log the model directly
with mlflow.start_run(run_name="optimized_bible_qa"):
    model_info = mlflow.dspy.log_model(
        optimized_module,
        artifact_path="model"
    )

# You can later load the model back
loaded_module = mlflow.dspy.load_model(model_info.model_uri)
```

## Key Metrics to Track

For Bible QA models, we track:

| Metric | Description | Target |
|--------|-------------|--------|
| `accuracy` | Overall answer correctness | > 0.80 |
| `theological_match_score` | Theological concept match | > 0.70 |
| `key_term_accuracy` | Accuracy on theological terms | > 0.85 |
| `cross_reference_recall` | Ability to find related passages | > 0.65 |

## Tracking Theological Performance

Our custom theological metrics can be tracked in MLflow:

```python
def evaluate_theological_precision(model, test_data):
    """Calculate theological concept precision."""
    # Implementation details
    precision_score = calculate_precision()
    
    # Log the metric
    mlflow.log_metric("theological_precision", precision_score)
    
    # You can also log metrics during the training process
    for epoch in range(num_epochs):
        epoch_score = train_epoch(model, data)
        mlflow.log_metric("epoch_accuracy", epoch_score, step=epoch)
```

## Comparing Different Models

To programmatically compare model runs:

```python
from mlflow.tracking import MlflowClient

# Initialize client
client = MlflowClient()

# Get experiment by name
experiment = client.get_experiment_by_name("dspy_bible_qa")

# Get runs for the experiment
runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    filter_string="metrics.accuracy > 0.8"
)

# Compare runs
for run in runs:
    run_id = run.info.run_id
    metrics = run.data.metrics
    params = run.data.params
    
    print(f"Run ID: {run_id}")
    print(f"Accuracy: {metrics.get('accuracy')}")
    print(f"Model: {params.get('model')}")
    print("---")
```

## Best Practices

1. **Always start the MLflow server first**
   ```bash
   mlflow ui --port 5000
   ```

2. **Use direct URI configuration** rather than environment variables
   ```python
   mlflow.set_tracking_uri("http://localhost:5000")
   ```

3. **Create descriptive run names** that include:
   - Model type/name
   - Timestamp
   - Key configuration parameter

4. **Log all parameters** that could affect results:
   ```python
   mlflow.log_params({
       "model": model_name,
       "optimizer": optimizer_type,
       "learning_rate": learning_rate,
       "batch_size": batch_size,
       "max_epochs": max_epochs,
       "train_size": len(train_data),
       "val_size": len(val_data)
   })
   ```

5. **Track multiple metrics** for comprehensive evaluation

6. **Log sample predictions** for qualitative analysis:
   ```python
   # Log sample predictions
   sample_results = {
       "questions": questions[:5],
       "predictions": predictions[:5],
       "ground_truth": ground_truth[:5]
   }
   
   with open("sample_predictions.json", "w") as f:
       json.dump(sample_results, f, indent=2)
       
   mlflow.log_artifact("sample_predictions.json")
   ```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "URI required" error | Set `mlflow.set_tracking_uri()` before any other MLflow operations |
| Missing runs | Make sure you're viewing the correct experiment |
| Connection errors | Verify MLflow server is running at the correct URL |
| Duplicate runs | Use unique run names with timestamps |

## Related Resources

- [Project MLflow Integration Guide](../guides/dspy_mlflow_integration.md)
- [DSPy Training Guide](../guides/dspy_training_guide.md)
- [Official MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [DSPy MLflow API Reference](https://docs.dspy.ai/docs/mlflow) 