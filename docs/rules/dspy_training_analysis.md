type: feature
title: DSPy Training Analysis
description: Guidelines for analyzing DSPy training results and MLflow experiment tracking in the Bible Scholar Project
globs:
  - "src/dspy_programs/*.py"
  - "train_dspy_bible_qa.py"
  - "test_*dspy*.py"
alwaysApply: false
---

# DSPy Training Analysis Guidelines

## Overview

This rule provides guidelines for analyzing DSPy model training results, interpreting metrics, and utilizing MLflow for experiment tracking in the Bible Scholar Project.

## MLflow Experiment Tracking

### 1. Accessing MLflow UI

To view experiment results:

```bash
mlflow ui
# Access at http://localhost:5000
```

### 2. Experiment Structure

MLflow experiments are organized as follows:

1. **Runs**: Each training session or evaluation is recorded as a run
2. **Parameters**: Configuration settings for the run (model, dataset, etc.)
3. **Metrics**: Performance measurements (accuracy, F1 score, etc.)
4. **Artifacts**: Saved models, logs, and evaluation results

### 3. Key Metrics

When analyzing DSPy Bible QA models, focus on these metrics:

1. **Correctness**: Percentage of factually correct answers
2. **Theological Accuracy**: Correct interpretation of theological concepts
3. **Reference Accuracy**: Correct citation of Bible references
4. **Verification Rate**: Percentage of answers verified by database

## Dataset Analysis

### 1. Dataset Composition

The Bible Scholar Project includes several datasets:

1. **Combined Bible Corpus**: 2000+ QA examples in JSON format
   - Path: `data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json`

2. **Theological Terms Dataset**: 100+ theological term examples in JSONL format
   - Path: `data/processed/dspy_training_data/theological_terms_dataset.jsonl`

3. **Training/Validation Split**: 80/20 split for model evaluation
   - Training: `data/processed/dspy_training_data/bible_corpus/dspy/train_dataset.json`
   - Validation: `data/processed/dspy_training_data/bible_corpus/dspy/validation_dataset.json`

### 2. Data Quality Assessment

When analyzing dataset quality, consider:

1. **Question Distribution**: Ensure coverage across Bible books and theological topics
2. **Answer Completeness**: Verify answers contain accurate, complete information
3. **Reference Coverage**: Check for proper Bible reference formatting
4. **Theological Depth**: Assess coverage of key theological concepts

## Model Performance Analysis

### 1. DSPy Module Evaluation

For each module in the pipeline:

1. **Reference Extractor**: Accuracy in identifying Bible references
2. **Theological Term Extractor**: Precision in identifying theological terms
3. **QA Module**: Quality and accuracy of generated answers
4. **Verifier**: Accuracy in verifying answers against the database

### 2. Error Analysis

Common error patterns to investigate:

1. **Reference Extraction Errors**: Missed or incorrect Bible references
2. **Theological Misinterpretations**: Incorrect understanding of theological concepts
3. **Context Limitations**: Failure to use provided context effectively
4. **Verification Failures**: Errors in database verification process

### 3. Improvement Strategies

Based on error analysis, consider these improvements:

1. **Prompt Optimization**: Refine prompts for better module performance
2. **Example Selection**: Choose better few-shot examples for specific error cases
3. **Pipeline Modification**: Adjust module sequence or add new verification steps
4. **Database Integration**: Improve database lookup for better context

## Optimizer Evaluation

### 1. Comparing Optimizers

The project supports multiple DSPy optimizers:

1. **BootstrapFewShot**: Uses existing examples to bootstrap optimization
2. **GRPO**: Gradient-based optimization
3. **SIMBA**: Optimization through parameter search

Compare these metrics across optimizers:

1. **Performance Improvement**: Increase in accuracy over baseline
2. **Training Efficiency**: Time and computational resources required
3. **Generalization**: Performance on diverse question types

### 2. Hyperparameter Analysis

For each optimizer, analyze the impact of hyperparameters:

