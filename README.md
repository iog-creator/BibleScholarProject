# Bible Scholar Project

A comprehensive Bible study and research tool leveraging artificial intelligence to explore theological concepts across different translations.

## Features

- Question answering about Bible content using advanced language models
- Cross-language theological term exploration
- Semantic search across Bible translations
- Lexicon integration with Strong's numbers
- Dynamic comparison of Bible translations
- DSPy-powered fine-tuned LLM for theological accuracy
- Advanced model optimization for 95%+ accuracy

## New Features - DSPy 2.6 Integration

We've enhanced the project with DSPy 2.6 features including:

- Advanced prompt optimization using the Teleprompter API
- Improved model accuracy with theological assertions
- MLflow integration for experiment tracking
- Real-world Bible datasets (HuggingFace and Bible corpus)
- Multi-turn conversation support with theological term handling
- Enhanced validation dataset with Strong's ID theological questions
- Additional training data sources from comprehensive Bible database
- BetterTogether and InferRules optimization for high-accuracy theological reasoning

## Training Data

The Bible QA system can be trained using multiple data sources:

- Core Bible QA dataset (verse questions and answers)
- Theological terms dataset with Strong's IDs
- Cross-language concept training with Hebrew, Greek, and Arabic
- Biblical proper names and relationships
- Multi-turn conversation examples

See [Additional Training Data](docs/features/additional_training_data.md) for details on utilizing all available data sources.

## Getting Started

### Requirements

The project requires:

- Python 3.9+
- PostgreSQL with pgvector extension
- LM Studio for local model inference
- MLflow for experiment tracking

### Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Install additional DSPy requirements: `pip install -r requirements-dspy.txt`
6. Configure environment variables in `.env` and `.env.dspy`

## Usage

### Bible Q&A Web Interface

```bash
# Start the web interface
python start_bible_qa_web.bat
```

Access the API at http://localhost:8000/api/bible-qa

### Vector Search Demo

```bash
# Start the vector search demo
python start_vector_search_web.bat
```

## Development

### Database Setup

```bash
# Setup database security
python setup_db_security.bat
# Verify database schema
python check_db_schema.py
```

### Training Models

```bash
# Train DSPy Bible QA model
python train_dspy_bible_qa.py
# Train semantic search model
python train_semantic_search_models.bat
```

### Model Optimization

```bash
# Start MLflow server
mlflow ui --host 127.0.0.1 --port 5000
# Optimize Bible QA model with BetterTogether
optimize_bible_qa.bat better_together
# Optimize Bible QA model with InferRules
optimize_bible_qa.bat infer_rules
```

### Validation

```bash
# Expand the validation dataset
python scripts/expand_validation_dataset.py --num-single 40 --num-multi 10
# Test the Bible QA system
python test_enhanced_bible_qa.py --batch-test --use-lm-studio
```

## Documentation

- [DSPy Integration](README_DSPY.md)
- [Semantic Search](README_VECTOR_SEARCH.md)
- [Bible Corpus Training](README_BIBLE_CORPUS_TRAINING.md)
- [Bible QA System](README_BIBLE_QA.md)
- [T5 Model Training](README_BIBLE_T5_TRAINING.md)
- [Dataset Validation Expansion](docs/features/dataset_validation_expansion.md)
- [Bible QA Optimization](docs/features/bible_qa_optimization.md)
- [Additional Training Data](docs/features/additional_training_data.md)

## License

This project is licensed under the MIT License - see the LICENSE file for details.