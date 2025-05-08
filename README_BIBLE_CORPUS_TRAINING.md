# Bible QA Training with Non-Synthetic Data

This guide explains how to use the scripts for training a Bible QA system using non-synthetic training data and DSPy, with database and vector search integration.

## Overview

This system builds upon the existing Bible corpus dataset by integrating additional non-synthetic data sources:
- Massively Parallel Bible Corpus
- Public domain lexicons
- Theological terms and concepts
- Multi-turn conversation examples

The complete pipeline includes:
1. Data integration and preparation
2. Model training using DSPy
3. Testing the trained model with database retrieval
4. Deploying an API with vector search integration

## Requirements

- Python 3.10+
- DSPy 2.6+
- PostgreSQL database with pgvector extension
- LM Studio for generating embeddings
- Required packages: `pip install dspy-ai scikit-learn flask flask-cors psycopg2-binary requests`
- API keys configured in `.env.dspy` (for OpenAI or other API-based LMs)

## Database Configuration

Create a `.env` file in the project root with the following variables:
```
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

The database should have the following tables:
- `bible.verses`: Contains Bible verses from various translations
- `bible.verse_embeddings`: Contains vector embeddings for each verse
- `bible.hebrew_lexicon`: Contains Hebrew lexicon entries
- `bible.greek_lexicon`: Contains Greek lexicon entries

## Scripts

The following scripts are included:

### 1. Data Integration Script

`scripts/integrate_non_synthetic_data.py`

This script integrates various non-synthetic data sources into the Bible corpus dataset.

```bash
python scripts/integrate_non_synthetic_data.py
```

The script:
- Attempts to download the Massively Parallel Bible Corpus
- Generates QA pairs for theological concepts
- Generates QA pairs for Hebrew and Greek terms
- Generates multi-turn conversation examples
- Integrates with the existing Bible corpus dataset

The expanded dataset is saved to:
```
data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json
```

### 2. Training Script

`scripts/train_with_huggingface.py`

This script trains a Bible QA model using DSPy and teacher-student optimization.

```bash
python scripts/train_with_huggingface.py --lm gpt-3.5-turbo --teacher-model gpt-4
```

Key parameters:
- `--lm`: Base language model for DSPy (default: `gpt-3.5-turbo`)
- `--teacher-model`: Teacher model for optimization (default: `gpt-4`)
- `--dataset-path`: Path to the dataset file (default: `data/processed/dspy_training_data/bible_corpus/dspy/combined_bible_corpus_dataset.json`)
- `--output-dir`: Directory to save the compiled model (default: `models/dspy/bible_qa_huggingface`)
- `--max-examples`: Maximum number of examples to use (default: 100)

When using local Hugging Face models, modify as follows:
```bash
python scripts/train_with_huggingface.py --lm google/flan-t5-small --teacher-model meta-llama/Llama-2-7b-hf
```

### 3. Database Retrieval Utility

`scripts/bible_retrieval_utils.py`

This script provides utilities for retrieving context from the database.

```bash
python scripts/bible_retrieval_utils.py "What does Genesis 1:1 say?"
```

Key features:
- Bible verse retrieval by reference
- Strong's lexicon entry lookup
- Semantic search using pgvector
- Automatic context retrieval based on question content

### 4. Testing Script

`scripts/test_bible_qa.py`

This script tests a trained Bible QA model with sample questions and database retrieval.

```bash
python scripts/test_bible_qa.py --model-path models/dspy/bible_qa_huggingface/compiled_model.json --use-retrieval
```

Key parameters:
- `--model-path`: Path to the compiled model file
- `--lm`: Language model to use for inference (default: `gpt-3.5-turbo`)
- `--question`: Single question to test (optional)
- `--context`: Context for the question (optional, will be retrieved if not provided)
- `--use-retrieval`: Enable automatic context retrieval from the database
- `--test-file`: Path to JSON file with test questions (optional)
- `--output`: Path to save test results (optional)

Example with a single question and automatic retrieval:
```bash
python scripts/test_bible_qa.py --question "What does Genesis 1:1 say?" --use-retrieval
```

### 5. API Deployment Script

`scripts/deploy_bible_qa_api.py`

This script deploys an API for the Bible QA model with database and vector search integration.

```bash
python scripts/deploy_bible_qa_api.py --model-path models/dspy/bible_qa_huggingface/compiled_model.json --port 5050
```

Key parameters:
- `--model-path`: Path to the compiled model file
- `--lm`: Language model to use for inference (default: `gpt-3.5-turbo`)
- `--host`: Host to run the API on (default: `0.0.0.0`)
- `--port`: Port to run the API on (default: `5050`)
- `--disable-retrieval`: Disable automatic context retrieval (off by default)

API Endpoints:
- `POST /api/bible-qa`: Main QA endpoint
- `GET /api/reference`: Look up Bible verses by reference
- `GET /api/lexicon`: Look up Strong's lexicon entries
- `GET /api/vector-search`: Perform semantic search
- `GET /health`: Health check endpoint

#### Example usage of the main QA endpoint:
```bash
curl -X POST http://localhost:5050/api/bible-qa \
  -H "Content-Type: application/json" \
  -d '{"question": "What does Genesis 1:1 say?"}'
