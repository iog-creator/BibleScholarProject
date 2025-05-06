# Semantic Search in BibleScholarProject

This document provides detailed information about the semantic search implementation in the BibleScholarProject using PostgreSQL's pgvector extension.

## Overview

Semantic search enables users to find relevant Bible verses based on meaning rather than exact keyword matches. This is particularly useful for Biblical research, as it can surface conceptually related passages that might not share the same vocabulary.

## Technical Implementation

### Prerequisites

1. **PostgreSQL with pgvector extension**
   - The pgvector extension must be installed and enabled in your PostgreSQL database
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **LM Studio for embeddings**
   - The implementation uses LM Studio's API to generate embeddings
   - Default model: `text-embedding-nomic-embed-text-v1.5@q8_0:2`
   - LM Studio should be running on `http://127.0.0.1:1234` (configurable via .env)

### Database Structure

The implementation uses a dedicated table in the Bible schema:

```sql
CREATE TABLE bible.verse_embeddings (
    id SERIAL PRIMARY KEY,
    verse_id INTEGER REFERENCES bible.verses(id) ON DELETE CASCADE,
    book_name TEXT NOT NULL,
    chapter_num INTEGER NOT NULL,
    verse_num INTEGER NOT NULL,
    translation_source TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_verse_embeddings_vector 
ON bible.verse_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

### Key Components

1. **Embedding Generation** (`src/utils/generate_verse_embeddings.py`)
   - Retrieves all verses from the database
   - Processes verses in batches of 50 for optimal GPU utilization
   - Generates embeddings using LM Studio's API
   - Stores the embeddings in the `bible.verse_embeddings` table
   - Creates an index for efficient similarity search

2. **Vector Search API** (`src/api/vector_search_api.py`)
   - Provides endpoints for semantic search functionality
   - `/api/vector-search`: Find verses semantically related to a query
   - `/api/similar-verses`: Find verses similar to a reference verse
   - `/api/compare-translations`: Compare different translations of a verse

3. **Demo Application** (`src/utils/vector_search_demo.py`)
   - Standalone web interface for testing semantic search
   - Compares results against traditional keyword search
   - Runs on http://localhost:5050

4. **Test Script** (`src/utils/test_vector_search.py`)
   - Tests the vector search functionality directly
   - Useful for debugging and verification

## Usage

### Generating Embeddings

Run the embedding generation script to process all verses and store their embeddings:

```bash
python -m src.utils.generate_verse_embeddings
```

This is a one-time operation (unless verse content changes). The script will:
- Delete any existing embeddings for the specified translations
- Process all verses in batches
- Create the necessary index for efficient searching

### Using the API

The API endpoints can be accessed from your web application:

1. **Semantic Search**
   ```
   GET /api/vector-search?q=your search query&translation=KJV&limit=10
   ```

2. **Similar Verses**
   ```
   GET /api/similar-verses?book=John&chapter=3&verse=16&translation=KJV&limit=10
   ```

3. **Compare Translations**
   ```
   GET /api/compare-translations?book=John&chapter=3&verse=16
   ```

### Running the Demo

Launch the standalone demo application:

```bash
python -m src.utils.vector_search_demo
```

Then open http://localhost:5050 in your browser to test and compare semantic search with traditional keyword search.

## Performance Considerations

1. **Batch Processing**
   - Process verses in batches (default: 50) for optimal GPU utilization
   - This significantly improves embedding generation performance

2. **Indexing**
   - The `ivfflat` index type is used for efficient similarity searches
   - Adjust the `lists` parameter based on your dataset size (default: 100)

3. **Vector Formatting**
   - Ensure proper formatting of vectors in PostgreSQL queries
   - Always use the correct format with square brackets

## Examples

### Finding Conceptually Similar Verses

The semantic search can find verses with similar meaning, even if they don't share the same words:

Query: "The wages of sin is death"

Keyword search might only find Romans 6:23, but semantic search can find related concepts about sin and death throughout the Bible.

### Comparing Translations

Semantic search can help identify how different translations express the same concept:

```
GET /api/compare-translations?book=John&chapter=3&verse=16
```

This returns different translations of the verse, allowing for comparison of language and expression. 