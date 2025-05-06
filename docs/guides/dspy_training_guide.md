# DSPy Training Data Guide for BibleScholarProject

This document provides comprehensive guidance on generating, using, and extending DSPy training data for the BibleScholarProject's AI assistance capabilities.

*This document is complemented by the [dspy_generation](.cursor/rules/standards/dspy_generation.mdc) cursor rule.*

## Overview

The BibleScholarProject uses DSPy to train AI models that can assist with biblical research, theological queries, and autonomous web interface interactions. Training data is stored in JSONL format in the `data/processed/dspy_training_data` directory.

## Dataset Categories

### 1. Question-Answering (QA)

Dataset file: `qa_dataset.jsonl`

This dataset contains question-answer pairs about Bible verses, with proper context. It's designed to train models to answer factual and theological questions about biblical content.

Example format:
```json
{
  "context": "In the beginning God created the heavens and the earth.",
  "question": "Who created the heavens and the earth?",
  "answer": "God",
  "metadata": {"book": "Genesis", "chapter": 1, "verse": 1, "type": "factual"}
}
```

### 2. Theological Terms Analysis

Dataset file: `theological_terms_dataset.jsonl`

This dataset focuses specifically on critical theological terms such as Elohim, YHWH, Adon, Chesed, and Aman. It provides context, lexical information, and theological analysis.

Example format:
```json
{
  "term": {"word": "אלהים", "strongs_id": "H430", "lemma": "אלהים", "gloss": "God"},
  "context": {"verse_text": "In the beginning God created...", "book": "Genesis", "chapter": 1, "verse": 1},
  "analysis": {"theological_meaning": "Elohim", "importance": "Core theological term with expected 2,600+ occurrences"}
}
```

### 3. Named Entity Recognition (NER)

Dataset file: `ner_dataset.jsonl`

This dataset contains tagged tokens for identifying named entities in biblical texts, with special focus on distinguishing between DEITY and PERSON entities.

Example format:
```json
{
  "tokens": ["In", "the", "beginning", "God", "created"],
  "tags": ["O", "O", "O", "DEITY", "O"],
  "metadata": {"book": "Genesis", "chapter": 1, "verse": 1}
}
```

### 4. Web Interaction

Dataset file: `web_interaction_dataset.jsonl`

This dataset trains models to interpret user queries, extract parameters, and formulate appropriate API calls for web interface interaction.

Example format:
```json
{
  "query": "Find verses containing YHWH in Genesis",
  "action": "search_database",
  "parameters": {"book": "Genesis", "term": "YHWH", "strongs_id": "H3068"},
  "expected_response_format": {"results": [{"reference": "Gen 2:4", "text": "..."}]},
  "metadata": {"interaction_type": "database_query"}
}
```

### 5. Evaluation Metrics

Dataset file: `evaluation_metrics.jsonl`

This dataset provides specialized evaluation metrics for assessing the quality of model outputs, particularly for theological accuracy.

Example format:
```json
{
  "task": "bible_qa",
  "metric_name": "theological_accuracy",
  "metric_implementation": "def theological_accuracy(prediction, reference): ...",
  "metadata": {"metric_type": "accuracy", "theological_focus": true}
}
```

## Generating Training Data

### Running the Generator

To generate fresh DSPy training data:

```bash
python scripts/generate_dspy_training_data.py
```

This script connects to the database, extracts relevant information, and formats it into the appropriate JSONL files in the `data/processed/dspy_training_data` directory.

### Critical Requirements

1. **Theological Term Integrity**: All data generation must validate the presence of critical theological terms:
   - Elohim (H430): Minimum 2,600 occurrences
   - YHWH (H3068): Minimum 6,000 occurrences
   - Adon (H113): Minimum 335 occurrences
   - Chesed (H2617): Minimum 248 occurrences
   - Aman (H539): Minimum 100 occurrences

2. **Batch Processing**: Generation must use batch processing for efficiency:
   ```python
   def process_in_batches(items, batch_size=100):
       results = []
       for i in range(0, len(items), batch_size):
           batch = items[i:i+batch_size]
           batch_results = process_batch(batch)
           results.extend(batch_results)
       return results
   ```

3. **Quality Control**: All generated data must adhere to the schema defined in the README.md file in the output directory.

## Using with DSPy

### Basic Loading

Load DSPy examples like this:

```python
import dspy
import json

with open('data/processed/dspy_training_data/qa_dataset.jsonl') as f:
    trainset = [dspy.Example(**json.loads(line)) for line in f if not line.startswith('//') and line.strip()]
```

### Model Optimization

Optimize models using DSPy's optimization capabilities:

```python
from dspy.teleprompt import SIMBA

# Define a custom metric function if needed
def theological_accuracy(prediction, reference):
    # Add implementation that checks theological accuracy
    pass

# Create optimizer with the metric
optimizer = SIMBA(metric=theological_accuracy)

# Optimize the model
optimized_model = optimizer.optimize(base_model, trainset=trainset, devset=devset)
```

### Creating Web Interface Agents

Implement autonomous web interface agents:

```python
class BibleSearchAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.query_parser = dspy.ChainOfThought("context, query -> action, parameters")
        
    def forward(self, query):
        # Parse query to determine action and parameters
        parsed = self.query_parser(context="Biblical research assistant", query=query)
        
        # Execute the appropriate action
        if parsed.action == "search_database":
            results = search_bible_database(**parsed.parameters)
            return {"results": results}
        elif parsed.action == "lookup_strongs":
            definition = lookup_strongs_entry(**parsed.parameters)
            return {"definition": definition}
        # Add other actions as needed
```

## Extending Training Data

### Adding New Categories

1. Create a new generation function in `scripts/generate_dspy_training_data.py`
2. Update the main function to call your new generator
3. Add the new dataset to the README.md template

### Improving Existing Categories

To improve an existing category:

1. Review the current examples for quality and theological accuracy
2. Modify the generator function to include more diverse examples
3. Add new example types that address identified weaknesses
4. Ensure all critical theological terms are properly represented

## Best Practices

1. **Theological Verification**: Always verify that theological terms are correctly represented and that answers align with scholarly biblical interpretation.
2. **Consistent Formatting**: Maintain consistent JSON formatting across all dataset files.
3. **Metadata Inclusion**: Always include metadata fields for traceability and filtering.
4. **Cross-Language Support**: Include examples across different translations when possible.

## Integration with Semantic Search

The DSPy training system integrates closely with the semantic search capabilities:

1. **Vector-Enhanced Examples**: Use embedding vectors to find semantically similar verses for training examples.
2. **Theological Term Boosting**: Prioritize examples containing critical theological terms.
3. **Multilingual Support**: Generate examples across different language translations.

See [Semantic Search](../features/semantic_search.md) for more details on how the vector search capabilities enhance DSPy training data generation.

## Related Documentation

- [Theological Terms](../features/theological_terms.md) - Theological term definitions and processing
- [Database Schema](../reference/DATABASE_SCHEMA.md) - Database structure information
- [API Reference](../reference/API_REFERENCE.md) - API endpoints for data access

## Modification History

| Date | Change | Author |
|------|--------|--------|
| 2025-05-06 | Moved to guides directory and updated cross-references | BibleScholar Team |
| 2025-04-20 | Added integration with semantic search section | BibleScholar Team |
| 2025-03-15 | Added best practices section | BibleScholar Team |
| 2025-02-01 | Initial DSPy training guide | BibleScholar Team | 