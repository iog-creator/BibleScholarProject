# DSPy Training Data

This directory contains training data for DSPy language models used in the BibleScholarProject.

## Datasets

- `qa_dataset.jsonl` - Question-answering pairs for Bible verses and theological concepts
- `theological_terms_dataset.jsonl` - Examples featuring Hebrew theological terms like Elohim, YHWH, etc.
- `translation_dataset.jsonl` - Translation comparison examples
- `summarization_dataset.jsonl` - Bible passage summarization examples
- `web_interaction_dataset.jsonl` - API usage examples
- `user_interactions_dataset.jsonl` - Real user interactions with the system

## Generation and Management

This data is managed by the DSPy data collection system:

1. **Check status**: `make dspy-status`
2. **Refresh all data**: `make dspy-refresh`
3. **Generate specific datasets**: `make dspy-collect`
4. **Enhance with specialized examples**: `make dspy-enhance`

## Directory Structure

- `bible_corpus/` - Core Bible corpus and extraction data
- `dspy/` - DSPy-specific formatted data
- `.state.json` - Current database state hash and metadata

## Format

All datasets use the JSONL format, with one example per line. Each example includes:
- Input fields (like question, context)
- Output fields (like answer)
- Metadata (like references, theological notes)

## For Developers

When making changes to the database that affect Bible verses or theological terms, use `scripts/refresh_dspy_data.py refresh` to regenerate training data.

## Available Datasets

| Dataset | Description | Examples | Format |
|---------|-------------|----------|--------|
| `documentation_organization_dataset.jsonl` | Examples of documentation organization problems and solutions | 5 | `{"input": "problem", "output": "solution"}` |
| `documentation_organization_formatted.jsonl` | Formatted data for the documentation organizer | 5 | Custom DSPy format |
| `tvtms_parsing_examples.jsonl` | TVTMS parser examples | 6 | `{"input": "raw", "output": "parsed"}` |
| `evaluation_metrics.jsonl` | DSPy evaluation metrics | 7 | `{"metric_name": "name", "implementation": "code"}` |

## Model Metrics

The `metrics/` directory contains tracking data for trained DSPy models:

| Metrics File | Description |
|--------------|-------------|
| `documentation_organizer_metrics.jsonl` | Metrics for the documentation organizer model |
| `qa_model_metrics.jsonl` | Metrics for the Bible QA model |
| `theological_analyzer_metrics.jsonl` | Metrics for the theological term analyzer |

Each metrics file contains JSONL entries with:
- Performance metrics (accuracy, F1, etc.)
- Dataset version hashes
- Model parameters
- Timestamps and version numbers

## Usage

### Loading Datasets

```python
import json
import dspy

def load_examples(filepath):
    examples = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('//') or not line.strip():
                continue
            data = json.loads(line)
            example = dspy.Example(**data)
            examples.append(example)
    return examples

# Load documentation organization examples
documentation_examples = load_examples('data/processed/dspy_training_data/documentation_organization_dataset.jsonl')
```

### Data Generation

The datasets are generated and refreshed using:

```bash
# Check current status
python scripts/refresh_dspy_data.py status

# Force regeneration of all datasets
python scripts/refresh_dspy_data.py refresh

# Regenerate specific dataset types
python scripts/refresh_dspy_data.py refresh --type qa,theological
```

### Model Tracking

Track model metrics using:

```bash
# Record model metrics
python scripts/track_dspy_model_metrics.py record --model-name doc_organizer --metrics metrics.json

# Generate performance report
python scripts/track_dspy_model_metrics.py report --model-name doc_organizer
```

Or use the integrated tracking in optimization scripts:

```bash
# Train with automatic metrics tracking
python scripts/optimize_documentation_organizer.py --track-metrics
```

## Standards

1. All dataset files should:
   - Include comments at the top with generation date
   - Use consistent JSON field naming
   - Include appropriate metadata fields
   - Follow the prescribed format for the task

2. Versioning:
   - Dataset versions are tracked via file hashes in `.state.json`
   - Model versions are tracked in metrics files
   - Changes to datasets should be documented

3. Format validation:
   - Use the validation script to check dataset integrity
   - Ensure all required fields are present
   - Verify theological accuracy when applicable
