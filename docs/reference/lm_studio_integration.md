# LM Studio Integration Reference

This reference document details the integration between the BibleScholarProject and LM Studio.

## Overview

The BibleScholarProject uses LM Studio as a local inference server for language models. This approach provides:
- Local inference without external API dependencies
- Support for a variety of models
- Cost-effective operation for development and testing
- Compatibility with OpenAI-style APIs

## API Endpoints

LM Studio provides several compatible API endpoints that the BibleScholarProject uses:

| Endpoint | Purpose | Usage |
|----------|---------|-------|
| `/v1/chat/completions` | Generate chat completions | Used for DSPy program execution |
| `/v1/completions` | Generate text completions | Used for T5 model inference |
| `/v1/embeddings` | Generate text embeddings | Used for semantic search |
| `/v1/models` | List and manage models | Used for model verification |

## Environment Configuration

LM Studio integration is configured through environment variables in `.env.dspy`:

```
LM_STUDIO_API_URL=http://localhost:1234/v1
LM_STUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0
LM_STUDIO_CHAT_MODEL=darkidol-llama-3.1-8b-instruct-1.2-uncensored
LM_STUDIO_COMPLETION_MODEL=gguf-flan-t5-small
```

## API Usage Examples

### Chat Completions

```python
import requests
import os
import json

def get_chat_completion(messages):
    """Get chat completion from LM Studio."""
    lm_studio_api = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1")
    lm_studio_model = os.getenv("LM_STUDIO_CHAT_MODEL", "darkidol-llama-3.1-8b-instruct-1.2-uncensored")
    
    response = requests.post(
        f"{lm_studio_api}/chat/completions",
        headers={"Content-Type": "application/json"},
        json={
            "model": lm_studio_model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code}: {response.text}"
```

### Embeddings

```python
import requests
import os
import numpy as np

def get_embedding(text):
    """Get embedding from LM Studio."""
    lm_studio_api = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1")
    embedding_model = os.getenv("LM_STUDIO_EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5@q8_0")
    
    response = requests.post(
        f"{lm_studio_api}/embeddings",
        headers={"Content-Type": "application/json"},
        json={
            "model": embedding_model,
            "input": text
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        return result["data"][0]["embedding"]
    else:
        # Return a dummy embedding for error cases
        return np.zeros(768).tolist()
```

### Model Verification

```python
import requests
import os
import logging

def verify_model_availability(model_name):
    """Verify if a model is available in LM Studio."""
    lm_studio_api = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1")
    
    response = requests.get(f"{lm_studio_api}/models")
    if response.status_code == 200:
        available_models = response.json().get("data", [])
        model_loaded = any(model.get("id") == model_name for model in available_models)
        return model_loaded
    else:
        logging.error(f"Error checking LM Studio models: {response.status_code}")
        return False
```

### Model Loading

```python
import requests
import os
import logging

def load_model(model_name):
    """Attempt to load a model in LM Studio."""
    lm_studio_api = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1")
    
    response = requests.post(
        f"{lm_studio_api}/models", 
        json={"model": model_name}
    )
    
    if response.status_code in [200, 201]:
        logging.info(f"Successfully loaded model: {model_name}")
        return True
    else:
        logging.error(f"Failed to load model: {model_name}")
        return False
```

## DSPy Integration

The BibleScholarProject integrates LM Studio with DSPy using the OpenAI provider compatibility:

```python
import dspy
import os

def initialize_dspy():
    """Initialize DSPy with LM Studio."""
    # Load environment variables
    lm_studio_api = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1")
    lm_studio_model = os.getenv("LM_STUDIO_CHAT_MODEL", "llama3")
    
    # Set environment variables for openai compatibility
    os.environ["OPENAI_API_KEY"] = "dummy-key"
    os.environ["OPENAI_API_BASE"] = lm_studio_api
    
    # Use OpenAI provider with explicit provider name
    lm = dspy.LM(
        provider="openai",  # Explicitly set provider to "openai"
        model=lm_studio_model,
        api_base=lm_studio_api,
        api_key="dummy-key"  # LM Studio doesn't need a real key
    )
    dspy.settings.configure(lm=lm)
    return True
```

## Required Parameters

### Chat/Completion Endpoints

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| model | Yes | - | The model name to use |
| messages/prompt | Yes | - | The input text(s) |
| temperature | No | 0.7 | Controls randomness |
| max_tokens | No | 500 | Maximum tokens to generate |
| top_p | No | 1.0 | Probability mass to consider |
| frequency_penalty | No | 0.0 | Penalty for token frequency |
| presence_penalty | No | 0.0 | Penalty for token presence |

### Embeddings Endpoint

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| model | Yes | - | The embedding model name |
| input | Yes | - | Text to embed (string or array) |

## Error Handling

When handling LM Studio API calls, implement proper error handling:

```python
try:
    response = requests.post(f"{lm_studio_api}/chat/completions", ...)
    if response.status_code == 200:
        # Process successful response
        pass
    elif response.status_code == 404:
        # Model not found error
        logger.error("Model not found. Check if model is loaded in LM Studio.")
    elif response.status_code == 500:
        # Internal server error
        logger.error("LM Studio internal error. Check LM Studio logs.")
    else:
        # Other error
        logger.error(f"Error: {response.status_code}: {response.text}")
except requests.RequestException as e:
    # Connection error
    logger.error(f"Connection error: {e}")
    logger.error("Is LM Studio running?")
```

## See Also

- [DSPy Model Management](../guides/dspy_model_management.md)
- [Semantic Search](../features/semantic_search.md)
- [DSPy Training Guide](../guides/dspy_training_guide.md) 