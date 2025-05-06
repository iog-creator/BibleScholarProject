# DSPy Training System for BibleScholarProject

## Overview

The BibleScholarProject includes a sophisticated system for generating training data for machine learning models using [DSPy](https://dspy.ai/). This system collects high-quality examples from the Bible database to train AI models that can answer questions, summarize passages, analyze theological terms, and interact with the project's API and web interfaces.

## Key Components

The DSPy training system consists of:

1. **Collection System** (`src/utils/dspy_collector.py`): Tracks database state and triggers regeneration when needed
2. **Generation Script** (`scripts/generate_dspy_training_data.py`): Creates various training datasets
3. **Refresh Utility** (`scripts/refresh_dspy_data.py`): Command-line utility for checking status and manual refreshing
4. **Enhancement Script** (`scripts/enhance_dspy_training.py`): Adds specialized examples and fixes formatting issues
5. **User Interaction Logger** (`scripts/log_user_interactions.py`): Captures real user questions and solutions
6. **API Integration** (`src/api/lexicon_api.py`): Automatically logs real API interactions via decorators
7. **Web Integration** (`src/web_app.py`): Automatically logs web interface interactions via decorators
8. **Training Data Directory** (`data/processed/dspy_training_data/`): Stores generated JSONL files
9. **State Tracking File** (`.state.json`): Maintains database state hash and timestamp

## Generated Datasets

The system generates the following datasets:

| Dataset | Purpose | Example Count | Format |
|---------|---------|---------------|--------|
| `qa_dataset.jsonl` | Question-answering over Bible verses | 100+ | Context, question, answer |
| `theological_terms_dataset.jsonl` | Hebrew theological term analysis | 100+ | Term, context, analysis |
| `translation_dataset.jsonl` | Parallel translations comparison | 15+ | Source, target, metadata |
| `summarization_dataset.jsonl` | Bible passage summarization | 3+ | Passage, summary |
| `ner_dataset.jsonl` | Named entity recognition | 85+ | Tokens, tags |
| `web_interaction_dataset.jsonl` | API usage examples | 15+ | Query, action, parameters |
| `web_ui_interaction_dataset.jsonl` | Web interface interaction | 4+ | Steps, expected result |
| `problem_solution_dataset.jsonl` | Problem-solving examples | 4+ | Problem, solution, code |
| `evaluation_metrics.jsonl` | Custom DSPy metrics | 4+ | Metric implementation |
| `user_interactions_dataset.jsonl` | Real user interactions | Variable | Query, solution |

## Usage

### Checking Status

```bash
python scripts/refresh_dspy_data.py status
```

This command shows:
- Current database state hash
- Last update timestamp
- List of available data files with sizes
- Translation verse counts
- Theological term counts

### Refreshing Data

```bash
python scripts/refresh_dspy_data.py refresh
```

This command:
1. Calculates a new database state hash
2. Regenerates all training data files
3. Updates the state file

### Enhancing Data

```bash
python scripts/enhance_dspy_training.py
```

This script:
1. Adds specialized examples not automatically generated from the database
2. Fixes formatting issues in existing examples
3. Creates additional datasets for web UI interaction and problem-solving

### Logging User Interactions

The system automatically logs real user interactions from the API and web application. This happens through decorators applied to API endpoints and web routes.

You can also manually log interactions:

```bash
# Start with example interactions
python scripts/log_user_interactions.py

# Reset the log files (for testing)
python scripts/log_user_interactions.py --reset
```

To manually log specific interactions in Python code:

```python
# Log an API interaction
from scripts.log_user_interactions import log_api_interaction
log_api_interaction(
    endpoint="/api/lexicon/hebrew/H7225",
    method="GET",
    params={},
    response={"strongs_id": "H7225", "lemma": "רֵאשִׁית"},
    success=True
)

# Log a web interface interaction
from scripts.log_user_interactions import log_web_interaction
log_web_interaction(
    route="/bible/Genesis/1/1", 
    query_params={"show_strongs": "true"}, 
    response_type="verse_with_strongs"
)

# Log a question and answer
from scripts.log_user_interactions import log_question_answer
log_question_answer(
    question="What is the meaning of Elohim in Hebrew?",
    answer="Elohim (אֱלֹהִים) is the Hebrew word for 'God' or 'gods'. It's the plural form of Eloah, but is often used with singular verbs when referring to the one true God of Israel.",
    category="theological_term"
)

# Log a problem and solution with code example
from scripts.log_user_interactions import log_problem_solution
log_problem_solution(
    problem="How do I search for specific Hebrew words in the API?",
    solution="Use the /api/lexicon/search endpoint with the lang parameter set to 'hebrew'",
    code_example="""
    import requests
    
    response = requests.get("http://localhost:5000/api/lexicon/search", 
                           params={"q": "beginning", "lang": "hebrew"})
    results = response.json()
    """
)
```

## Integration with API and Web Application

### API Integration

The DSPy collection system automatically logs API requests via a decorator in `src/api/lexicon_api.py`:

```python
@app.route('/api/lexicon/hebrew/<strongs_id>', methods=['GET'])
@log_api_endpoint
def get_hebrew_entry(strongs_id):
    # API code...
```

Each API call is captured with:
- Endpoint path
- HTTP method
- Query parameters
- Response data
- Success status

### Web Application Integration

Web page visits are automatically logged via a decorator in `src/web_app.py`:

```python
@app.route('/lexicon/<lang>/<strongs_id>')
@log_web_request
def lexicon_entry(lang, strongs_id):
    # Route handler code...
```

Each web interaction is captured with:
- Route path
- Query parameters
- Response type

## Integration with Bible Loading Process

The DSPy collection system is automatically triggered whenever:

1. A new Bible translation is loaded
2. Hebrew theological terms are updated
3. Morphology data is modified

This integration is handled through hooks in the Bible loading scripts:

```python
# Example from load_kjv_bible.py
from src.utils import dspy_collector

# After loading verses
dspy_collector.trigger_after_verse_insertion(conn, 'KJV')
```

## Automatic Collection Mechanism

1. **State Tracking**: Generates a hash representing the current database state
2. **Change Detection**: Compares current hash with previous state
3. **Smart Regeneration**: Only regenerates when state changes
4. **Transaction Management**: Ensures data consistency during collection

## Example Data

### Question-Answering Example
```json
{
  "context": "In the beginning, God created the heavens and the earth.",
  "question": "Who created the heavens and the earth?",
  "answer": "God",
  "metadata": {
    "book": "Genesis",
    "chapter": 1,
    "verse": 1,
    "type": "factual"
  }
}
```

### User Interaction Example
```json
{
  "timestamp": "2025-05-05T20:11:58.463139",
  "type": "api_interaction",
  "endpoint": "/api/lexicon/hebrew/H7225",
  "method": "GET",
  "parameters": {},
  "response": {
    "strongs_id": "H7225",
    "lemma": "רֵאשִׁית",
    "transliteration": "rēʾšîṯ",
    "gloss": "beginning, chief"
  },
  "success": true,
  "formatted_query": "Make an API call to /api/lexicon/hebrew/H7225 with GET",
  "formatted_solution": "API response: {\"strongs_id\": \"H7225\", \"lemma\": \"רֵאשִׁית\", \"transliteration\": \"rēʾšîṯ\", \"gloss\": \"beginning, chief\"}"
}
```

### Problem-Solution Example
```json
{
  "timestamp": "2025-05-05T20:05:19.884467",
  "problem": "API returns 404 for /api/lexicon/greek/G25",
  "solution": "The Greek lexicon endpoint needs to be properly implemented. The Hebrew endpoint works but Greek is missing.",
  "code_example": "\n# Implementation for Greek lexicon API\n@app.route('/api/lexicon/greek/<strongs_id>', methods=['GET'])\ndef get_greek_lexicon_entry(strongs_id):\n    conn = get_db_connection()\n    try:\n        with conn.cursor(row_factory=dict_row) as cur:\n            cur.execute(\n                \"SELECT * FROM bible.greek_entries WHERE strongs_id = %s\",\n                (strongs_id,)\n            )\n            entry = cur.fetchone()\n            \n        if entry:\n            return jsonify(entry)\n        else:\n            return jsonify({\"error\": f\"No entry found for Strong's ID {strongs_id}\"}), 404\n    finally:\n        conn.close()\n",
  "diagnostic_steps": [
    "Checked API server logs - no Greek lexicon endpoint implemented",
    "Verified the database has Greek entries table",
    "Confirmed Hebrew endpoint works correctly"
  ],
  "metadata": {
    "issue_type": "user_reported",
    "has_code_solution": true
  }
}
```

## Using the Training Data

The generated datasets can be used with DSPy to train and optimize models:

```python
import dspy
import json
from pathlib import Path

# Load examples
def load_examples(filename):
    examples = []
    data_path = Path('data/processed/dspy_training_data') / filename
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('//') or not line.strip():
                continue
            examples.append(dspy.Example(**json.loads(line)))
    return examples

# Create a model
qa_examples = load_examples('qa_dataset.jsonl')
lm = dspy.OpenAI(model="gpt-3.5-turbo")

# Define a signature
class BibleQA(dspy.Signature):
    """Answer questions about Bible verses."""
    context = dspy.InputField(desc="The Bible verse or passage")
    question = dspy.InputField(desc="Question about the verse")
    answer = dspy.OutputField(desc="Answer to the question")

# Create a module
class BibleQAModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.qa_model = dspy.ChainOfThought(BibleQA)
    
    def forward(self, context, question):
        return self.qa_model(context=context, question=question)

# Optimize with DSPy
optimizer = dspy.teleprompt.SIMBA()
optimized_module = optimizer.optimize(
    BibleQAModule(),
    trainset=qa_examples[:80],
    devset=qa_examples[80:],
    metric=dspy.Accuracy()
)
```

## Troubleshooting

### Collection Not Triggering

If DSPy collection isn't triggering when expected:

1. Check the database connection is established correctly
2. Verify changes are being committed to the database
3. Ensure changes affect tables monitored in `get_db_state_hash()`
4. Check log files for errors: `logs/dspy_collector.log`

### Formatting Issues in Data

If you notice HTML artifacts or formatting issues:

1. Run the enhancement script: `python scripts/enhance_dspy_training.py`
2. Check the data generation script for proper HTML cleaning
3. Verify the source data doesn't contain unexpected formatting

### Missing Training Files

If training files are missing:

1. Check log files for generation errors
2. Verify the state file exists: `data/processed/dspy_training_data/.state.json`
3. Run manual refresh: `python scripts/refresh_dspy_data.py refresh`

### API Logging Not Working

If API interactions are not being logged:

1. Ensure the API server is running with the correct module: `python start_servers.py`
2. Check that the `@log_api_endpoint` decorator is applied to API routes
3. Verify the log directories exist and are writable

## Extending the System

### Adding New Dataset Types

To add a new dataset type:

1. Create a new generation function in `scripts/generate_dspy_training_data.py`
2. Call the function from the `main()` function
3. Update the README in the data directory

### Adding New Interaction Types

To log new types of user interactions:

1. Add a new logging function in `scripts/log_user_interactions.py`
2. Create a decorator for automatic logging if needed
3. Add the new interaction type to the appropriate dataset

### Customizing Tracking Logic

To modify what triggers regeneration:

1. Edit the `get_db_state_hash()` function in `src/utils/dspy_collector.py`
2. Add additional tables or fields to track
3. Update the hash generation logic

## Further Resources

- [DSPy Documentation](https://dspy.ai/)
- [DSPy Tutorials](https://dspy.ai/tutorials/rag/)
- [Cursor Rule for DSPy Usage](.cursor/rules/dspy_usage.mdc) 