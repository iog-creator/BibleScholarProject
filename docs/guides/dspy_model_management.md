# DSPy Model Management in LM Studio

This guide explains how to manage and troubleshoot DSPy models with LM Studio in the BibleScholarProject.

## Required Models

The BibleScholarProject relies on several models in LM Studio:

1. **Chat Model**: `darkidol-llama-3.1-8b-instruct-1.2-uncensored` (or similar LLaMa model)
   - Used for general chat and completion tasks
   - Primary model for DSPy program execution

2. **Embedding Model**: `text-embedding-nomic-embed-text-v1.5@q8_0`
   - Used for generating vector embeddings for semantic search
   - Required for all pgvector-based search functionality

3. **T5 Model**: `gguf-flan-t5-small` 
   - Used for fine-tuned Bible question answering
   - Critical for the Bible QA system

## Environment Configuration

Model configuration is managed through environment variables in `.env.dspy`:

```
LM_STUDIO_API_URL=http://localhost:1234/v1
LM_STUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0
LM_STUDIO_CHAT_MODEL=darkidol-llama-3.1-8b-instruct-1.2-uncensored
LM_STUDIO_COMPLETION_MODEL=gguf-flan-t5-small
```

## Loading and Verifying Models

### Automated Model Verification

The system will automatically check for required models when starting:

1. At application startup, it attempts to verify all models are loaded
2. If a model is not found, a warning message is displayed
3. For automatic model loading, use the provided batch files

### Using the Model Management Tools

Two batch files help you manage models:

1. **check_required_models.bat** - Checks if all required models are loaded:
   ```
   > check_required_models.bat
   ```

2. **load_t5_model.bat** - Attempts to load the T5 model specifically:
   ```
   > load_t5_model.bat
   ```

### Command Line Options

The Bible QA API supports several command line options for model management:

```
python bible_qa_api.py --test-models    # Test if all required models are loaded
python bible_qa_api.py --load-t5        # Try to load the T5 model
python bible_qa_api.py --test-web       # Test the web server (10 seconds)
python bible_qa_api.py --test-only      # Only test model loading, don't start server
```

## Troubleshooting Model Issues

### T5 Model Not Loading

If you see errors related to the T5 model not being loaded:

1. Run `check_required_models.bat` to verify model status
2. Run `load_t5_model.bat` to attempt automatic loading
3. If automatic loading fails, open LM Studio and manually load the model:
   - In LM Studio, go to the Models tab
   - Search for "gguf-flan-t5-small"
   - Click "Load" next to the model
   - Restart your Bible QA application

### LM Studio API Connection Errors

If you see "Cannot connect to LM Studio API" errors:

1. Ensure LM Studio is running
2. Verify the API URL in `.env.dspy` matches your LM Studio configuration
3. Check that LM Studio's Local Server is enabled and running

### Model Compatibility Issues

If you encounter compatibility errors:

1. Verify you have the correct versions of the models in LM Studio
2. Check for model name mismatches between environment variables and available models
3. Try using an alternative model with similar capabilities

## Manual Model Management via API

For advanced users, models can be managed via the LM Studio API:

```python
import requests

def load_model(model_name):
    """Attempt to load a model via LM Studio API."""
    lm_studio_api = "http://localhost:1234/v1"
    
    response = requests.post(
        f"{lm_studio_api}/models", 
        json={"model": model_name}
    )
    
    if response.status_code in [200, 201]:
        print(f"Successfully loaded model: {model_name}")
        return True
    else:
        print(f"Failed to load model: {model_name}")
        return False
```

## Best Practices

1. **Always start LM Studio before running the application**
2. **Load models before starting the application server**
3. **Verify model availability with `--test-models` when troubleshooting**
4. **Keep model names in `.env.dspy` synchronized with LM Studio models**
5. **For production, ensure models are loaded in LM Studio's startup configuration**

## See Also

- [DSPy Training Guide](dspy_training_guide.md) - Guide for DSPy training
- [LM Studio Integration Guide](../reference/lm_studio_integration.md) - Detailed LM Studio integration documentation 