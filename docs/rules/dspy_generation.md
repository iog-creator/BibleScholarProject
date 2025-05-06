# DSPy Training Data Generation Guidelines

## Overview

This document provides guidelines for generating training data for DSPy in the BibleScholarProject. DSPy is used for AI assistance with biblical research queries and autonomous web interface interactions.

## Data Storage Standards

DSPy training data should be stored in the following locations:

- **Primary Data Storage**: `data/processed/dspy_training_data/`
- **Test Data Storage**: `tests/data/processed/dspy_training_data/`

## Dataset Types

The project uses these standard DSPy training dataset types:

1. **Question-Answering (QA)**: `qa_dataset.jsonl`
2. **Theological Terms Analysis**: `theological_terms_dataset.jsonl`
3. **Named Entity Recognition (NER)**: `ner_dataset.jsonl`  
4. **Web Interaction**: `web_interaction_dataset.jsonl`
5. **Evaluation Metrics**: `evaluation_metrics.jsonl`

## File Format Standards

All DSPy training data must be in JSONL format with the following requirements:

1. Each line must be a valid JSON object
2. UTF-8 encoding must be used
3. Comment lines must start with `//`
4. Each file must have a schema comment at the beginning

Example:
```jsonl
// Schema: {"context": "str", "question": "str", "answer": "str", "metadata": {"book": "str", "chapter": "int", "verse": "int", "type": "str"}}
{"context": "In the beginning God created the heavens and the earth.", "question": "Who created the heavens and the earth?", "answer": "God", "metadata": {"book": "Genesis", "chapter": 1, "verse": 1, "type": "factual"}}
```

## Data Generation Process

### Generation Script

Use the standard generation script:
```bash
python scripts/generate_dspy_training_data.py
```

### Batch Processing Requirement

Always use batch processing for efficiency:

```python
def process_in_batches(items, batch_size=100):
    """Process items in batches for efficiency."""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_results = process_batch(batch)
        results.extend(batch_results)
    return results
```

### Critical Theological Term Validation

All data generation must validate the presence of critical theological terms:

```python
def validate_theological_terms(conn):
    """Validate that critical theological terms meet minimum requirements."""
    critical_terms = {
        "H430": {"name": "Elohim", "min_count": 2600},
        "H3068": {"name": "YHWH", "min_count": 6000},
        "H113": {"name": "Adon", "min_count": 335},
        "H2617": {"name": "Chesed", "min_count": 248},
        "H539": {"name": "Aman", "min_count": 100}
    }
    
    # Validation implementation...
```

## Data Quality Requirements

### Theological Accuracy

All generated examples must be theologically accurate:

1. Scripture references must be correct
2. Theological term definitions must match lexicon entries
3. Cross-references must be valid

### Data Distribution

Each dataset must have appropriate distribution:

1. **Book Coverage**: All books of the Bible must be represented
2. **Testament Balance**: Include both Old and New Testament examples
3. **Topic Diversity**: Cover a range of theological topics

### Data Cleaning

Always apply these data cleaning steps:

1. Remove HTML and XML tags from text
2. Normalize whitespace
3. Handle special characters consistently
4. Verify Unicode is properly encoded

Example:
```python
def clean_text(text):
    """Clean text for DSPy training data."""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Handle special characters
    text = text.replace('&quot;', '"').replace('&amp;', '&')
    
    return text
```

## Using DSPy Training Data

### Loading Data

Load DSPy examples with this pattern:

```python
import dspy
import json

def load_dspy_dataset(file_path):
    """Load DSPy dataset from JSONL file."""
    examples = []
    with open(file_path) as f:
        for line in f:
            # Skip comment lines
            if line.startswith('//') or not line.strip():
                continue
            # Parse JSON line into DSPy example
            example = dspy.Example(**json.loads(line))
            examples.append(example)
    return examples

# Load the dataset
trainset = load_dspy_dataset('data/processed/dspy_training_data/qa_dataset.jsonl')
```

### Model Training

Use this pattern for optimizing DSPy models:

```python
from dspy.teleprompt import SIMBA

# Define custom metrics if needed
def theological_accuracy(prediction, reference):
    # Implementation...
    pass

# Create optimizer with custom metric
optimizer = SIMBA(metric=theological_accuracy)

# Optimize the model
optimized_model = optimizer.optimize(
    model=base_model,
    trainset=trainset,
    devset=devset,
    max_rounds=5
)
```

## Update History

- **2025-05-05**: Added theological validation requirements
- **2025-04-15**: Added data cleaning guidelines
- **2025-03-10**: Added batch processing requirement
- **2025-02-01**: Initial version created 