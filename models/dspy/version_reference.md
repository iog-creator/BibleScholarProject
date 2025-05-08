# DSPy Version Reference Guide

This guide explains DSPy version compatibility and the features available in different versions for the BibleScholarProject.

## Supported DSPy Versions

| Version | Status | Features | Limitations |
|---------|--------|----------|-------------|
| 2.6.x   | Recommended | BetterTogether, InferRules, MLflow integration | JSON formatting issues with LM Studio |
| 2.5.x   | Compatible | Basic optimizers (GRPO, Bootstrap) | No BetterTogether, InferRules |
| 2.4.x   | Compatible with fixes | Basic optimizers | No experimental optimizers |
| < 2.4.0 | Not Supported | - | Missing essential features |

## Version-Specific Notes

### DSPy 2.6.x (Recommended)

The Bible QA optimization system is designed for DSPy 2.6.x with specific configuration:

1. **Requirements**: 
   - Install with: `pip install "dspy-ai>=2.6.0" mlflow`
   - Enable experimental features: `dspy.settings.experimental = True`

2. **JSON Compatibility**: 
   - **Do not** use the `response_format` parameter with LM Studio
   - Remove `modules` parameter from BetterTogether constructor

3. **Available Optimizers**:
   - BetterTogether: Best for diverse question types
   - InferRules: Best for theological questions with Strong's IDs
   - Ensemble: Combines both approaches

4. **MLflow Integration**:
   - Built-in tracking via `mlflow.dspy.log_model`
   - Automatic metric logging

### DSPy 2.5.x (Compatible)

Compatible but with limited optimization options:

1. **Requirements**:
   - Install with: `pip install "dspy-ai>=2.5.0,<2.6.0" mlflow`

2. **Available Optimizers**:
   - GRPO (Gradient-based Prompt Optimization)
   - Bootstrap (Iterative refinement)

3. **Limitations**:
   - No BetterTogether or InferRules
   - May have JSON parsing issues with newer models

### DSPy 2.4.x (Compatible with Fixes)

Can be used with specific fixes:

1. **Requirements**:
   - Install with: `pip install "dspy-ai>=2.4.0,<2.5.0" mlflow`

2. **Necessary Fixes**:
   - Manual MLflow integration
   - Custom implementation of optimizers

3. **Limitations**:
   - No automatic MLflow tracking
   - No experimental optimizers

## Setting Up for DSPy 2.6

To set up for DSPy 2.6:

1. **Install dependencies**:
   ```bash
   pip install "dspy-ai>=2.6.0" mlflow
   ```

2. **Configure your environment**:
   - `.env.dspy`: Environment variables for DSPy
   - Set `LM_STUDIO_CHAT_MODEL` to your preferred model
   - Set `LM_STUDIO_API_URL` to your LM Studio endpoint

3. **Verify compatibility**:
   ```batch
   .\verify_dspy_model.bat
   ```

4. **Run with experimental features**:
   ```python
   import dspy
   
   # Enable experimental features
   dspy.settings.experimental = True
   
   # Configure LM without response_format
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
   
   # Set as default LM
   dspy.configure(lm=lm)
   ```

## Common Error Messages

| Error | Likely Version | Solution |
|-------|----------------|----------|
| `BetterTogether.__init__() got an unexpected keyword argument 'modules'` | 2.6.x | Remove 'modules' parameter |
| `Expected a JSON object but parsed a <class 'str'>` | 2.6.x | Remove 'response_format' parameter |
| `This is an experimental optimizer` | 2.6.x | Add `dspy.settings.experimental = True` |
| `Module not found: 'dspy.experimental'` | < 2.5.0 | Upgrade to DSPy 2.6 |
| `cannot schedule new futures after shutdown` | Any | Optimization was interrupted, restart |

## Version History

- **DSPy 2.6.4** (May 2025): Latest tested version
- **DSPy 2.6.0** (March 2025): Added BetterTogether, InferRules
- **DSPy 2.5.1** (January 2025): Added enhanced MLflow integration
- **DSPy 2.4.0** (November 2024): Added basic optimization support

## LM Studio Models

| Model | Compatibility | Max Tokens | Response Format | Notes |
|-------|---------------|------------|----------------|-------|
| mistral-nemo-instruct-2407 | ✅ Good | 4096 | ❌ No JSON | Remove `response_format` parameter |
| Llama-3-8B-Instruct | ✅ Good | 4096 | ❌ No JSON | Remove `response_format` parameter |
| Qwen2.5-7B-Instruct | ✅ Good | 4096 | ✅ Basic JSON | Test carefully with structured output |
| Mixtral-8x7B-Instruct | ⚠️ Limited | 4096 | ❌ No JSON | JSON parsing issues, use with caution |
| Falcon-40B-Instruct | ❌ Poor | 2048 | ❌ No JSON | Not recommended for optimization |

## Optimization Techniques

### BetterTogether

**Requirements**:
- DSPy 2.6+
- `dspy.settings.experimental = True`
- No `response_format` with LM Studio models
- No `modules` parameter in constructor

**Example Configuration**:
```python
# Enable experimental features
dspy.settings.experimental = True

# Configure optimizer
metric = BibleQAMetric()
optimizer = dspy.BetterTogether(
    metric=metric
)

# Configure LM (with LM Studio)
lm = dspy.LM(
    model_type="openai", 
    model="mistral-nemo-instruct-2407",
    api_base="http://127.0.0.1:1234/v1",
    api_key="dummy",
    config={
        "temperature": 0.1,
        "max_tokens": 1024
        # No response_format!
    }
)
```

### InferRules

**Requirements**:
- DSPy 2.6+
- `dspy.settings.experimental = True`
- Models with reasoning capabilities

**Example Configuration**:
```python
# Enable experimental features
dspy.settings.experimental = True

# Configure optimizer
metric = BibleQAMetric()
optimizer = dspy.InferRules(
    module=theological_model,
    metric=metric,
    max_rules=5
)
```

## MLflow Integration

**Requirements**:
- MLflow installed (`pip install mlflow`)
- PowerShell-compatible server start command
- DSPy 2.6+ for full integration

**Example Usage**:
```python
# Start MLflow run
with mlflow.start_run(run_name="bible_qa_optimization"):
    # Log metrics
    mlflow.log_metric("accuracy", score)
    
    # Save model
    model_info = mlflow.dspy.log_model(
        optimized_model,
        artifact_path="model",
        registered_model_name="bible_qa_optimized"
    )
```

## Troubleshooting Matrix

| Issue | DSPy 2.4 | DSPy 2.5 | DSPy 2.6 | Solution |
|-------|----------|----------|----------|----------|
| JSON parsing errors | ❌ Common | ❌ Common | ⚠️ Possible | Remove `response_format` parameter |
| `modules` parameter error | N/A | N/A | ❌ Common | Remove `modules` parameter from BetterTogether |
| `score()` method error | ✅ Works | ⚠️ Warning | ❌ Error | Convert to `__call__` pattern |
| MLflow integration fails | ❌ Not supported | ⚠️ Limited | ✅ Works | Upgrade to DSPy 2.6+ |
| PowerShell compatibility | ⚠️ Issues | ⚠️ Issues | ⚠️ Issues | Use `Start-Process` instead of `start` |

## Recommendations

1. **Always use DSPy 2.6+** for Bible QA optimization
2. **Remove `response_format`** when using LM Studio models
3. **Enable experimental features** with `dspy.settings.experimental = True`
4. **Use the `__call__` pattern** for custom metrics
5. **Start small** with optimization (5 iterations before scaling up)
6. **Verify the model** with `verify_dspy_model.bat` before optimization 