# Validation Dataset Expansion

This document explains how to expand the validation dataset for the Bible QA system to ensure thorough testing of complex theological and multi-turn conversation capabilities.

## Overview

The validation dataset (`qa_dataset_val.jsonl`) is used to evaluate the performance of DSPy-trained models such as the Mistral NeMo 12B. To ensure thorough testing, the dataset should include:

1. Single-turn theological questions with Strong's IDs
2. Multi-turn conversation scenarios to test context retention
3. Diverse Bible verses from multiple translations

The `expand_validation_dataset.py` script generates new examples by sourcing data from:
- PostgreSQL Bible database (`bible_db`)
- Theological terms dataset (`theological_terms_dataset.jsonl`)
- Bible corpus dataset (`combined_bible_corpus_dataset.json`)

## Installation & Prerequisites

Before using the script, ensure the following prerequisites are met:

1. **PostgreSQL Database**: 
   - The Bible database should be properly set up with:
     - `bible.verses` table containing verse data
     - `bible.hebrew_entries` and `bible.greek_entries` tables with Strong's IDs

2. **Required Packages**:
   ```
   psycopg2-binary>=2.9.5
   python-dotenv>=1.0.0
   ```

3. **Environment Configuration**:
   - Create a `.env` file with database credentials:
   ```env
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=bible_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   ```

## Cursor Rules and Standards

When working with the validation dataset expansion functionality, follow the guidelines in the `.cursor/rules/validation_dataset_expansion.mdc` rule, which specifies:

1. **Database Access Patterns**:
   - Use `get_db_connection()` from `src.database.secure_connection` for read-only operations
   - Implement fallback mechanisms for database connection errors
   - Handle disconnections gracefully

2. **Theological Term Handling**:
   - Use standardized Strong's ID format (H#### for Hebrew, G#### for Greek)
   - Include proper transliteration and definitions from lexicon tables
   - Handle null values with appropriate defaults
   - Cross-reference with `docs/rules/theological_terms.md`

3. **Testing Requirements**:
   - Use standard test commands with proper arguments
   - Log validation results to both console and MLflow
   - Track metrics for factual accuracy and theological term recognition

The cursor rule ensures consistency across all validation dataset expansions.

## Integration with MLflow

The validation dataset expansion is fully integrated with MLflow for tracking experiment metrics:

```python
import mlflow
from src.dspy_programs.enhanced_bible_qa import EnhancedBibleQA
from src.utils.mlflow_utils import setup_mlflow_tracking

# Setup MLflow tracking
setup_mlflow_tracking()

# Initialize the Bible QA system with newly expanded dataset
qa_system = EnhancedBibleQA(model_path="models/dspy/bible_qa_mistral.dspy", use_lm_studio=True)

# Start an MLflow run
with mlflow.start_run(run_name="validation_dataset_test"):
    # Set parameters
    mlflow.log_param("model", "mistral-nemo-12b")
    mlflow.log_param("dataset", "qa_dataset_val.jsonl")
    mlflow.log_param("validation_size", 200)  # Number of examples in validation set
    
    # Run batch test on validation dataset
    results = qa_system.batch_test("data/processed/bible_training_data/qa_dataset_val.jsonl")
    
    # Log metrics
    mlflow.log_metric("overall_accuracy", results["overall_accuracy"])
    mlflow.log_metric("theological_accuracy", results["theological_accuracy"])
    mlflow.log_metric("multi_turn_accuracy", results["multi_turn_accuracy"])
    
    # Log artifacts
    mlflow.log_artifact("results.json")
```

### Accessing MLflow Results

To view the MLflow experiment results:

1. Start the MLflow UI:
   ```bash
   mlflow ui --port 5000
   ```

2. Open a browser to `http://localhost:5000`

3. Navigate to the "Experiments" tab to see validation dataset test results

## Running Enhanced Tests

After expanding the validation dataset, run the enhanced Bible QA tests:

```bash
# Run the standard test with LM Studio integration
python test_enhanced_bible_qa.py --batch-test --use-lm-studio

# Test with specific limits and model path
python test_enhanced_bible_qa.py --batch-test --use-lm-studio --limit 10 --model-path "models/dspy/bible_qa_mistral.dspy"
```

## Usage

### Basic Usage

Run the script with default parameters:

```bash
python scripts/expand_validation_dataset.py
```

This will:
- Add 40 single-turn theological questions
- Add 10 multi-turn conversation scenarios
- Save to the default output file: `data/processed/bible_training_data/qa_dataset_val.jsonl`

### Advanced Usage

Customize the script behavior with the following arguments:

