# Bible Scholar Project

A modern, AI-powered Bible study and research platform for exploring scripture, theology, and original languages across multiple translations.

## Project Overview

Bible Scholar Project integrates advanced language models (via LM Studio), a robust Postgres database, and a modular API to deliver rich contextual insights, semantic search, and lexicon data for Bible study. The system is designed for extensibility, accuracy, and transparency, with a focus on theological term mapping and translation comparison.

## Key Features

- **Contextual Insights API**: Generate summaries, cross-references, theological term explanations, historical context, original language notes, and related entities for verses, topics, or text snippets.
- **Translation Variants**: Compare KJV, ASV, TAGNT, TAHOT (excludes ESV by default) for any verse.
- **Lexicon Integration**: Strong's number mapping, word-level data, and theological term linking for Hebrew and Greek.
- **Semantic Search**: pgvector-powered search across Bible translations and topics.
- **LM Studio Integration**: Local LLM inference for insights and normalization.
- **DSPy/MLflow**: Model optimization and experiment tracking (optional, for advanced users).
- **Comprehensive Testing**: Integration tests for all API features and translation validation.
- **Documentation System**: Centralized, versioned docs with change history and project rules.

## Quickstart

### Requirements
- Python 3.9+
- PostgreSQL with pgvector extension
- LM Studio (local LLM server)
- MLflow (optional, for model optimization)

### Installation
```bash
# Clone the repository
$ git clone https://github.com/iog-creator/BibleScholarProject.git
$ cd BibleScholarProject

# Create and activate a virtual environment
$ python -m venv venv
$ source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
$ pip install -r requirements.txt
$ pip install -r requirements-dspy.txt

# Configure environment variables
$ cp .env.example .env
$ cp .env.example.dspy .env.dspy
# Edit .env and .env.dspy as needed
```

### Database Setup
See `docs/guides/system_build_guide.md` for full instructions.

## Usage

### Start LM Studio
- Download and run LM Studio (see https://lmstudio.ai/)
- Ensure it is running at `http://localhost:1234/v1`

### Start the Contextual Insights API
```bash
$ python src/api/contextual_insights_api.py
```

### Example API Request
```bash
curl -X POST http://localhost:5002/api/contextual_insights/insights \
  -H "Content-Type: application/json" \
  -d '{"type": "verse", "reference": "John 1:1", "translation": "KJV"}'
```

### Example Response
```json
{
  "input": {"type": "verse", "reference": "John 1:1", "translation": "KJV"},
  "insights": {
    "summary": "...",
    "theological_terms": {"Theos": "God"},
    "cross_references": [...],
    "historical_context": "...",
    "original_language_notes": [...],
    "related_entities": {"people": [...], "places": [...]},
    "translation_variants": [...],
    "lexical_data": [...]
  },
  "processing_time_seconds": 12.3
}
```

## Testing

Run all integration tests (ensure LM Studio and API are running):
```bash
pytest tests/integration/test_contextual_insights.py -v
```

## Documentation
- All documentation is in the `docs/` directory.
- See `docs/known_issues.md` for current data gaps and issues.
- See `docs/roadmaps/contextual_insights_feature_roadmap.md` for feature plans.
- Project rules and standards are in `.cursor/rules/`.

## Contribution
- Please review and follow the documentation and code standards in `docs/` and `.cursor/rules/`.
- Use integration tests to validate changes.
- Update documentation and add change history for all major changes.
- For questions or contributions, open an issue or pull request on GitHub.

## License
MIT License. See LICENSE file for details.

## Attribution
- Bible data from public domain and licensed sources (see `STEPBible-Data/README.md`)
- LM Studio: https://lmstudio.ai/