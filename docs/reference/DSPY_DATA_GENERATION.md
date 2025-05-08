# DSPy 2.6 Training Data Generation

This guide explains how to use the DSPy training data generation system for training Bible QA models with DSPy 2.6 features.

## Overview

The BibleScholarProject includes a comprehensive system for generating high-quality training data for DSPy 2.6 models. This system:

1. **Generates diverse training datasets**: QA pairs, theological term analysis, multi-turn conversations, etc.
2. **Tracks database state**: Automatically detects when data needs to be refreshed
3. **Integrates with ETL processes**: Training data is updated when Bible data changes
4. **Supports multi-turn conversations**: Special datasets for DSPy 2.6 conversation history

## Key Components

The system consists of several components:

- **`scripts/generate_dspy_training_data.py`**: Main data generation script
- **`scripts/refresh_dspy_data.py`**: Utility for checking status and refreshing data
- **`scripts/enhance_dspy_training.py`**: Adds specialized examples
- **`src/utils/dspy_collector.py`**: Core collection system
- **`data/processed/dspy_training_data/`**: Generated datasets

## Available Datasets

The system generates these datasets:

| Dataset | Purpose | Examples |
|---------|---------|----------|
| `qa_dataset.jsonl` | Basic question answering | ~1,000+ |
| `theological_terms_dataset.jsonl` | Hebrew theological term analysis | ~500+ |
| `translation_dataset.jsonl` | Translation comparison | ~100+ |
| `conversation_history_dataset.jsonl` | Multi-turn conversations | ~200+ |
| `summarization_dataset.jsonl` | Bible passage summarization | ~500+ |
| `web_interaction_dataset.jsonl` | API usage examples | ~100+ |

## Commands

### Check Status

```bash
make dspy-status
```

This shows:
- Current database state hash
- Last update timestamp
- Available data files
- Translation and theological term statistics

### Refresh Data

```bash
make dspy-refresh
```

This:
- Checks if database state has changed
- Regenerates all training data
- Updates the state file

### Add Custom Examples

```bash
make dspy-enhance
```

This adds specialized examples for:
- Theological assertions
- Multi-turn conversations
- Complex reasoning chains

## Using with DSPy 2.6

The data is designed to work with DSPy 2.6 features:

### Multi-turn Conversation History

```python
class BibleQASignature(dspy.Signature):
    """Signature for Bible Question Answering that supports conversation history."""
    context = dspy.InputField(desc="Biblical context or verse")
    question = dspy.InputField(desc="Question about the biblical context")
    history = dspy.InputField(desc="Previous conversation turns as a list of questions and answers", default=[])
    answer = dspy.OutputField(desc="Answer to the question based on the biblical context")
```

Example data from `conversation_history_dataset.jsonl`:

```json
{
  "context": "John 3:16",
  "question": "What happens to those who believe?",
  "history": [
    {"question": "What did God give?", "answer": "His one and only Son"},
    {"question": "Why?", "answer": "Because he loved the world"}
  ],
  "answer": "They will not perish but have eternal life"
}
```

### Theological Assertions

The datasets include examples that enforce theological assertions:

```python
# Using DSPy assertions
if "god" in question.lower() and not any(term in prediction.answer.lower() for term in ["god", "lord", "creator"]):
    dspy.Assert(
        condition=False,
        message="Answer must reference God when questions are about God."
    )
```

### MLflow Integration

The data generation system integrates with MLflow:

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("BibleQA")

with mlflow.start_run(run_name="dspy_data_generation"):
    mlflow.log_param("database_state_hash", current_hash)
    mlflow.log_param("dataset_sizes", {
        "qa": len(qa_pairs),
        "theological_terms": len(theological_terms),
        "conversation_history": len(conversation_history)
    })
```

## Advanced Usage

### Custom Dataset Generation

To generate a specific dataset type:

```bash
python scripts/refresh_dspy_data.py refresh --type qa,theological
```

### Adding Custom Examples

You can manually add examples to any dataset:

```python
from scripts.enhance_dspy_training import add_examples_to_jsonl

# Add conversation examples
examples = [
    {
        "context": "Genesis 1:1",
        "question": "What does this verse teach?",
        "answer": "God is the creator of everything",
        "history": [{"question": "First question", "answer": "First answer"}]
    }
]

add_examples_to_jsonl(examples, "conversation_history_dataset.jsonl")
```

### ETL Integration

The system integrates with ETL processes:

```python
from src.utils.dspy_collector import trigger_after_verse_insertion

# After inserting Bible verses
with conn.cursor() as cur:
    # Insert verses
    cur.execute(...)
    
# Trigger DSPy collection
trigger_after_verse_insertion(conn, translation_code)
```

## Troubleshooting

If you encounter issues:

1. **Database connection errors**: Check `.env` for correct database credentials
2. **Missing data files**: Run `make dspy-refresh` to regenerate all files
3. **Script errors**: Check `logs/dspy_data_generator.log` for details
4. **State file issues**: Delete `.state.json` and run refresh to regenerate 