```

#### Example usage of reference lookup:
```bash
curl "http://localhost:5050/api/reference?book=Genesis&chapter=1&verse=1"
```

#### Example usage of lexicon lookup:
```bash
curl "http://localhost:5050/api/lexicon?strongs_id=H430"
```

#### Example usage of vector search:
```bash
curl "http://localhost:5050/api/vector-search?query=creation&translation=KJV&limit=5"
```

## Complete Training Pipeline

Here's a step-by-step guide to running the complete pipeline:

1. **Prepare the dataset**:
   ```bash
   python scripts/integrate_non_synthetic_data.py
   ```

2. **Train the model**:
   ```bash
   python scripts/train_with_huggingface.py
   ```

3. **Test the model with retrieval**:
   ```bash
   python scripts/test_bible_qa.py --use-retrieval
   ```

4. **Deploy the API**:
   ```bash
   python scripts/deploy_bible_qa_api.py
   ```

## Vector Search Setup

This system uses LM Studio to generate embeddings and pgvector for storing and searching them.

### Setting up LM Studio

1. Download and install LM Studio from https://lmstudio.ai/
2. Open LM Studio and go to the Local Server tab
3. Load the `text-embedding-nomic-embed-text-v1.5@q8_0` model
4. Start the server (should run on http://localhost:1234)

### Setting up pgvector

1. Install the pgvector extension in your PostgreSQL database:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. Create the verse embeddings table:
   ```sql
   CREATE TABLE bible.verse_embeddings (
     verse_id INTEGER PRIMARY KEY REFERENCES bible.verses(verse_id),
     embedding vector(768)
   );
   ```

3. Create an index for faster searches:
   ```sql
   CREATE INDEX ON bible.verse_embeddings USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```

## Customization

### Using Local Models

To use local Hugging Face models instead of API-based models:

1. Install additional requirements:
   ```bash
   pip install transformers torch accelerate
   ```

2. Update the model parameters:
   ```bash
   python scripts/train_with_huggingface.py --lm google/flan-t5-small --teacher-model meta-llama/Llama-2-7b-hf
   ```

### Customizing the Retrieval Process

You can modify the `retrieve_context_for_question` function in `scripts/bible_retrieval_utils.py` to:
- Change the search strategies
- Adjust context length limits
- Add more sophisticated context merging

### Building a Web Interface

A simple web interface can be built using HTML, CSS, and JavaScript to interact with the API:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Bible QA</title>
    <script>
        async function askQuestion() {
            const question = document.getElementById("question").value;
            const response = await fetch("http://localhost:5050/api/bible-qa", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question })
            });
            const data = await response.json();
            document.getElementById("answer").textContent = data.answer;
            document.getElementById("context").textContent = data.context;
        }
    </script>
</head>
<body>
    <h1>Bible QA System</h1>
    <input id="question" type="text" placeholder="Ask a Bible question">
    <button onclick="askQuestion()">Ask</button>
    <h2>Answer:</h2>
    <div id="answer"></div>
    <h3>Context:</h3>
    <div id="context" style="font-size: smaller;"></div>
</body>
</html>
```

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:
1. Verify your `.env` file contains the correct credentials
2. Ensure PostgreSQL is running and accessible
3. Check that the required tables and extensions exist

### LM Studio Connection Issues

If the system can't connect to LM Studio:
1. Ensure LM Studio is running and the server is started
2. Verify the correct embedding model is loaded
3. Check the API endpoint is accessible at http://localhost:1234

### Vector Search Performance

If vector search is slow:
1. Ensure you have created the IVFFlat index on the embedding column
2. Consider increasing the number of lists in the index for larger databases
3. Limit the number of results returned by vector search

### DSPy API Keys

If you're using API-based models like OpenAI, ensure your `.env.dspy` file contains:
```
OPENAI_API_KEY=your_key_here
```

## Next Steps

- **Improve Dataset**: Continue expanding the dataset with more diverse examples
- **Optimize Models**: Experiment with different teacher and student models
- **Enhance Retrieval**: Implement hybrid search combining vector and keyword approaches
- **Improve UI**: Build a more sophisticated web interface with advanced features 