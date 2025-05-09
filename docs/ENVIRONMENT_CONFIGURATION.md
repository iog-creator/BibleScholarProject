# Environment Configuration Guide

This document provides information about environment configuration for the BibleScholarProject, including DSPy integration, MLflow, and API keys.

## Overview

The project uses environment files to manage configuration:

1. `.env` - Main application configuration
2. `.env.dspy` - DSPy-specific configuration
3. `.env.example` and `.env.example.dspy` - Example configuration templates

## Security Guidelines

- **Never commit** actual environment files with API keys to the repository
- All `.env*` files (except examples) are excluded in `.gitignore`
- Rotate API keys if they're accidentally committed
- Use placeholder values in example files

## Main Environment Configuration

Copy `.env.example` to `.env` and customize:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=biblescholar
DB_USER=your_username
DB_PASSWORD=your_password_here

# API Keys (replace with your own)
HUGGINGFACE_API_KEY=your_huggingface_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Web Application Settings
WEB_HOST=0.0.0.0
WEB_PORT=8000
DEBUG=True
```

## DSPy Environment Configuration

Copy `.env.example.dspy` to `.env.dspy` and customize:

```bash
# LLM Provider Keys (choose at least one)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# LM Studio Configuration (for local models)
LM_STUDIO_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=your_local_model_here

# MLflow Tracking 
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=bible_qa_optimization

# DSPy Parameters
DSPY_NUM_THREADS=4
DSPY_CACHE_DIR=./local_cache/dspy
DSPY_VERBOSE=True
```

## Loading Environment Variables

The project automatically loads both `.env` and `.env.dspy` files. In your code:

```python
import os
from dotenv import load_dotenv

# Load both environment files
load_dotenv()  # Loads .env by default
load_dotenv(".env.dspy")  # Load DSPy-specific settings

# Access the variables
db_host = os.getenv("DB_HOST")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
```

## Validation and Verification

You can verify your environment configuration with:

```bash
# Check main environment
python check_imports.py

# Check DSPy environment
python check_dspy_setup.py

# Check LM Studio integration
python check_dspy_setup.py --use-lm-studio
```

## MLflow Configuration

MLflow settings are managed through environment variables:

```bash
MLFLOW_TRACKING_URI=http://localhost:5000  # Local tracking server
MLFLOW_EXPERIMENT_NAME=bible_qa_optimization
```

Start the MLflow tracking server with:

```bash
mlflow ui --host 127.0.0.1 --port 5000
# Or use the batch file
./start_mlflow_server.bat
```

## Troubleshooting

If you encounter environment-related issues:

1. **Missing API Keys**: Check that your environment files exist and contain the required keys
2. **Invalid Paths**: Ensure paths are correct for your operating system
3. **Connection Issues**: Verify that services like LM Studio are running on the specified ports
4. **Permission Errors**: Check file permissions on environment files and directories

## References

- [Python dotenv Documentation](https://pypi.org/project/python-dotenv/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [DSPy Documentation](https://dspy.ai) 