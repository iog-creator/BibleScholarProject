# DSPy Training Data for BibleScholarProject

This directory contains training data files for DSPy-based AI model development in the BibleScholarProject.

## File Listing and Contents

- `qa_dataset.jsonl`: 104 examples
- `summarization_dataset.jsonl`: 3 examples
- `translation_dataset.jsonl`: 16 examples
- `theological_terms_dataset.jsonl`: 100 examples
- `ner_dataset.jsonl`: 86 examples
- `web_interaction_dataset.jsonl`: 13 examples
- `evaluation_metrics.jsonl`: 2 examples
- `tvtms_parsing_examples.jsonl`: (TVTMS versification mapping examples) examples
- `versification_parser_schema_issues.jsonl`: (Versification parser issues) examples

## Schema

Each file is a JSONL file (one JSON object per line) with task-specific fields:

### Question-Answering (QA)
```json
{
  "context": "Bible verse text",
  "question": "Question about the verse",
  "answer": "Answer to the question",
  "metadata": {"book": "Genesis", "chapter": 1, "verse": 1}
}
```

### Summarization
```json
{
  "passage": "Bible passage text",
  "summary": "Summary of the passage",
  "metadata": {"book": "Genesis", "chapter": 1, "verses": [1, 2]}
}
```

### Translation
```json
{
  "source": "Original language text",
  "target": "Translated text",
  "metadata": {"book": "Genesis", "chapter": 1, "verse": 1, "source_language": "Hebrew", "target_language": "English"}
}
```

### Theological Terms
```json
{
  "term": {"word": "אלהים", "strongs_id": "H430", "lemma": "אלהים", "gloss": "God"},
  "context": {"verse_text": "In the beginning God created...", "book": "Genesis", "chapter": 1, "verse": 1},
  "analysis": {"theological_meaning": "Elohim", "importance": "Core theological term"}
}
```

### Named Entity Recognition
```json
{
  "tokens": ["In", "the", "beginning", "God", "created"],
  "tags": ["O", "O", "O", "DEITY", "O"],
  "metadata": {"book": "Genesis", "chapter": 1, "verse": 1}
}
```

### Web Interaction
```json
{
  "query": "Find verses containing YHWH",
  "action": "search_database",
  "parameters": {"book": "Genesis", "term": "YHWH", "strongs_id": "H3068"},
  "expected_response_format": {"results": [{"reference": "Gen 2:4", "text": "..."}]},
  "metadata": {"interaction_type": "database_query"}
}
```

### Evaluation Metrics
```json
{
  "task": "bible_qa",
  "metric_name": "theological_accuracy",
  "metric_implementation": "def theological_accuracy(prediction, reference): ...",
  "metadata": {"metric_type": "accuracy", "theological_focus": true}
}
```

## Using with DSPy

```python
import dspy
import json

# Basic loading of examples
with open('data/processed/dspy_training_data/qa_dataset.jsonl') as f:
    trainset = [dspy.Example(**json.loads(line)) for line in f if not line.startswith('//') and line.strip()]

# Using DSPy for model optimization
from dspy.teleprompt import SIMBA
optimizer = SIMBA(metric="theological_accuracy")
optimized_model = optimizer.optimize(model, trainset=trainset)
```

## Optimization and Autonomous Interface Interaction

The `web_interaction_dataset.jsonl` contains examples specifically designed for training models to interact with web interfaces. Combined with DSPy's optimization capabilities, this allows for training autonomous agents that can:

1. Parse user queries related to biblical content
2. Determine the appropriate API action to take
3. Extract the correct parameters from the query
4. Format and validate the response

### Example DSPy Agent Setup

```python
class BibleSearchAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.query_parser = dspy.ChainOfThought("context, query -> action, parameters")
        
    def forward(self, query):
        # Parse the query to determine action and parameters
        parsed = self.query_parser(context="Biblical research assistant", query=query)
        
        # Execute the appropriate action
        if parsed.action == "search_database":
            results = search_bible_database(**parsed.parameters)
            return {"results": results}
        elif parsed.action == "lookup_strongs":
            definition = lookup_strongs_entry(**parsed.parameters)
            return {"definition": definition}
        # ... other actions
```

## Generation

Generated on 2025-05-05 19:53:46
To regenerate this data, run `python scripts/generate_dspy_training_data.py`
