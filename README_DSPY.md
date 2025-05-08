# DSPy Bible QA System

This document explains how to use DSPy for training Bible Question-Answering models with enhanced capabilities and MLflow tracking.

## Overview

The DSPy Bible QA system provides:

1. **Enhanced Bible QA** with conversation history support
2. **Multiple optimizers** including GRPO, SIMBA, and BootstrapFewShot
3. **MLflow integration** for experiment tracking
4. **Theological assertion validation** for improved accuracy
5. **LM Studio integration** for local model inference
6. **Advanced optimization** with BetterTogether and InferRules

## Prerequisites

- Python 3.9+
- PyTorch 2.0+ (for local model inference)
- DSPy 2.6+
- MLflow
- LM Studio (for local inference)

## Setup

### 1. Environment Setup

First, ensure you have all the required dependencies:

```bash
pip install dspy mlflow python-dotenv requests torch
```

### 2. Environment Variables

Create a `.env.dspy` file in the project root with the following configuration:

```
# LM Studio API endpoints (for local inference)
LM_STUDIO_API_URL=http://localhost:1234/v1
LM_STUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0
LM_STUDIO_CHAT_MODEL=llama3-8b-instruct

# MLflow configuration
MLFLOW_TRACKING_URI=./mlruns
MLFLOW_EXPERIMENT_NAME=dspy_bible_qa

# HuggingFace API (alternative to LM Studio)
HUGGINGFACE_API_KEY=your_hf_api_key
```

### 3. Verify Environment

Run the environment check script to ensure everything is set up correctly:

```bash
python check_dspy_setup.py
```

This will verify that:
- Required libraries are installed
- Environment variables are configured
- LM Studio is running (if using LM Studio)
- MLflow tracking is configured
- Training data is available

## Training Data

The system uses a comprehensive dataset of Bible question-answer pairs.

### Expanding the Training Dataset

To create or expand the training dataset:

```bash
python expand_dspy_training_data.py --examples 5000 --huggingface --deduplicate --stratify
```

Options:
- `--examples`: Number of examples to generate (default: 5000)
- `--huggingface`: Download additional data from HuggingFace
- `--deduplicate`: Remove duplicate questions
- `--stratify`: Stratify train/val/test splits by book or source
- `--output-dir`: Output directory (default: data/processed/dspy_training_data/bible_corpus/dspy)

This will:
1. Run the archived data generation scripts
2. Download HuggingFace datasets (if requested)
3. Expand the Bible corpus with theological examples
4. Deduplicate the dataset (if requested)
5. Create proper train/validation/test splits

### Expanding the Validation Dataset

For optimization, having a robust validation dataset is crucial:

```bash
python -m scripts.expand_validation_dataset --num-single 50 --num-multi 15
```

Options:
- `--num-single`: Number of single-turn examples to generate (default: 50)
- `--num-multi`: Number of multi-turn conversation examples to generate (default: 15)
- `--include-theological`: Include theological questions with Strong's IDs
- `--output-file`: Output file (default: data/processed/dspy_training_data/bible_corpus/integrated/qa_dataset_val.jsonl)

This creates a diverse validation set with:
- Theological questions with Strong's IDs
- Multi-turn conversation examples
- Factual Bible verse questions

## Training Models

### Using the Training Script

The main training script provides a flexible way to train models with different optimizers:

```bash
python train_dspy_bible_qa.py --model "google/flan-t5-small" --optimizer grpo --lm-studio
```

Options:
- `--model`: Model to use (default: google/flan-t5-small)
- `--optimizer`: Optimizer to use [bootstrap, grpo, simba, miprov2] (default: bootstrap)
- `--lm-studio`: Use LM Studio for inference
- `--max-demos`: Maximum number of demonstrations to use (default: 8)
- `--data-dir`: Directory containing training data
- `--train-pct`: Percentage of data to use for training (default: 0.8)
- `--experiment-name`: MLflow experiment name (default: dspy_bible_qa)
- `--save-dir`: Directory to save trained models (default: models/dspy/bible_qa_t5)

### Using the Training Batch File

For Windows users, a batch file is provided for easier training:

```bat
train_dspy_bible_qa.bat
```

This will:
1. Check if DSPy and MLflow are installed
2. Expand the training data if needed
3. Check if LM Studio is running
4. Prompt for model size and optimizer choice
5. Run the training script with the selected options

## Advanced Optimization

The system supports advanced optimization methods to reach higher accuracy levels (95%+).

### Using the Optimization Script

```bash
python train_and_optimize_bible_qa.py --optimization-method better_together --max-iterations 10 --target-accuracy 0.95
```

Options:
- `--optimization-method`: Optimization method [better_together, infer_rules, ensemble] (default: better_together)
- `--max-iterations`: Maximum optimization iterations (default: 10)
- `--target-accuracy`: Target accuracy to achieve (default: 0.95)
- `--training-file`: Path to training JSONL file
- `--validation-file`: Path to validation JSONL file
- `--output-dir`: Directory to save optimized models (default: models/dspy/bible_qa_optimized)
- `--teacher-model`: Teacher model for optimization (default: gpt-4o-mini)

### Using the Optimization Batch File

For Windows users, a batch file simplifies the optimization process:

```bat
optimize_bible_qa.bat [optimization_method]
```

Where `optimization_method` can be:
- `better_together` (default): Ensembles multiple approaches
- `infer_rules`: Learns rules to improve theological reasoning
- `ensemble`: Tries both methods and selects the best

### Optimization Methods

