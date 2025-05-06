# DSPy 2.6 Integration for Bible Scholar Project

This document describes the integration of DSPy 2.6 with the Bible Scholar Project to enable training and inference using smaller local models.

## Overview

We've integrated [DSPy 2.6](https://github.com/stanfordnlp/dspy) with [LM Studio](https://lmstudio.ai) to create a Bible Question Answering system that can:

1. Use locally running LLMs through LM Studio's API
2. Perform inference for Bible-related questions without requiring expensive cloud API calls
3. Run on consumer hardware with appropriate quantized models
4. Leverage the modern DSPy 2.6 API for better compatibility and access to features like adapters

## Components

### 1. Bible QA API (`final_bible_qa_api.py`)

A Flask API server that provides endpoints for:
- Health checking
- Bible question answering

The API creates fresh DSPy modules for each request rather than attempting to load models from disk, avoiding permission issues and ensuring consistency.

### 2. DSPy Training (`simple_dspy_train.py`)

A simple script to train DSPy models using:
- LM Studio models as teachers
- Small local models as students
- Bible QA examples as training data

### 3. Testing Client (`test_bible_qa.py`)

A Python script to test the Bible QA API with custom contexts and questions.

### 4. Upgrade Tool (`scripts/upgrade_to_dspy26.py`)

A utility script for:
- Upgrading from DSPy 2.5.x to DSPy 2.6
- Replacing deprecated client classes with the unified `dspy.LM` API
- Disabling problematic integrations (Langfuse)

## Setup and Usage

### Prerequisites

1. Install LM Studio from [lmstudio.ai](https://lmstudio.ai)
2. Download the following models in LM Studio:
   - `darkidol-llama-3.1-8b-instruct-1.2-uncensored` (for chat)
   - `gguf-flan-t5-small` (for completion)
   - `text-embedding-nomic-embed-text-v1.5@q8_0` (for embeddings)
3. Start the LM Studio API server (Developer tab)
4. Ensure DSPy 2.6.0 is installed: `pip install dspy-ai==2.6.0`

### Environment Configuration

Create a `.env.dspy` file with the following environment variables:

```
# Port configuration
PORT=5005

# LM Studio API endpoints
LM_STUDIO_API_URL=http://localhost:1234/v1
LM_STUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0
LM_STUDIO_CHAT_MODEL=darkidol-llama-3.1-8b-instruct-1.2-uncensored
LM_STUDIO_COMPLETION_MODEL=gguf-flan-t5-small

# Disable Langfuse to avoid NoneType has no len() errors
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://localhost:1234
```

### Running the API

```bash
python final_bible_qa_api.py
```

The API will start on port 5005.

### Testing the API

Use the provided test script:

```bash
python test_bible_qa.py --context "Your Bible verse here" --question "Your question here"
```

Or make requests directly to the API:

```bash
curl -X POST http://localhost:5005/qa \
  -H "Content-Type: application/json" \
  -d '{"context": "In the beginning God created the heavens and the earth.", "question": "Who created the heavens and the earth?"}'
```

## Implementation Details

### DSPy 2.6 API Integration

The project uses the DSPy 2.6 unified API approach:

```python
# Create language model
lm = dspy.LM(
    f"openai/{model_name}",  # Using the provider prefix format
    api_base="http://localhost:1234/v1", 
    api_key="lm-studio",
    model_type='chat'  # Explicitly specify model type
)

# Configure DSPy to use this LM
dspy.configure(lm=lm)  # New configuration method in DSPy 2.6
```

### DSPy Bible QA Module

We've created a `BibleQAModule` that:
1. Takes a biblical context and a question as input
2. Uses a DSPy signature to define the input/output format
3. Returns an answer based on the context

### LM Studio Integration

The system uses LM Studio's OpenAI-compatible API endpoints to:
1. Generate embeddings for semantic search
2. Run chat completions for answering questions
3. Provide fallback options when DSPy modules encounter issues

### Fallback Mechanisms

The API implements a multi-tier fallback system:
1. First tries to use the DSPy module with the LM Studio model
2. Falls back to direct API calls if DSPy encounters errors
3. Provides hardcoded answers if all else fails

## Process Management

### Proper Server Management

One key challenge in our implementation was managing multiple server processes effectively. Follow these guidelines:

1. **Use Unique Ports**: Each server should have a dedicated port
   - DSPy API: 5005
   - Testing Servers: 5006+
   - LM Studio: 1234 (default)

2. **Background vs Foreground**:
   - Development: Run servers in the foreground to see logs
   - Production: Use background processes with proper logging

3. **Terminating Servers**:
   - Check running servers with `netstat -ano | findstr "5005 5004 5003"`
   - Terminate with `taskkill /PID [PID] /F` when needed

4. **Avoid Flask Debug Mode in Production**:
   - Debug mode causes frequent reloads with file changes
   - Use `debug=False` for stable operation

### Server Management Script

Use the provided server management script:

```bash
# Start the DSPy API in foreground mode
./scripts/server_management.ps1 -StartDspyApi

# Start the DSPy API in background mode
./scripts/server_management.ps1 -StartDspyApi -Background

# List all running servers
./scripts/server_management.ps1 -ListServers

# Stop all servers
./scripts/server_management.ps1 -StopAll
```

## Issues Resolved

### DSPy 2.5 Deprecation Warnings

We've successfully migrated to DSPy 2.6 using our `scripts/upgrade_to_dspy26.py` script, which:
- Replaced deprecated `GPT3` client with the modern `dspy.LM` interface
- Updated configuration methods from `dspy.settings.configure()` to `dspy.configure()`
- Applied provider prefix format for models (e.g., `openai/{model_name}`)
- Added explicit model type specifications

### Langfuse Integration Issues

We disabled the Langfuse integration that was causing `NoneType has no len()` errors by:
- Setting empty environment variables for Langfuse keys
- Configuring an invalid host to prevent connection attempts

### Model Loading Issues

We improved model loading reliability by:
- Creating fresh DSPy modules for each request rather than loading from disk
- Using the fallback mechanism in the API for robust error handling

## Troubleshooting

If you encounter issues:

1. **API Not Starting**:
   - Check if the port is already in use with `netstat -ano | findstr "5005"`
   - Ensure LM Studio API is running on port 1234
   - Verify DSPy 2.6.0 is installed with `pip show dspy-ai`

2. **Model Not Responding**:
   - Verify the correct models are loaded in LM Studio
   - Check LM Studio API server is running in Developer tab
   - Ensure the model names in `.env.dspy` match exactly with LM Studio

3. **Permission Issues**:
   - Run the application from a directory where you have write permissions
   - Check for file locks if trying to update model files

4. **Invalid Response Format**:
   - For structured output, consider using the DSPy 2.6 JSON adapter:
     ```python
     lm_with_json = lm.with_adapter('json')
     dspy.configure(lm=lm_with_json)
     ```

## License

This integration is part of the Bible Scholar Project and follows its licensing terms. 