```bash
python scripts/expand_validation_dataset.py \
    --output-file "data/processed/bible_training_data/qa_dataset_val.jsonl" \
    --theological-file "data/processed/dspy_training_data/theological_terms_dataset.jsonl" \
    --corpus-file "data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json" \
    --num-single 40 \
    --num-multi 10 \
    --verbose
```

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--output-file` | Path to output JSONL file | `data/processed/bible_training_data/qa_dataset_val.jsonl` |
| `--theological-file` | Path to theological terms dataset | `data/processed/dspy_training_data/theological_terms_dataset.jsonl` |
| `--corpus-file` | Path to corpus dataset | `data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json` |
| `--num-single` | Number of single-turn questions to generate | 40 |
| `--num-multi` | Number of multi-turn conversations to generate | 10 |
| `--verbose` | Enable verbose logging | False |

## Example Output

### Single-Turn Theological Questions

```json
{
  "context": "John 1:1: In the beginning was the Word, and the Word was with God, and the Word was God.",
  "question": "What is the significance of 'logos' (G3056) in John 1:1?",
  "answer": "In John 1:1, 'logos' (G3056) refers to the divine Word, specifically Jesus Christ as the revelation of God. The term indicates that Jesus is the ultimate expression and communication of God to humanity, existing from eternity and sharing in God's divine nature.",
  "history": [],
  "metadata": {
    "type": "theological",
    "strongs_id": "G3056",
    "translation": "KJV"
  }
}
```

### Multi-Turn Conversations

```json
{
  "context": "Psalms 136:1: O give thanks unto the LORD; for he is good: for his mercy endureth for ever.",
  "question": "How is 'chesed' (H2617) specifically used in Psalms 136:1 and how does it relate to 'emunah' (H530)?",
  "answer": "In Psalms 136:1, 'chesed' (H2617) is used to emphasize God's covenant loyalty, lovingkindness and mercy that endures forever. This relates to 'emunah' (H530) because faithfulness is the foundation of God's covenant relationships. Together, these terms highlight important theological concepts of God's character as both merciful and faithful to His promises.",
  "history": [
    {
      "question": "What does 'chesed' (H2617) mean in Biblical Hebrew?",
      "answer": "'chesed' (H2617) means covenant loyalty, steadfast love, loving-kindness, or mercy. It represents God's faithful love toward His people that is rooted in covenant relationship and extends beyond simple obligation to deep compassion."
    }
  ],
  "metadata": {
    "type": "multi-turn",
    "strongs_id": ["H2617", "H530"],
    "translation": "KJV"
  }
}
```

## Integration with DSPy

The validation dataset expansion is specifically designed to work with DSPy-based Bible QA systems. To evaluate your DSPy model on the expanded dataset:

```python
import dspy
from dspy.evaluate import Evaluate

# Load your DSPy model
model = dspy.load("models/dspy/bible_qa_mistral.dspy")

# Create evaluator for the validation dataset
evaluator = Evaluate(
    devset="data/processed/bible_training_data/qa_dataset_val.jsonl",
    metric="theological_accuracy",  # Custom metric for theological questions
    num_threads=4
)

# Run evaluation
results = evaluator(model)
print(f"Model accuracy: {results:.2%}")
```

### MLflow Integration

You can track evaluation metrics using MLflow:

```python
import mlflow

with mlflow.start_run(run_name="bible_qa_validation"):
    results = evaluator(model)
    
    # Log the aggregated score
    mlflow.log_metric("accuracy", results)
    
    # Log detailed metrics by category
    mlflow.log_metric("theological_accuracy", results_by_type.get("theological", 0))
    mlflow.log_metric("multi_turn_accuracy", results_by_type.get("multi-turn", 0))
```

## Error Handling & Logging

The script includes robust error handling with fallbacks:

1. **Database Connection**:
   - Tries `secure_connection` from the project
   - Falls back to direct psycopg2 connection if not available

2. **Data Sources**:
   - Uses database as primary source for theological terms
   - Falls back to JSONL files if database access fails

3. **Logging**:
   - All operations are logged to `logs/expand_validation_dataset.log`
   - Use `--verbose` for detailed debugging information

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Check `.env` file has correct credentials
   - Ensure PostgreSQL is running and accessible
   - Verify that the `bible_db` database exists with required tables

2. **Missing Strong's Data**:
   - Ensure Hebrew and Greek lexicon tables are properly populated
   - Check that the theological terms dataset exists and is properly formatted

3. **Output Format Issues**:
   - Check for JSON formatting errors in the output file
   - Ensure all required fields are present in the output examples

### Runtime Checks

The script performs several runtime checks:
- Verifies database connectivity
- Ensures enough theological terms are available
- Confirms proper Bible verse availability
- Creates output directories if they don't exist

## Related Resources

- [Bible QA System Documentation](../README_BIBLE_QA.md)
- [DSPy Integration Guide](../README_DSPY.md)
- [Theological Terms Processing](../rules/theological_terms.md)
- [Vector Search Implementation](../README_VECTOR_SEARCH.md)

## Change History

| Date | Version | Changes |
|------|---------|---------|
| 2023-05-07 | 1.0 | Initial implementation |
| 2023-05-08 | 1.1 | Added Strong's ID verification |
| 2023-07-15 | 1.2 | Enhanced multi-turn conversation support |
| 2023-11-23 | 2.0 | Integrated with DSPy evaluation system |
| 2024-05-08 | 2.1 | Added MLflow integration and cursor rule documentation | 