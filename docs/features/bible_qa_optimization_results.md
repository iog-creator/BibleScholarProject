# Bible QA Optimization Results and Troubleshooting

This document tracks the results of Bible QA optimization runs, identifies common issues, and provides solutions.

## Latest Optimization Results

| Date | Method | Accuracy | Iterations | Notes |
|------|--------|----------|------------|-------|
| 2023-05-07 | BetterTogether | 29.1% | 1 | JSON parsing errors interrupted optimization |
| 2023-05-06 | InferRules | 24.5% | 2 | DSPy 2.6 compatibility issues |

## Common Issues and Solutions

### 1. JSON Parsing Errors

**Issue**: The optimization was interrupted with error messages like:
```
ERROR dspy.utils.parallelizer: Error for Example(...): Expected a JSON object but parsed a <class 'str'>
```

**Solution**: 
- Remove the `response_format` parameter from the LM configuration
- Ensure DSPy 2.6 experimental features are enabled with `dspy.settings.experimental = True`
- Use the following configuration for LM Studio:

```python
lm = dspy.LM(
    model_type="openai", 
    model=model_name,
    api_base=lm_studio_api,
    api_key="dummy",
    config={
        "temperature": 0.1,
        "max_tokens": 1024
    }
)
```

### 2. BetterTogether Initialization Issues

**Issue**: The BetterTogether optimizer fails with `unexpected keyword argument 'modules'` error.

**Solution**:
- Initialize BetterTogether without the `modules` parameter:

```python
optimizer = dspy.BetterTogether(
    metric=metric
)
```

### 3. PowerShell MLflow Server Issues

**Issue**: MLflow server fails to start with PowerShell using the `start` command.

**Solution**:
- Use PowerShell's `Start-Process` instead of `start`:

```powershell
powershell -Command "Start-Process -FilePath 'mlflow' -ArgumentList 'ui', '--host', '127.0.0.1', '--port', '5000' -WindowStyle Minimized"
```

### 4. DSPy 2.6 Compatibility

**Issue**: The `score()` method in custom metrics is deprecated in DSPy 2.6.

**Solution**:
- Convert custom metrics to use the `__call__` pattern:

```python
class BibleQAMetric:
    def __call__(self, example, pred):
        # Metric implementation here
        return score
```

## Optimization Path to 95% Accuracy

Based on our experiments, here is the recommended path to achieve 95% accuracy:

1. **Verify DSPy Setup**: Run `verify_dspy_model.bat` to ensure LM Studio is configured correctly
2. **Expand Validation Dataset**: Use `scripts/expand_validation_dataset.py` to generate diverse theological questions
3. **Initial Optimization**: Run BetterTogether optimization for 5 iterations
4. **Error Analysis**: Analyze errors using the MLflow UI
5. **Final Optimization**: Run ensemble optimization for 10 iterations

## MLflow Integration Results

The MLflow integration successfully tracks:
- Accuracy metrics per iteration
- Best model checkpoints
- Learning curves

To view results, access the MLflow UI at http://localhost:5000 during or after optimization.

## Next Steps

To further improve accuracy:
1. Generate more diverse validation data
2. Experiment with different DSPy optimizers like `dspy.GradientRules`
3. Fine-tune hyperparameters for BetterTogether
4. Implement custom assertions for theological accuracy

## References

- [DSPy Optimization Guide](https://dspy.ai/learn/optimization/overview/)
- [MLflow DSPy Integration](https://mlflow.org/docs/latest/python_api/mlflow.dspy.html)
- [BetterTogether API](https://dspy.ai/api/optimizers/BetterTogether/) 