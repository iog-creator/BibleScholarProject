# Bible QA Optimization Guide

This guide explains the changes made to the Bible QA system to fix JSON parsing issues and optimize performance with DSPy 2.6.

## Summary of Changes

1. **Fixed JSON Parsing Errors**
   - Removed `response_format` parameter from LM configuration
   - Enabled experimental features for DSPy 2.6 with `dspy.settings.experimental = True`
   - Removed `modules` parameter from BetterTogether optimizer
   - Reduced batch size and threads to prevent overwhelming the API

2. **Enhanced Validation Dataset**
   - Added support for theological questions with Strong's IDs (H430, G3056, etc.)
   - Created sample terms for testing when none are available
   - Implemented multi-turn conversation examples

3. **Improved MLflow Integration**
   - Fixed PowerShell compatibility issues
   - Enhanced tracking of optimization metrics
   - Added proper error handling and logging

4. **Created Comprehensive Documentation**
   - Added version reference guide (`version_reference.md`)
   - Created optimization documentation (`bible_qa_optimization.md`)
   - Added troubleshooting information for common issues

## Key Files Modified

1. **`scripts/verify_dspy_model.py`**: Verification script to test LM Studio API
2. **`verify_dspy_model.bat`**: PowerShell-compatible batch file for verification
3. **`expand_validation_dataset.py`**: Dataset expansion with theological terms
4. **`run_complete_optimization.bat`**: Complete workflow with proper MLflow integration
5. **`train_and_optimize_bible_qa.py`**: Core optimization script with JSON error fixes

## Running the Optimization Pipeline

Follow these steps to run the Bible QA optimization:

1. **Verify Setup**
   ```batch
   .\verify_dspy_model.bat
   ```

2. **Expand Dataset** (if needed)
   ```batch
   python expand_validation_dataset.py --sample-theological
   ```

3. **Start MLflow Server** (in PowerShell)
   ```powershell
   powershell -Command "mlflow ui --host 127.0.0.1 --port 5000"
   ```

4. **Run Complete Optimization**
   ```batch
   .\run_complete_optimization.bat better_together 10 0.95
   ```

## Detailed Fixes for JSON Parsing Errors

### 1. Language Model Configuration

**Before** (causes errors):
```python
lm = dspy.LM(
    model_type="openai", 
    model="mistral-nemo-instruct-2407",
    api_base="http://localhost:1234/v1",
    api_key="dummy",
    config={
        "response_format": {"type": "json_object"},  # Causes errors with LM Studio
        "temperature": 0.1
    }
)
```

**After** (fixed):
```python
lm = dspy.LM(
    model_type="openai", 
    model="mistral-nemo-instruct-2407",
    api_base="http://localhost:1234/v1",
    api_key="dummy",
    config={
        "temperature": 0.1,
        "max_tokens": 1024
    }
)
```

### 2. BetterTogether Optimizer Configuration

**Before** (causes errors):
```python
optimizer = dspy.BetterTogether(
    metric=metric,
    modules=[module1, module2]  # DSPy 2.6 no longer accepts this parameter
)
```

**After** (fixed):
```python
optimizer = dspy.BetterTogether(
    metric=metric
)
```

### 3. Batch Size Reduction

**Before** (causes overflow):
```python
optimized_model = optimizer.compile(
    student=ensemble_student,
    trainset=train_data[:100],  # Too many examples
    strategy="p -> w -> p",
    valset_ratio=0.2
)

evaluator = dspy.Evaluate(
    devset=val_data,  # Too many examples
    metric=metric,
    num_threads=4,  # Too many concurrent requests
    display_progress=True,
    display_table=False
)
```

**After** (fixed):
```python
optimized_model = optimizer.compile(
    student=ensemble_student,
    trainset=train_data[:20],  # Reduced examples
    strategy="p -> w -> p",
    valset_ratio=0.2
)

evaluator = dspy.Evaluate(
    devset=val_data[:20],  # Reduced examples
    metric=metric,
    num_threads=2,  # Fewer concurrent requests
    display_progress=True,
    display_table=False
)
```

## Expected Results

The optimization process should now:
1. Successfully generate theological questions with Strong's IDs
2. Verify LM Studio connectivity without JSON errors
3. Track optimization progress with MLflow
4. Increase accuracy with each iteration (typically reaching 80-90% after 10 iterations)
5. Save optimized models to `models/dspy/bible_qa_optimized/`

## Further Troubleshooting

If you still encounter issues:

1. **Check LM Studio** to ensure it's running with a compatible model
2. **Verify DSPy Version** (`python -c "import dspy; print(dspy.__version__)"`) is 2.6.0 or higher
3. **Clear Cache** by removing the `local_cache` directory
4. **Restart Services** including LM Studio and MLflow
5. **Reduce Batch Size** further if necessary

For technical details about DSPy version compatibility, see `models/dspy/version_reference.md`. 