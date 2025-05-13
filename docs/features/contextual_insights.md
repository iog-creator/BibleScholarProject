# Contextual Insights Feature

This document provides a comprehensive overview of the Contextual Insights feature, which generates rich contextual information for Bible study using direct LM Studio chat completions (Qwen3-14B) via `query_lm_studio` in `contextual_insights_minimal.py`. DSPy-based modules and JSON patches are planned for future enhancements.

## Overview

The Contextual Insights feature allows users to select a specific Bible verse, topic, or text snippet as their area of focus and receive a comprehensive set of AI-generated insights to deepen their understanding. These insights include summaries, cross-references, theological term explanations, historical context, original language notes, and related entities (people, places).

The system uses minimal integration to call LM Studio directly for all insight types and leverages `bible_db` for primary data; semantic search layers will be added later.

## Architecture

The Contextual Insights feature follows a modular architecture:

1. **Focus Processing**: Parses and validates user input (verse reference, topic, or text snippet)
2. **Context Augmentation**: Enriches the primary focus with semantically similar passages
3. **Multi-Module Insight Generation**: Applies specialized modules for each insight type
4. **API Integration**: Exposes the functionality via a RESTful API endpoint

The system operates within the core DSPy framework, with each insight module implementing a specific DSPy signature.

## Components

### Core Classes

- **ContextualInsightsProgram**: Main DSPy module that orchestrates the process
- **FocusProcessor**: Processes different types of user focus (verse, topic, text snippet)
- **InsightGenerator**: Generates various insight categories based on processed focus
- **Insight-Specific Modules**: Specialized DSPy modules for each insight type

### Insight Types

1. **Summary**: Concise summary of the main focus, highlighting key themes and meanings
2. **Cross-References**: Related Bible passages with explanations of theological connections
3. **Theological Terms**: Key theological terms with definitions and contextual relevance
4. **Historical Context**: Cultural and historical background information
5. **Original Language Notes**: Analysis of key terms in the original Hebrew/Greek (for verses)
6. **Related Entities**: People and places relevant to the focus, with brief descriptions
7. **Translation Variants**: Multiple translations of the specified verse drawn from the primary `bible_db` (public domain sources like ASV, KJV, TAGNT, TAHOT), excluding licensed translations (e.g., ESV).

### API

The insights are accessible via a RESTful API endpoint:
```
POST /api/contextual_insights/insights
```

