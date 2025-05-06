# Model Validation Guidelines

## Overview

This document provides guidelines for validating machine learning models in the BibleScholarProject. These standards ensure all models meet quality requirements before deployment.

## Validation Metrics

All models must be evaluated using these core metrics:

1. **Accuracy**: Overall correctness of predictions
2. **Precision**: Correctness of positive predictions
3. **Recall**: Ability to find all positive instances
4. **F1 Score**: Harmonic mean of precision and recall
5. **Theological Accuracy**: Domain-specific accuracy for theological content

## Cross-Validation Requirements

For all model validation:

1. Use k-fold cross-validation (k=5 minimum)
2. Stratify splits for imbalanced datasets
3. Report mean and standard deviation of metrics
4. Hold out a final test set that is never used during training

Example:
```python
from sklearn.model_selection import StratifiedKFold
import numpy as np

def cross_validate_model(model, X, y, n_splits=5):
    """
    Perform stratified k-fold cross validation.
    
    Args:
        model: Model to validate
        X: Features
        y: Target labels
        n_splits: Number of CV splits
        
    Returns:
        dict: Metrics with mean and std
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    metrics = {
        'accuracy': [],
        'precision': [],
        'recall': [],
        'f1': [],
        'theological_accuracy': []
    }
    
    for train_idx, val_idx in skf.split(X, y):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        model.fit(X_train, y_train)
        preds = model.predict(X_val)
        
        # Calculate metrics
        metrics['accuracy'].append(accuracy_score(y_val, preds))
        metrics['precision'].append(precision_score(y_val, preds))
        metrics['recall'].append(recall_score(y_val, preds))
        metrics['f1'].append(f1_score(y_val, preds))
        metrics['theological_accuracy'].append(theological_accuracy(y_val, preds))
    
    # Calculate mean and std
    results = {}
    for metric, values in metrics.items():
        results[f'{metric}_mean'] = np.mean(values)
        results[f'{metric}_std'] = np.std(values)
    
    return results
```

## Theological Accuracy Validation

Theological accuracy is evaluated based on:

1. **Term Consistency**: Correct identification of theological terms
2. **Contextual Accuracy**: Correct interpretation within biblical context
3. **Doctrinal Accuracy**: Alignment with standard theological interpretations
4. **Cross-Reference Accuracy**: Proper linking of related passages

Example implementation:
```python
def theological_accuracy(y_true, y_pred, theological_terms=None):
    """
    Calculate theological accuracy score.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        theological_terms: List of critical theological terms to check
        
    Returns:
        float: Theological accuracy score (0-1)
    """
    if theological_terms is None:
        theological_terms = {
            "Elohim", "YHWH", "Adon", "Chesed", "Aman",
            "Theos", "Kyrios", "Christos", "Pneuma", "Pistis"
        }
    
    # Get samples containing theological terms
    theo_indices = [i for i, sample in enumerate(X) if any(term in sample for term in theological_terms)]
    
    if not theo_indices:
        return 1.0  # No theological terms to evaluate
    
    # Calculate accuracy only on samples with theological terms
    theo_y_true = [y_true[i] for i in theo_indices]
    theo_y_pred = [y_pred[i] for i in theo_indices]
    
    return accuracy_score(theo_y_true, theo_y_pred)
```

## Minimum Performance Requirements

Models must meet these minimum requirements:

| Model Type | Accuracy | F1 Score | Theological Accuracy |
|------------|----------|----------|----------------------|
| Classification | 0.85 | 0.83 | 0.90 |
| NER | 0.80 | 0.78 | 0.90 |
| Embedding | - | - | 0.85 |
| Generation | BLEU > 0.40 | - | 0.90 |

## Validation Documentation

All model validation must be documented with:

1. **Validation Report**: Detailed metrics and methodology
2. **Dataset Description**: Training, validation, and test sets
3. **Error Analysis**: Analysis of incorrect predictions
4. **Performance Graphs**: Learning curves and metric visualizations

Example validation report structure:
```python
def generate_validation_report(model_name, validation_results, dataset_info):
    """Generate a standardized validation report."""
    report = {
        "model_name": model_name,
        "timestamp": datetime.now().isoformat(),
        "metrics": validation_results,
        "dataset": dataset_info,
        "error_analysis": perform_error_analysis(),
        "theological_assessment": assess_theological_accuracy()
    }
    
    # Save report
    with open(f"reports/{model_name}_validation.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return report
```

## Domain-Specific Validation

### Named Entity Recognition

For NER models specifically evaluating biblical entities:

1. **Entity Types**: Evaluate for PERSON, LOCATION, DEITY, PEOPLE_GROUP
2. **Sacred Name Handling**: Special evaluation for divine names
3. **Ambiguous Entities**: Test with cases like "Spirit" (DEITY vs. common noun)

### Text Generation

For generative models:

1. **Theological Soundness**: Verify theological accuracy of generated content
2. **Citation Accuracy**: Check scripture references in generated text
3. **Contextual Relevance**: Ensure generated text is contextually appropriate

## Update History

- **2025-05-05**: Added theological accuracy examples
- **2025-04-10**: Added minimum performance requirements
- **2025-03-01**: Added domain-specific validation guidance
- **2025-02-01**: Initial version created 