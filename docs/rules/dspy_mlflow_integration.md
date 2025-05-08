# DSPy and MLflow Integration

This guide documents the integration of DSPy with MLflow for experiment tracking and model management in the BibleScholarProject.

## Overview

MLflow integration enables:

1. **Experiment Tracking**: Recording DSPy optimizer runs, metrics, and parameters
2. **Model Versioning**: Capturing different model versions with metadata
3. **Visualization**: Analyzing optimization results with visualizations
4. **Model Registry**: Managing and deploying optimized models

## Configuration

### Environment Setup

Set up the environment by creating a `.env.dspy` file with the required variables:

```bash
# LM Studio Configuration
LM_STUDIO_API_URL=http://localhost:1234/v1
LM_STUDIO_CHAT_MODEL=mistral-nemo-instruct-2407
LM_STUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0

# MLflow Configuration 
MLFLOW_TRACKING_URI=http://localhost:5000
```

### MLflow Server

Start the MLflow server:

```bash
# Start MLflow UI server on default port 5000
mlflow ui --port 5000
```

## Usage

### Basic Integration

```python
import mlflow
import dspy

# Configure MLflow
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("bible_qa_optimization")

# Enable MLflow autologging for DSPy
mlflow.dspy.autolog()

# Start a run
with mlflow.start_run(run_name="bible_qa_run"):
    # Log parameters
    mlflow.log_params({
        "optimizer": "BootstrapFewShot",
        "max_train": 10
    })
    
    # Train your model
    model = BibleQAModule()
    optimizer = dspy.BootstrapFewShot(metric=your_metric)
    optimized_model = optimizer.compile(student=model, trainset=train_data)
    
    # Log metrics
    mlflow.log_metrics({
        "accuracy": 0.85,
        "improvement": 0.15
    })
    
    # Log model
    mlflow.dspy.log_model(optimized_model, "model")
```

### Loading Models

```python
# Load a model from MLflow
loaded_model = mlflow.dspy.load_model("runs:/run_id/model")

# Use the loaded model
prediction = loaded_model(context="...", question="...")
```

## Optimization Scripts

The project includes several scripts for MLflow integration:

1. **`train_and_optimize_bible_qa.py`**: Main script for training and optimization
2. **`analyze_mlflow_results.py`**: Analyze and visualize experiment results
3. **`test_mlflow_connection.py`**: Test MLflow server connection
4. **`run_dspy_mlflow_optimization.bat`**: Batch script for Windows

### Command Line Arguments

#### Training and Optimization

```bash
python train_and_optimize_bible_qa.py --max-train 10 --max-val 5 --use-bootstrap --mlflow-experiment-name "bible_qa_test"
```

Options:
- `--max-train`: Maximum training examples
- `--max-val`: Maximum validation examples
- `--use-bootstrap`: Use BootstrapFewShot optimizer (recommended for LM Studio)
- `--use-better-together`: Use BetterTogether optimizer
- `--mlflow-experiment-name`: MLflow experiment name
- `--no-mlflow-server`: Skip MLflow server check, use local tracking
- `--test`: Test the model after optimization

#### Result Analysis

```bash
python analyze_mlflow_results.py --experiment "bible_qa_optimization" --visualize
```

Options:
- `--experiment`: Experiment name to analyze
- `--limit`: Maximum number of runs to analyze
- `--visualize`: Generate all visualization plots
- `--compare-optimizers`: Generate optimizer comparison plot
- `--show-trends`: Generate performance trends plot
- `--analyze-params`: Parameters to analyze impact (comma-separated)

## Visualization

The `analyze_mlflow_results.py` script generates several visualizations:

1. **Optimizer Comparison**: Bar chart comparing different optimization approaches
2. **Performance Trends**: Line chart showing accuracy improvements over time
3. **Parameter Impact**: Analysis of how parameters affect model performance

## Best Practices

1. **Environment Variables**: Always use environment variables from `.env.dspy` for configuration
2. **Error Handling**: Include proper error handling for MLflow server connection issues
3. **Tracking URI**: Set tracking URI explicitly to ensure consistency
4. **Experiment Names**: Use descriptive experiment names
5. **Run Names**: Include timestamps in run names for easier identification
6. **Parameter Logging**: Log all relevant parameters at the start of the run
7. **Metric Logging**: Log both base and optimized metrics for comparison
8. **Artifact Paths**: Use consistent artifact paths when saving models

## Troubleshooting

1. **Connection Issues**
   - Ensure MLflow server is running at the specified port
   - Check network connectivity if using a remote server
   - Verify no firewall is blocking the connection

2. **Model Loading Issues**
   - Ensure DSPy version is compatible with the saved model
   - Check if all required dependencies are installed

3. **Visualization Issues**
   - Install required packages: `pip install matplotlib pandas seaborn`
   - Check if output directory has proper write permissions

## Example Workflows

### Basic Workflow

1. Start MLflow server: `mlflow ui --port 5000`
2. Run optimization: `python train_and_optimize_bible_qa.py --use-bootstrap`
3. Analyze results: `python analyze_mlflow_results.py --visualize`

### Using the Batch Script

```bash
run_dspy_mlflow_optimization.bat --max-train 10 --visualize
```

### Comparing Optimizers

```bash
# Run with BootstrapFewShot
python train_and_optimize_bible_qa.py --use-bootstrap --mlflow-experiment-name "optimizer_comparison"

# Run with BetterTogether
python train_and_optimize_bible_qa.py --use-better-together --mlflow-experiment-name "optimizer_comparison"

# Analyze results
python analyze_mlflow_results.py --experiment "optimizer_comparison" --compare-optimizers
```

## Additional Resources

- [MLflow Documentation](https://www.mlflow.org/docs/latest/index.html)
- [DSPy Documentation](https://dspy.ai/)
- [LM Studio Documentation](https://lmstudio.ai/docs/basics) 