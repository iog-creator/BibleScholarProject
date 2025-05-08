# DSPy Training Data Expansion and MLflow Integration

This directory contains scripts for expanding DSPy training data and integrating with MLflow for experiment tracking.

## Files Overview

### Data Generation and Setup

- `expand_dspy_training_data.py` - Main script to expand DSPy training data from multiple sources
- `check_dspy_setup.py` - Script to verify DSPy and MLflow environment setup
- `requirements-dspy.txt` - Package requirements for DSPy training

### Training Scripts

- `train_dspy_bible_qa.py` - Main DSPy training script with MLflow integration
- `train_dspy_bible_qa.bat` - Windows batch file for running the training script
- `check_dspy_setup.bat` - Windows batch file for checking the DSPy setup
- `setup_and_train_dspy.bat` - Comprehensive batch file for setup and training

### Documentation

- `README_DSPY.md` - Complete documentation for the DSPy training system
- `DSPY_TRAINING_README.md` - This file, with a summary of the training files

## Quick Start

For Windows users, the simplest way to get started is to run:

```
setup_and_train_dspy.bat
```

This will:
1. Install required packages
2. Verify the DSPy setup
3. Expand training data
4. Check LM Studio connection
5. Configure and run the training script
6. Open MLflow UI to view results

## Manual Steps

If you prefer to run the steps manually:

1. Install requirements:
   ```
   pip install -r requirements-dspy.txt
   ```

2. Check the DSPy setup:
   ```
   python check_dspy_setup.py
   ```

3. Expand training data:
   ```
   python expand_dspy_training_data.py --examples 5000 --deduplicate --stratify
   ```

4. Train the model:
   ```
   python train_dspy_bible_qa.py --model "google/flan-t5-small" --optimizer grpo --lm-studio
   ```

5. View results in MLflow:
   ```
   mlflow ui
   ```

## Data Sources

The data expansion script integrates multiple sources:

1. **Archive generation scripts** - Comprehensive generation from Bible database
2. **HuggingFace datasets** - Downloads Bible-related datasets
3. **Bible corpus expansion** - Adds specialized theological examples
4. **Existing datasets** - Incorporates and deduplicates existing data

## MLflow Integration

The training script is integrated with MLflow to track:

1. **Parameters** - Model type, optimizer, training parameters
2. **Metrics** - Accuracy, loss, and other performance metrics
3. **Artifacts** - Trained models and metadata
4. **Runs** - Multiple experiments with different configurations

## LM Studio Integration

The system integrates with LM Studio for efficient local model inference:

1. Uses the OpenAI-compatible API in LM Studio
2. Configures embeddings and model inference through environment variables
3. Provides compatibility with Llama-3 and other local models

## Next Steps

After training, you can:

1. Compare different model runs in MLflow UI
2. Load and use the trained model for inference
3. Explore different optimizer configurations
4. Integrate the model with the Bible QA API 