1. **Number of Examples**: Impact of few-shot example count
2. **Temperature**: Effect on answer diversity and accuracy
3. **Max Tokens**: Impact on answer completeness
4. **Optimization Steps**: Diminishing returns analysis

## Integration Testing

### 1. End-to-End Evaluation

Evaluate the complete pipeline with:

```bash
python test_enhanced_bible_qa.py --batch-test --output-file results.json
```

Analyze the following in test results:

1. **Overall Accuracy**: Percentage of correctly answered questions
2. **Processing Time**: Average time to answer questions
3. **Verification Rate**: Percentage of answers verified by database
4. **Error Distribution**: Types and frequencies of errors

### 2. Comparative Analysis

Compare performance across:

1. **Model Variants**: Different DSPy-optimized models
2. **Translations**: Performance across Bible translations (KJV, ASV, etc.)
3. **Question Types**: Performance on different question categories
4. **Context Length**: Impact of context size on answer quality

## MLflow Best Practices

### 1. Run Naming Convention

Use consistent naming for MLflow runs:

```python
with mlflow.start_run(run_name=f"bible_qa_{model_type}_{date_string}"):
    # Training or evaluation code
```

### 2. Parameter Logging

Log all relevant parameters:

```python
mlflow.log_param("model_type", model_type)
mlflow.log_param("optimizer", optimizer_name)
mlflow.log_param("num_examples", num_examples)
mlflow.log_param("dataset_version", dataset_version)
```

### 3. Metric Logging

Log both aggregate and detailed metrics:

```python
# Aggregate metrics
mlflow.log_metric("accuracy", accuracy)
mlflow.log_metric("verification_rate", verification_rate)

# Per-question metrics for detailed analysis
for i, result in enumerate(results):
    mlflow.log_metric(f"question_{i}_accuracy", result["score"])
```

### 4. Artifact Management

Save important artifacts:

```python
# Save model
mlflow.dspy.log_model(optimized_model, "model")

# Save evaluation results
mlflow.log_table(results_table, "results.json")

# Save example outputs
with open("example_outputs.txt", "w") as f:
    f.write(examples_text)
mlflow.log_artifact("example_outputs.txt")
```

## Troubleshooting

### 1. Common Issues

1. **Missing Dependencies**: Ensure all required packages are installed
2. **Database Connection**: Verify database connection for lookups
3. **Model Loading**: Check for correct model path and format
4. **MLflow Server**: Ensure MLflow server is running for tracking

### 2. Debug Logging

Enable detailed logging for troubleshooting:

```python
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dspy_training_debug.log"),
        logging.StreamHandler()
    ]
)
```

## Implementation Examples

### 1. Basic Training Analysis

```python
import mlflow
import json
from pathlib import Path

# Load results
with open("results.json", "r") as f:
    results = json.load(f)

# Calculate success metrics
success_count = sum(1 for r in results if "error" not in r)
verified_count = sum(1 for r in results if "error" not in r and 
                    r.get("verification", {}).get("is_consistent", False))
accuracy = success_count / len(results)
verification_rate = verified_count / len(results)

print(f"Accuracy: {accuracy:.2f}")
print(f"Verification Rate: {verification_rate:.2f}")
```

### 2. Error Analysis Script

```python
from collections import Counter

# Categorize errors
error_categories = Counter()

for result in results:
    if "error" in result:
        error_categories["processing_error"] += 1
    elif not result.get("verification", {}).get("is_consistent", False):
        error_categories["verification_failure"] += 1
    elif not result.get("references"):
        error_categories["reference_extraction_failure"] += 1
    elif not result.get("theological_terms") and "theological" in result["question"].lower():
        error_categories["term_extraction_failure"] += 1

print("Error Distribution:")
for category, count in error_categories.most_common():
    print(f"  {category}: {count} ({count/len(results):.2%})")
```

## References

1. **DSPy Documentation**: https://dspy.ai/
2. **MLflow Documentation**: https://mlflow.org/docs/latest/index.html
3. **Bible Scholar Project README**: README_DSPY.md
4. **Enhanced Bible QA Documentation**: docs/rules/enhanced_bible_qa.md 