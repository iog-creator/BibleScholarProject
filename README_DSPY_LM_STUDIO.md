# DSPy 2.6 with LM Studio Integration

This guide explains how to successfully integrate DSPy 2.6 with LM Studio in the BibleScholarProject, focusing on compatibility solutions and best practices.

## Prerequisites

- **LM Studio**: Version 0.3.0 or newer
- **Python**: 3.10 or newer
- **DSPy**: Version 2.6.16 or newer

## Quick Start

1. **Run the integration test** to verify your setup:
   ```
   test_dspy_lm_studio.bat
   ```

2. **If you encounter issues**, check the logs in `logs/test_dspy_lm_studio.log`

## Configuration

### Environment Setup

Create a `.env.dspy` file with the following configuration:

```
LM_STUDIO_API_URL=http://localhost:1234/v1
LM_STUDIO_CHAT_MODEL=mistral-nemo-instruct-2407
LM_STUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0
```

Replace the model names with the ones you've loaded in LM Studio.

### Essential Imports

Always import the required modules in this order:

```python
import os
from dotenv import load_dotenv
load_dotenv('.env.dspy')  # Load environment variables first

import dspy
import dspy_json_patch  # Apply JSON patch for LM Studio compatibility

# Enable experimental features for DSPy 2.6
dspy.settings.experimental = True
```

## LM Studio Setup

1. **Start LM Studio** and load your preferred model
2. **Enable the API Server** in Settings → API → Enable API Server
3. **Verify API access** by visiting http://localhost:1234/v1/models in your browser

## DSPy Configuration Pattern

Always use this pattern to configure DSPy with LM Studio:

```python
def configure_lm_studio():
    """Configure DSPy to use LM Studio."""
    try:
        lm_studio_api = os.environ.get("LM_STUDIO_API_URL", "http://localhost:1234/v1")
        model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
        
        # Connect using OpenAI provider type (LM Studio is OpenAI-compatible)
        lm = dspy.LM(
            model_type="openai",
            model=model_name,
            api_base=lm_studio_api,
            api_key="dummy",  # LM Studio doesn't check API keys
            config={"temperature": 0.1, "max_tokens": 1024}
        )
        
        dspy.configure(lm=lm)
        return True
    except Exception as e:
        logger.error(f"LM Studio configuration failed: {e}")
        return False
```

## JSON Schema Integration

LM Studio 0.3.0+ supports structured output using JSON Schema, which can greatly improve the reliability of DSPy responses by ensuring they match the expected format.

### Basic Usage

When you import the `dspy_json_patch` module, it automatically patches DSPy to use LM Studio's JSON Schema capabilities:

```python
import dspy
import dspy_json_patch  # Enables JSON Schema integration

# Define a signature with multiple output fields
class BibleQA(dspy.Signature):
    """Answer questions about Bible verses."""
    context = dspy.InputField(desc="Biblical context or verse")
    question = dspy.InputField(desc="Question about the context")
    reasoning = dspy.OutputField(desc="Step-by-step reasoning")
    answer = dspy.OutputField(desc="The final answer")
    
# Create a predictor
predictor = dspy.ChainOfThought(BibleQA)

# The response will automatically use JSON Schema
result = predictor(
    context="Genesis 1:1 - In the beginning God created the heaven and the earth.",
    question="What did God create?"
)

print(f"Reasoning: {result.reasoning}")
print(f"Answer: {result.answer}")
```

### Testing JSON Schema Support

Run the JSON Schema integration test to verify this capability:

```
test_lm_studio_json_schema.bat
```

### Advanced JSON Schema Usage

For more complex schemas or direct API usage:

```python
import dspy_json_patch

# Get a JSON schema from a DSPy signature
schema = dspy_json_patch.get_json_schema_for_signature(BibleQA)

# Or create a custom schema
custom_schema = {
    "type": "object",
    "properties": {
        "verse_analysis": {
            "type": "object",
            "properties": {
                "book": {"type": "string"},
                "chapter": {"type": "string"},
                "verse": {"type": "string"},
                "key_terms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "term": {"type": "string"},
                            "meaning": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["book", "chapter", "verse", "key_terms"]
        },
        "interpretation": {"type": "string"}
    },
    "required": ["verse_analysis", "interpretation"]
}

# Configure LM Studio to use a custom schema directly
api_url = os.environ.get("LM_STUDIO_API_URL", "http://localhost:1234/v1")
model_name = os.environ.get("LM_STUDIO_CHAT_MODEL", "mistral-nemo-instruct-2407")
dspy_json_patch.configure_lm_studio_json_schema(api_url, model_name, custom_schema)
```

## Known Issues and Solutions

### 1. JSON Parsing Errors

LM Studio may return string responses instead of properly formatted JSON, causing parsing errors in DSPy.

**Solution**: Import `dspy_json_patch` which provides enhanced JSON parsing:

```python
import dspy_json_patch  # Must be imported after dspy
```