1. **BetterTogether**:
   - Combines multiple model architectures (CoT, PoT, Theological QA)
   - Learns which approach works best for different question types
   - Good for diverse question sets

2. **InferRules**:
   - Focuses on improving a single model
   - Derives explicit reasoning rules to enhance performance
   - Especially effective for theological questions with Strong's IDs

3. **Ensemble**:
   - Runs both methods with half the iterations each
   - Selects the best-performing approach
   - Good when uncertain which method will work better

## Tracking Experiments with MLflow

The system uses MLflow to track training and optimization experiments:

1. **Start MLflow Server**:
   ```bash
   mlflow ui --host 127.0.0.1 --port 5000
   ```
   Then open http://localhost:5000 in your browser

2. **Compare Runs**: MLflow UI allows comparing metrics across different optimizer and model combinations

3. **Load Models**: Models can be loaded from MLflow for inference:
   ```python
   import mlflow.dspy
   
   # Load model from MLflow
   model = mlflow.dspy.load_model("runs:/RUN_ID/model")
   
   # Use the model
   result = model(context="Bible verse", question="Your question")
   print(result.answer)
   ```

### Analyzing Optimization Results

The project includes a dedicated tool for analyzing MLflow optimization results:

```bash
python -m scripts.analyze_mlflow_results --experiment-name bible_qa_optimization --compare-methods
```

Or use the batch file for a simplified workflow:

```bat
analyze_mlflow_results.bat
```

The analysis tool generates:

1. **Learning curves**: Visualization of accuracy improvement over iterations
2. **Method comparison**: Statistical comparison of different optimization methods
3. **Detailed reports**: CSV and JSON reports with detailed metrics

The tool supports the following options:
- `--experiment-name`: MLflow experiment name (default: bible_qa_optimization)
- `--output-dir`: Directory to save analysis results (default: analysis_results)
- `--top-n`: Number of top runs to analyze (default: 5)
- `--compare-methods`: Compare different optimization methods
- `--tracking-uri`: MLflow tracking URI (defaults to environment variable)

Results include:
- **optimization_curves.png**: Graph showing accuracy improvement over iterations
- **optimization_curves.html**: Interactive visualization (requires plotly)
- **method_comparison.csv**: Statistical comparison of optimization methods
- **method_comparison.json**: Detailed JSON report with run information
- **method_comparison.png**: Bar chart comparing method performance

## Model Architecture

The Bible QA system uses a modular architecture:

1. **BibleQASignature**: Defines the input/output interface including conversation history
2. **BibleQAModule**: Implements the QA functionality with theological assertions
3. **Optimizers**: Different optimizers (GRPO, SIMBA, etc.) for fine-tuning the prompts
4. **TheologicalQA**: Specialized module for theological questions with Strong's ID handling

### Theological QA Module

The system includes a specialized module for theological questions:

```python
from src.dspy_programs.theological_qa import TheologicalQA

# Initialize the theological QA system
theological_qa = TheologicalQA()

# Example with Strong's ID
result = theological_qa(
    context="In the beginning God created the heaven and the earth.",
    question="What is the meaning of 'God' (H430 Elohim) in Genesis 1:1?"
)
print(result.answer)
```

This module:
1. Extracts and analyzes Strong's IDs in questions
2. Performs theological exegesis on the text
3. Formulates precise answers with theological accuracy

### Conversation History

The system supports multi-turn conversations with history:

```python
# Example with conversation history
history = [
    ("Who created the heavens and the earth?", "God created the heavens and the earth."),
    ("When did this happen?", "In the beginning, as described in Genesis 1:1.")
]

result = model(
    context="Genesis 1:1-5",
    question="What did God create first?",
    history=history
)
```

### Theological Assertions

The model implements theological assertions to ensure accuracy:

1. Questions about God properly reference God
2. Questions about Jesus properly reference Jesus/Christ
3. Biblical references are accurate and consistent
4. Strong's IDs are correctly referenced and explained

## Evaluating Optimized Models

To test optimized models:

```bash
python test_enhanced_bible_qa.py --model-path models/dspy/bible_qa_optimized/final_YYYYMMDD_HHMMSS --batch-test --output-file optimized_results.json
```

Options:
- `--model-path`: Path to the optimized model directory
- `--test-file`: Path to test JSONL file
- `--batch-test`: Run batch testing on all examples in the test file
- `--output-file`: Path to output results file
- `--use-lm-studio`: Use LM Studio for inference (default: True)

## Troubleshooting

### LM Studio Issues

- Ensure LM Studio is running with the server enabled
- Check that the model specified in `.env.dspy` is loaded in LM Studio
- Verify the API URL is correct (typically http://localhost:1234/v1)
- Ensure JSON response format is configured for structured outputs

### MLflow Issues

- If MLflow UI doesn't show experiments, check the MLFLOW_TRACKING_URI setting
- For permission errors, check the directory permissions
- MLflow requires write access to the tracking URI directory
- Ensure the MLflow server is running on the correct port (5000)

### Training Data Issues

- If training fails due to missing data, run the data expansion script
- For format errors, check that the JSON/JSONL files are properly formatted
- Ensure the data directory structure matches the expected paths

### Optimization Issues

- **JSON Parsing Errors**: Ensure LM Studio correctly formats JSON responses
- **Low Accuracy**: Try increasing the number of training examples or iterations
- **Memory Issues**: Reduce batch sizes by using fewer examples per iteration
- **Theological Questions**: Check that Strong's IDs are properly formatted (H1234 or G5678)

## Additional Resources

- [DSPy Documentation](https://dspy.ai/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [LM Studio Documentation](https://lmstudio.ai/) 