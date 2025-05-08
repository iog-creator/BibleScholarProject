type: feature
title: pgVector Semantic Search
description: Guidelines for working with pgvector semantic search functionality in the BibleScholarProject
globs:
  - "src/utils/vector_search.py"
  - "src/database/connection.py"
  - "src/dspy_programs/semantic_search.py"
  - "vector_search_web.py"
alwaysApply: false
---

# pgVector Semantic Search Implementation

This guide outlines the implementation of semantic search capabilities in the BibleScholarProject using PostgreSQL's pgvector extension.

## Core Components

1. **Database Structure**
   - The extension `vector` must be enabled in PostgreSQL
   - Embeddings are stored in `bible.verse_embeddings` table with 768-dimensional vectors
   - Includes columns: `verse_id`, `book_name`, `chapter_num`, `verse_num`, `translation_source`, `embedding`
   - Uses the IVFFlat index type for efficient similarity search

2. **Configuration**
   - **All configuration** must be through environment variables, never hardcoded
   - Primary configuration variables:
     - `LM_STUDIO_API_URL`: URL for LM Studio API (default: "http://localhost:1234/v1")
     - `LM_STUDIO_EMBEDDING_MODEL`: Embedding model name (default: "text-embedding-nomic-embed-text-v1.5@q8_0")
     - `LM_STUDIO_CHAT_MODEL`: Chat model for DSPy components (default depends on local installation)
   - Database connection variables:
     - `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
   - Configuration in `.env` and `.env.dspy` files (dspy takes precedence for DSPy operations)

3. **Embedding Generation** (`src/utils/generate_verse_embeddings.py`)
   - Uses LM Studio API with model specified in environment variables
   - Processes verses in batches of 50 for optimal GPU utilization
   - Stores embeddings in the database with proper vector formatting
   - Creates appropriate index on the verse_embeddings table

4. **Search Implementation** (`src/utils/vector_search.py`)
   - `search_verses_by_semantic_similarity`: Search by query text
   - `get_verse_by_reference`: Get specific verse by reference
   - Cosine similarity for semantic matching with `<=>` operator
   - Proper error handling and connection management

5. **DSPy Integration** (`src/dspy_programs/semantic_search.py`)
   - Advanced semantic search with query expansion and result reranking
   - Multi-hop reasoning for complex theological queries
   - Integration with LM Studio through environment variables
   - Configuration through `.env.dspy` for specialized model settings

## Testing and Usage

### Python Scripts

Use the standalone test scripts to verify vector search functionality:
```python
python -m src.utils.test_vector_search
python test_pgvector_search.py  # Custom test script
```

### Web Demo Applications

1. **Basic Vector Search Demo**:
```bash
python vector_search_web.py  # Runs on port 5050
```

2. **DSPy-Enhanced Search Demo**:
```bash
python -m src.utils.dspy_search_demo  # Runs on port 5060
```

Access web interfaces at http://127.0.0.1:5050 and http://127.0.0.1:5060

## Implementation Details

1. **Vector Format for PostgreSQL**
   - Use square brackets format for vector arrays
   - Properly cast vectors to PostgreSQL vector type with `::vector`
   - Example: `embedding_array = "[0.1, 0.2, ...]"` then use `%s::vector` in SQL

2. **Search Algorithms**
   - Using cosine similarity for semantic search with `<=>` operator
   - Optimizing with proper indexing for faster search

3. **Performance**
   - Batch processing with 50 verses per batch
   - Using GPU acceleration via LM Studio
   - Created IVFFlat index with 100 lists for optimal search performance

4. **Environment Variable Management**
   - Always use environment variables from `.env` and `.env.dspy`
   - Never hardcode model names, API endpoints, or credentials
   - Provide sensible defaults for all environment variable lookups
   - Example: `os.getenv("VARIABLE_NAME", "default_value")`

## Troubleshooting

1. **LM Studio Connection Issues**
   - Ensure LM Studio is running at the URL specified in your environment variables
   - Verify the model specified in `LM_STUDIO_EMBEDDING_MODEL` is loaded
   - Check LM Studio API errors with direct API calls using the environment variables

2. **Search Query Issues**
   - Verify the correct book names (e.g., "Psalms" not "Psalm")
   - Check database connectivity and table existence
   - Confirm embedding vectors are properly formatted
   
3. **Database Connection Issues**
   - Try both `get_db_connection()` and `get_secure_connection(mode='read')` for reading
   - Check for proper error handling in vector search functions
   - Verify database credentials in environment variables 