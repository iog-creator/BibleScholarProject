# Bible QA Optimization with DSPy 2.6

This document provides guidance on using DSPy 2.6 to optimize the Bible QA system, with specific focus on handling JSON formatting issues and achieving the target 95% accuracy.

## Key Components

The Bible QA optimization system consists of:

1. **DSPy Verification Script** (`scripts/verify_dspy_model.py`): Validates that LM Studio is properly configured
2. **Validation Dataset Expansion** (`expand_validation_dataset.py`): Adds theological questions with Strong's IDs
3. **Optimization Script** (`train_and_optimize_bible_qa.py`): Runs BetterTogether, InferRules, or Ensemble optimization
4. **MLflow Integration**: Tracks optimization metrics and models
5. **Analysis Tools** (`scripts/analyze_mlflow_results.py`): Visualizes optimization performance

## Important DSPy 2.6 Requirements

DSPy 2.6 introduced several changes that require specific configuration:

1. **Experimental Features**: For BetterTogether and InferRules optimizers, enable experimental features:
   ```python
   dspy.settings.experimental = True
   ```

2. **JSON Compatibility**: For LM Studio models, **do not** use the `response_format` parameter:
   ```python
   # INCORRECT - Will cause JSON parsing errors
   lm = dspy.LM(
       model_type="openai", 
       model="mistral-nemo-instruct-2407",
       api_base="http://localhost:1234/v1",
       api_key="dummy",
       config={
           "response_format": {"type": "json_object"},  # This causes errors
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
           "max_tokens": 1024
       }
   )
   ```

3. **BetterTogether Constructor**: The `modules` parameter is no longer supported:
   ```python
   # INCORRECT
   optimizer = dspy.BetterTogether(
       metric=metric,
       modules=[module1, module2]  # This causes errors
   )
   
   # CORRECT
   optimizer = dspy.BetterTogether(
       metric=metric
   )
   ```

## Running the Optimization

1. **Verify Setup**:
   ```batch
   .\verify_dspy_model.bat
   ```

2. **Expand Dataset** (if needed):
   ```batch
   python expand_validation_dataset.py --sample-theological
   ```

3. **Start MLflow** (in PowerShell):
   ```powershell
   powershell -Command "mlflow ui --host 127.0.0.1 --port 5000"
   ```

4. **Run Optimization**:
   ```batch
   python train_and_optimize_bible_qa.py --optimization-method better_together --max-iterations 10 --target-accuracy 0.95
   ```

5. **Run Complete Workflow**:
   ```batch
   .\run_complete_optimization.bat better_together 10 0.95
   ```

## Troubleshooting

### JSON Parsing Errors

If you encounter errors like:
```
Expected a JSON object but parsed a <class 'str'>
```

1. Check that you're not using `response_format` in your LM configuration
2. Make sure DSPy experimental mode is enabled: `dspy.settings.experimental = True`
3. Clear any cached model configurations: `rm -r local_cache/*` (or delete the folder)

### MLflow Connection Issues

If MLflow doesn't start properly:
1. Use the PowerShell command: `powershell -Command "mlflow ui --host 127.0.0.1 --port 5000"`
2. Check that port 5000 is not in use: `netstat -ano | findstr 5000`
3. Kill any process using port 5000 if needed

### Low Accuracy

If the model accuracy is lower than expected:
1. Try a different optimization method: BetterTogether often works best for diverse datasets
2. Increase the number of iterations (10-20 is recommended)
3. Expand the validation dataset with more theological questions 
4. Try the Ensemble method that combines BetterTogether and InferRules

## Optimization Methods

### BetterTogether

Best for diverse question types. It learns which approach works best for different questions:
- Chain-of-Thought for factual questions
- Program-of-Thought for complex reasoning
- Specialized components for theological terms

### InferRules

Best for consistent patterns. It learns explicit rules to improve performance:
- Derives rules from successful examples
- Works well when there are clear patterns in how certain questions should be answered
- Good for theological questions with Strong's IDs

### Ensemble

Combines both approaches for maximum accuracy:
- Uses both BetterTogether and InferRules
- Takes the best-performing model from each
- Achieves highest accuracy but takes more time

## Reference

For more information, see:
- [DSPy Documentation](https://dspy.ai/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [README_DSPY_OPTIMIZATION.md](../../README_DSPY_OPTIMIZATION.md) 