### 2. Model Saving/Loading Issues

DSPy 2.6 uses pickle by default, which can cause compatibility issues.

**Solution**: Use Python module-based saving instead:

```python
# Save model as Python module
def save_model(model, output_dir="models/dspy/bible_qa_optimized", name="bible_qa_model"):
    """Save model as Python module."""
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, f"{name}.py")
    
    with open(model_path, 'w') as f:
        f.write(f"""#!/usr/bin/env python3
\"\"\"
Bible QA model optimized with DSPy 2.6
\"\"\"
import dspy

{inspect.getsource(model.__class__)}

def get_model():
    \"\"\"Return a fresh instance of the model.\"\"\"
    return {model.__class__.__name__}()
""")
    return model_path

# Load model from Python module
def load_model(model_path):
    """Load model from Python module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("model_module", model_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    if hasattr(module, 'get_model'):
        return module.get_model()
    else:
        raise AttributeError(f"Module {model_path} has no get_model function")
```

### 3. Multi-turn Conversation Handling

Always handle the `history` parameter with a default value:

```python
def forward(self, context, question, history=None):
    prediction = self.qa_model(
        context=context, 
        question=question, 
        history=history or []  # Use empty list if history is None
    )
    return prediction
```

### 4. LM Studio API Connection Issues

If you encounter `ErrorDeviceLost` or other connection issues:

1. Disable integrated graphics in LM Studio Settings → Hardware
2. Reduce model size or batch size
3. Restart LM Studio and ensure it's not using GPU memory from another application

## Compatible Optimizers

| Optimizer | LM Studio Compatibility | Notes |
|-----------|-------------------------|-------|
| BootstrapFewShot | ✅ Good | Recommended for LM Studio |
| BetterTogether | ⚠️ Limited | Use with caution, some parameter limitations |
| MIPRO/MIPROv2 | ⚠️ Limited | Bootstrap phase may fail with JSON errors |
| RL-based optimizers | ❌ Poor | Not recommended with LM Studio |

## Testing Your Integration

Run the comprehensive test script:

```
python test_dspy_lm_studio.py
```

This checks:
- DSPy version compatibility
- Environment configuration
- LM Studio API connection
- Simple prediction functionality 
- Multi-turn conversation support
- Model saving/loading

## Troubleshooting

1. **JSON Parsing Errors**:
   - Check that `dspy_json_patch.py` is imported correctly
   - Verify the model is loaded in LM Studio
   - Try reducing prompt complexity

2. **API Connection Failures**:
   - Ensure LM Studio API server is enabled and running
   - Check `.env.dspy` configuration matches your LM Studio setup
   - Try restarting LM Studio or using a different model

3. **Model Loading/Saving Issues**:
   - Use Python module-based saving instead of pickle
   - Ensure module names don't conflict with Python standard library

## Additional Resources

- [DSPy Documentation](https://dspy.ai/)
- [LM Studio GitHub](https://github.com/lmstudio-ai)
- [Integration Guide](docs/rules/dspy_lm_studio_integration.md)

For detailed implementation examples, see:
- `test_dspy_lm_studio.py`
- `train_and_optimize_bible_qa.py`
- `test_optimized_bible_qa.py`

## MLflow Integration

DSPy 2.6 integrates with MLflow for experiment tracking and model management.

### Setup MLflow

1. Install MLflow:

```bash
pip install mlflow
```

2. Start MLflow server (in a separate terminal):

```bash
mlflow ui --port 5000
```

### Basic MLflow Integration

```python
import mlflow

# Configure MLflow
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("bible_qa_optimization")
mlflow.dspy.autolog()  # Enable DSPy autologging

# Train with MLflow tracking
with mlflow.start_run(run_name="bible_qa_run"):
    # Log parameters
    mlflow.log_params({
        "optimizer": "BootstrapFewShot",
        "max_train": len(train_data)
    })
    
    # Train your model
    optimized_model = optimizer.compile(student=model, trainset=train_data)
    
    # Evaluate and log metrics
    accuracy = evaluate_model(optimized_model, test_data)
    mlflow.log_metric("accuracy", accuracy)
    
    # Save model
    mlflow.dspy.log_model(optimized_model, "model")
```

### Analyzing Results

The project includes tools for analyzing MLflow experiments:

```bash
# Run the analyzer with visualizations
python analyze_mlflow_results.py --experiment "bible_qa_optimization" --visualize
```

### Optimization Scripts

For convenience, batch scripts are provided:

```bash
# Run optimization with MLflow tracking
run_dspy_mlflow_optimization.bat --max-train 10 --visualize
```

For detailed documentation on MLflow integration, see [docs/rules/dspy_mlflow_integration.md](docs/rules/dspy_mlflow_integration.md).

## References

- [DSPy Documentation](https://dspy.ai/)
- [LM Studio Documentation](https://lmstudio.ai/docs/basics)
- [MLflow Documentation](https://www.mlflow.org/docs/latest/index.html) 