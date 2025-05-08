# Bible QA Optimization with DSPy 2.6

This document provides a guide for using DSPy 2.6 to optimize the Bible QA system.

## Overview

The Bible QA optimization system uses DSPy 2.6 to improve the accuracy of Bible question answering through iterative optimization. The system supports:

1. **Multiple Optimization Methods**:
   - **BetterTogether**: Learns which approach works best for different question types
   - **InferRules**: Learns explicit rules for specific theological questions
   - **Ensemble**: Combines both approaches for maximum accuracy

2. **MLflow Integration**:
   - Tracks optimization metrics (accuracy, iterations)
   - Visualizes progress over time
   - Maintains model versions

3. **Theological Focus**:
   - Enhanced understanding of Strong's IDs (H430, G3056, etc.)
   - Support for theological concepts and term definitions
   - Multi-turn conversation capabilities

## Setup

### Prerequisites

1. **Python Environment**:
   ```bash
   pip install "dspy-ai>=2.6.0" mlflow pandas matplotlib psycopg2-binary python-dotenv
   ```

2. **LM Studio**:
   - Download and install [LM Studio](https://lmstudio.ai/)
   - Load a suitable model (e.g., mistral-nemo-instruct-2407)
   - Enable the API server (port 1234)

3. **Environment Configuration**:
   - Copy `.env.example.dspy` to `.env.dspy`
   - Configure API endpoints and model names

### Verification

Before running the optimization, verify your setup with:

```
.\verify_dspy_model.bat
```

This script will:
- Check if LM Studio is running
- Test basic DSPy functionality
- Verify JSON compatibility

If you encounter errors, run the JSON format debug tool:

```
.\debug_dspy_json.bat
```

## Running the Optimization

### Basic Usage

To run the complete optimization workflow:

```
.\run_complete_optimization.bat better_together 10 0.95
```

Parameters:
- `better_together`: Optimization method (options: `better_together`, `infer_rules`, `ensemble`)
- `10`: Maximum iterations 
- `0.95`: Target accuracy (0.0-1.0)

### Manual Execution

If you prefer to run each step manually:

1. **Verify your setup**:
   ```
   .\verify_dspy_model.bat
   ```

2. **Expand validation dataset**:
   ```
   python expand_validation_dataset.py --sample-theological
   ```

3. **Start MLflow tracking server**:
   ```powershell
   powershell -Command "mlflow ui --host 127.0.0.1 --port 5000"
   ```

4. **Run optimization**:
   ```
   python train_and_optimize_bible_qa.py --optimization-method better_together --max-iterations 10 --target-accuracy 0.95
   ```

5. **Analyze results**:
   ```
   python -m scripts.analyze_mlflow_results --experiment-name bible_qa_optimization
   ```

## BetterTogether Implementation Details

We've created a minimal working implementation of the BetterTogether optimizer with DSPy 2.6, addressing specific compatibility issues with LM Studio. For detailed documentation, see [README_DSPY_BETTER_TOGETHER.md](README_DSPY_BETTER_TOGETHER.md).

Key improvements include:

1. **JSON Parsing Patch**:
   - Handles string responses from LM Studio
   - Extracts structured data from unstructured text
   - Supports ChainOfThought format automatically

2. **Parameter Compatibility**:
   - Automatically removes unsupported parameters
   - Simplified API compatible with DSPy 2.6
   - Provides helpful error messages

3. **Simplified Testing**:
   - Minimalist test implementation in `test_optimized_bible_qa.py`
   - Batch file for easy execution
   - Proper MLflow server management

To run the minimalist BetterTogether example:

```
.\test_optimized_bible_qa.bat
```

## JSON Parsing Issues in DSPy 2.6

DSPy 2.6 has known JSON parsing issues when used with LM Studio. The following fixes are implemented in our scripts:

1. **Remove `response_format`**:
   ```python
   # INCORRECT - Will cause errors with LM Studio
   lm = dspy.LM(
       model_type="openai", 
       model="mistral-nemo-instruct-2407",
       api_base="http://localhost:1234/v1",
       api_key="dummy",
       config={
           "response_format": {"type": "json_object"},  # Causes errors
           "temperature": 0.1
       }
   )
   
   # CORRECT - Works with LM Studio
   lm = dspy.LM(
       model_type="openai", 
       model="mistral-nemo-instruct-2407",
       api_base="http://localhost:1234/v1",
       api_key="dummy",
       config={
           "temperature": 0.1,
           "max_tokens": 512
       }
   )
   ```

2. **Enable experimental features**:
   ```python
   # Required for BetterTogether, InferRules optimizers
   dspy.settings.experimental = True
   ```

3. **Remove `modules` parameter**:
   ```python
   # INCORRECT - Not supported in DSPy 2.6
   optimizer = dspy.BetterTogether(
       metric=metric,
       modules=[module1, module2]  # Causes errors
   )
   
   # CORRECT - Works with DSPy 2.6
   optimizer = dspy.BetterTogether(
       metric=metric
   )
   ```

4. **Batch size limitation**:
   ```python
   # Reduce batch size to prevent overwhelming LM Studio API
   train_subset_size = min(20, len(train_data))
   optimized_model = optimizer.compile(
       student=ensemble_student,
       trainset=train_data[:train_subset_size]
   )
   ```

## Optimization Methods

### BetterTogether

The BetterTogether optimizer learns which approach works best for different question types. It's particularly effective for datasets with diverse question formats.

```python
# Configure BetterTogether optimizer
optimizer = dspy.BetterTogether(
    metric=metric
)

# Run optimization
optimized_model = optimizer.compile(
    student=ensemble_student,
    trainset=train_data[:20]
    # Do NOT include additional parameters in DSPy 2.6
)
```

### InferRules

InferRules learns explicit rules to improve performance on specific patterns. It's excellent for theological questions with Strong's IDs.

```python
# Configure InferRules optimizer
optimizer = dspy.InferRules(
    module=theological_model,
    metric=metric,
    max_rules=5
)

# Run optimization
optimized_model = optimizer.compile(
    trainset=train_data[:20]
    # Do NOT include additional parameters in DSPy 2.6
)
```

### Ensemble

The Ensemble approach combines both BetterTogether and InferRules, selecting the best-performing model for each question type.

## MLflow Integration

The optimization process is tracked with MLflow. To view the results:

1. Start the MLflow server:
   ```powershell
   powershell -Command "mlflow ui --host 127.0.0.1 --port 5000"
   ```

2. Open your browser to [http://127.0.0.1:5000](http://127.0.0.1:5000)

3. View experiments under "bible_qa_optimization"

## Troubleshooting

### LM Studio API Issues

If you encounter errors connecting to LM Studio:

1. Make sure LM Studio is running
2. Confirm the API server is enabled (Settings > API Server)
3. Verify the correct model is loaded
4. Check your `.env.dspy` file for correct API URL

### JSON Parsing Errors

If you see errors like `Expected a JSON object but parsed a <class 'str'>`:

1. Run the debug tool: `.\debug_dspy_json.bat`
2. Ensure you've removed `response_format` from LM configuration
3. Make sure `dspy.settings.experimental = True` is set
4. Add the JSON patch: `import dspy_json_patch` after importing DSPy

### PowerShell MLflow Issues

If MLflow doesn't start from batch file:

1. Run MLflow directly in PowerShell:
   ```powershell
   powershell -Command "mlflow ui --host 127.0.0.1 --port 5000"
   ```

2. Verify port 5000 is not in use by another process

3. Check for permissions issues when writing to the MLflow directory

## Additional Resources

- [DSPy Documentation](https://dspy.ai/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [models/dspy/version_reference.md](models/dspy/version_reference.md) - DSPy version compatibility
- [models/dspy/bible_qa_optimized/bible_qa_optimization.md](models/dspy/bible_qa_optimized/bible_qa_optimization.md) - Optimization guide 