See the [API Reference](../reference/API_REFERENCE.md#contextual-insights-api) for detailed documentation.

## Usage Examples

### Getting Insights for a Bible Verse

```python
import requests
import json

# API endpoint
url = "http://localhost:5002/api/contextual_insights/insights"

# Request for a verse
data = {
    "type": "verse",
    "reference": "John 3:16",
    "translation": "KJV"
}

# Send the request
response = requests.post(url, json=data)
insights = response.json()

# Print the summary
print(f"Summary: {insights['insights']['summary']}")

# Print theological terms
print("\nTheological Terms:")
for term, definition in insights['insights']['theological_terms'].items():
    print(f"- {term}: {definition}")
```

### Getting Insights for a Topic

```python
# Request for a topic
data = {
    "type": "topic",
    "query_text": "Sermon on the Mount"
}

# Send the request
response = requests.post(url, json=data)
insights = response.json()

# Print the summary
print(f"Summary: {insights['insights']['summary']}")

# Print historical context
print(f"\nHistorical Context: {insights['insights']['historical_context']}")
```

### Getting Insights for a Text Snippet

```python
# Request for a text snippet
data = {
    "type": "text_snippet",
    "text": "Blessed are the poor in spirit, for theirs is the kingdom of heaven."
}

# Send the request
response = requests.post(url, json=data)
insights = response.json()

# Print the summary
print(f"Summary: {insights['insights']['summary']}")

# Print related entities
print("\nRelated People:")
for person in insights['insights']['related_entities']['people']:
    print(f"- {person['name']}: {person['description']}")
```

## Web Server

The Contextual Insights feature includes a dedicated web server:

```
python run_contextual_insights_web.py
```

Or use the provided batch file:
```
run_contextual_insights_web.bat
```

The server runs on port 5002 by default and exposes the API endpoints.

## Configuration

The feature is configured using environment variables in `.env.dspy`:

| Variable                    | Description                                                       | Default                               |
|-----------------------------|-------------------------------------------------------------------|---------------------------------------|
| LM_STUDIO_API_URL           | URL for the LM Studio API                                         | http://localhost:1234/v1              |
| LM_STUDIO_CHAT_MODEL        | Model name for LM Studio                                          | mistral-nemo-instruct-2407@q4_k_m     |
| LM_STUDIO_API_KEY           | API key for LM Studio                                             | sk-dummykeyforlocal                   |
| PGVECTOR_CONNECTION_STRING  | Connection string for PostgreSQL with pgvector                    | (Required for retrieval)              |
| PGVECTOR_TABLE_NAME         | Table name for verse embeddings                                   | (Required for retrieval)              |
| DATABASE_URL                | Postgres connection string for the primary `bible_db`             | (Required for translation_variants)   |
| BIBLE_DB_PATH               | Local path to an SQLite fallback `bible_db.sqlite` (optional)     | (Fallback if used)                    |
| CONTEXTUAL_INSIGHTS_PORT    | Port for the web server                                           | 5002                                  |
| PYTHONUTF8                  | Force Python to use UTF-8 encoding                                | 1 (Recommended)                       |

## Testing

Validate the Contextual Insights API with the provided test script covering multiple verses and translations:

```bash
# Runs tests for John 1:1, Genesis 1:1, Psalm 23:1 and verifies JSON structure and translation_variants
python scripts/test_contextual_insights.py
```

This script ensures:
- All required insight fields are present (`summary`, `theological_terms`, `cross_references`, `historical_context`, `original_language_notes`, `related_entities`, `translation_variants`).
- `translation_variants` contains only the public domain translations (`ASV`, `KJV`, `TAGNT`, `TAHOT`) and excludes licensed versions (e.g., `ESV`).

## Implementation Notes

<!-- Implementation Notes: minimal integration bypasses DSPy JSONAdapter and uses direct LM Studio calls; see `.cursor/rules/features/contextual_insights_integration.mdc` for guidance. -->

## Training and Optimization

The Contextual Insights modules can be optimized using DSPy's optimization tools:

1. Generate training examples in JSONL format:
   ```
   data/processed/dspy_training_data/contextual_insights/summary_examples.jsonl
   data/processed/dspy_training_data/contextual_insights/cross_reference_examples.jsonl
   ```

2. Use DSPy optimizers to refine the prompts:
   ```python
   from dspy.teleprompt import BootstrapFewShot
   
   # Load examples
   trainset = dspy.load_dataset("path/to/examples.jsonl")
   
   # Create optimizer
   bootstrapper = BootstrapFewShot(metric="exact_match")
   
   # Optimize the module
   optimized_module = bootstrapper.compile(module, trainset=trainset)
   
   # Save the optimized module
   dspy.save(optimized_module, "models/dspy/contextual_insights/optimized_module.dspy")
   ```

## Troubleshooting

Common issues and solutions:

1. **Hebrew/Greek character display issues**:
   - Set `PYTHONUTF8=1` in environment or when running scripts

2. **Empty or malformed JSON responses**:
   - Ensure the DSPy JSON patch is correctly applied
   - Check that LM Studio is running and accessible
   - Verify that the response_format is correctly set in API calls

3. **Missing semantic search results**:
   - Verify that `PGVECTOR_CONNECTION_STRING` and `PGVECTOR_TABLE_NAME` are correctly set
   - Ensure the database has verse embeddings loaded

4. **API endpoint not found or server fails to start**:
   - Check for errors in the Flask blueprint registration
   - Verify port availability (default is 5002)
   - Check that the API blueprint is properly registered with the app

5. **"No module named 'src'"**:
   - Ensure the working directory is set to the project root
   - Add the project root to PYTHONPATH if needed

## Related Documentation

- [LM Studio + DSPy Integration](./LM_STUDIO_DSPY_INTEGRATION.md)
- [DSPy Usage](./dspy_usage.md)
- [Vector Search](./semantic_search.md)
- [API Reference](../reference/API_REFERENCE.md) 