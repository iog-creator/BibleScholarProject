# Bible Semantic Search

This document provides comprehensive documentation for the semantic search capabilities in the BibleScholarProject using PostgreSQL's pgvector extension.

*This document is complemented by the [pgvector_semantic_search](../../.cursor/rules/pgvector_semantic_search.mdc) cursor rule.*

## Overview

The BibleScholarProject implements semantic search for Bible verses using vector embeddings stored in PostgreSQL with the pgvector extension. This enables:

1. Finding verses similar to a text query
2. Finding verses similar to a specific reference verse
3. Comparing translations of the same verse
4. Exploring thematic connections between different parts of the Bible
5. Integrating semantic search with lexical and morphological data

## Required Models

For semantic search functionality, these LM Studio models must be loaded:

1. **Embedding Model**: `text-embedding-nomic-embed-text-v1.5@q8_0` 
   - Required for generating vector embeddings
   - Used by `src/utils/generate_verse_embeddings.py`

2. **Chat Model**: `darkidol-llama-3.1-8b-instruct-1.2-uncensored` (or similar LLaMa model)
   - Used for DSPy semantic search enhancements
   - Required for query expansion and result reranking

3. **T5 Model**: `gguf-flan-t5-small`
   - Used for Bible QA functionality that builds on semantic search
   - Required for the integrated Bible QA system

The application automatically checks if these models are loaded at startup. 
See [DSPy Model Management](../guides/dspy_model_management.md) for details on model verification and loading.

## Technical Implementation

### Database Schema

The semantic search feature relies on the following database schema:

```sql
CREATE TABLE bible.verse_embeddings (
    verse_id INTEGER PRIMARY KEY,
    book_name VARCHAR(50) NOT NULL,
    chapter_num INTEGER NOT NULL,
    verse_num INTEGER NOT NULL,
    translation_source VARCHAR(10) NOT NULL,
    embedding vector(768) NOT NULL
);

CREATE INDEX ON bible.verse_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### Configuration

All configuration for semantic search is managed through environment variables:

| Environment Variable | Description | Default Value |
|---------------------|-------------|---------------|
| LM_STUDIO_API_URL | URL for LM Studio API | http://localhost:1234/v1 |
| LM_STUDIO_EMBEDDING_MODEL | Model used for embeddings | text-embedding-nomic-embed-text-v1.5@q8_0 |
| LM_STUDIO_CHAT_MODEL | Model used for DSPy components | darkidol-llama-3.1-8b-instruct-1.2-uncensored |
| LM_STUDIO_COMPLETION_MODEL | Model used for T5 fine-tuning | gguf-flan-t5-small |
| POSTGRES_HOST | PostgreSQL host | localhost |
| POSTGRES_PORT | PostgreSQL port | 5432 |
| POSTGRES_DB | Database name | bible_db |
| POSTGRES_USER | Database user | postgres |
| POSTGRES_PASSWORD | Database password | postgres |

**Note**: These variables can be found in `.env` and `.env.dspy` files, with `.env.dspy` taking precedence for DSPy operations.

### Embedding Generation

Embeddings are generated using:
- LM Studio API with the model specified in `LM_STUDIO_EMBEDDING_MODEL`
- Text processed in batches of 50 for optimal GPU utilization
- 768-dimensional vector embeddings

Implementation in `src/utils/generate_verse_embeddings.py`:

```python
def generate_embeddings(verses, batch_size=50):
    """Generate embeddings for verses in batches."""
    all_embeddings = []
    
    for i in range(0, len(verses), batch_size):
        batch = verses[i:i+batch_size]
        texts = [v['verse_text'] for v in batch]
        
        # Generate embeddings using LM Studio API
        response = requests.post(
            f"{os.getenv('LM_STUDIO_API_URL')}/embeddings",
            headers={"Content-Type": "application/json"},
            json={"model": os.getenv("LM_STUDIO_EMBEDDING_MODEL"), "input": texts}
        )
        
        # Process response
        if response.status_code == 200:
            embeddings_data = response.json()
            for j, embedding in enumerate(embeddings_data['data']):
                all_embeddings.append({
                    'verse_id': batch[j]['id'],
                    'embedding': embedding['embedding']
                })
    
    return all_embeddings
```

### Model Verification

The semantic search system verifies model availability at startup to prevent runtime errors:

```python
def verify_lm_studio_model(model_name):
    """
    Verify if a specific model is available in LM Studio and attempt to load it if not.
    
    Args:
        model_name (str): The model to check for.
        
    Returns:
        bool: True if the model is available or successfully loaded, False otherwise.
    """
    try:
        response = requests.get(f"{lm_studio_api}/models")
        if response.status_code == 200:
            available_models = response.json().get("data", [])
            model_loaded = any(model.get("id") == model_name for model in available_models)
            
            if model_loaded:
                logger.info(f"Model '{model_name}' is available")
                return True
            else:
                logger.warning(f"Model '{model_name}' not found in loaded models")
                # Attempt to load the model
                # ...
        # ...
    # ...
```

### DSPy Integration

The system uses DSPy for advanced semantic search capabilities:

1. **Query Expansion**: Expands user queries with related theological concepts
2. **Result Reranking**: Reranks search results for better relevance
3. **Multi-hop Reasoning**: Connects related biblical topics for complex queries

The DSPy components are initialized with the LM Studio model specified in `LM_STUDIO_CHAT_MODEL`:

```python
def _init_dspy(self):
    """Initialize DSPy components."""
    try:
        # Configure DSPy
        lm_studio_api = os.getenv("LM_STUDIO_API_URL", "http://127.0.0.1:1234/v1")
        lm = dspy.LM(
            model_type="openai",
            model=os.environ.get("LM_STUDIO_CHAT_MODEL", "gguf-flan-t5-small"),
            api_base=lm_studio_api,
            api_key="dummy"  # LM Studio doesn't need a real key
        )
        dspy.configure(lm=lm)
        
        # Initialize DSPy modules
        self.query_expander = dspy.Predict(BibleQueryExpansion)
        self.reranker = dspy.Predict(BibleVerseReranker)
        self.topic_hopper = dspy.Predict(TopicHopping)
```

### Supported Translations

The system supports embeddings for these translations:

- King James Version (KJV)
- American Standard Version (ASV)
- Tagged Hebrew Old Testament (TAHOT)
- Tagged Greek New Testament (TAGNT)
- English Standard Version (ESV) - sample only

## Usage

### Demo Applications

Two demo applications are provided:

1. **Basic Vector Search**: `python -m src.utils.vector_search_demo` (port 5050)
2. **DSPy-Enhanced Search**: `python -m src.utils.dspy_search_demo` (port 5060)

### API Endpoints

The semantic search API provides these endpoints:

1. `/api/vector-search`: Search for verses semantically related to a query
2. `/api/similar-verses`: Find verses similar to a specified verse
3. `/api/compare-translations`: Compare translations using vector similarity
4. `/api/complex-search`: Perform multi-hop reasoning for theological queries

## Troubleshooting

### Model Verification and Loading

If you encounter model-related issues:

1. Use `check_required_models.bat` to verify all required models are loaded
2. Use `load_t5_model.bat` to load the T5 model specifically
3. Manually load models in LM Studio if automatic loading fails
4. Check model names in `.env.dspy` match the actual models in LM Studio

For detailed model management information, see [DSPy Model Management](../guides/dspy_model_management.md).

### API and Database Issues

Refer to the [pgvector_semantic_search](../../.cursor/rules/pgvector_semantic_search.mdc) cursor rule for detailed troubleshooting guidance for the entire semantic search system.

## See Also

- [DSPy Model Management](../guides/dspy_model_management.md)
- [Bible QA Documentation](../features/bible_qa.md)
- [API Reference](../reference/API_REFERENCE.md)

## Comprehensive Integration

### Multi-Source Semantic Search

The system enables searching across different text sources:

```sql
WITH query_embedding AS (
    SELECT %s::vector AS embedding
)
SELECT 
    'Hebrew' AS source_type,
    v.book_name, 
    v.chapter_num, 
    v.verse_num, 
    v.verse_text,
    v.translation_source,
    1 - (e.embedding <=> (SELECT embedding FROM query_embedding)) AS similarity
FROM 
    bible.verse_embeddings e
    JOIN bible.verses v ON e.verse_id = v.id
WHERE 
    v.translation_source = 'TAHOT'
UNION ALL
SELECT 
    'Greek' AS source_type,
    v.book_name, 
    v.chapter_num, 
    v.verse_num, 
    v.verse_text,
    v.translation_source,
    1 - (e.embedding <=> (SELECT embedding FROM query_embedding)) AS similarity
FROM 
    bible.verse_embeddings e
    JOIN bible.verses v ON e.verse_id = v.id
WHERE 
    v.translation_source = 'TAGNT'
ORDER BY 
    similarity DESC
LIMIT 20;
```

### Lexicon-Enhanced Results

Search results can be enriched with lexical information:

```python
def get_enriched_search_results(query, translation="KJV", limit=10):
    """Get semantic search results enriched with lexical data."""
    # Get query embedding vector
    query_embedding = get_embedding(query)
    
    # Determine which lexicon and word tables to use
    is_hebrew = translation in ['TAHOT']
    lexicon_table = "bible.hebrew_entries" if is_hebrew else "bible.greek_entries"
    word_table = "bible.hebrew_ot_words" if is_hebrew else "bible.greek_nt_words"
    
    # Format the embedding for PostgreSQL
    embedding_array = format_vector_for_postgres(query_embedding)
    
    # Build and execute query
    sql = f"""
    WITH similar_verses AS (
        SELECT 
            v.id, v.book_name, v.chapter_num, v.verse_num, v.verse_text,
            v.translation_source,
            1 - (e.embedding <=> %s::vector) AS similarity
        FROM 
            bible.verse_embeddings e
            JOIN bible.verses v ON e.verse_id = v.id
        WHERE 
            v.translation_source = %s
        ORDER BY 
            e.embedding <=> %s::vector
        LIMIT %s
    )
    SELECT 
        sv.book_name, sv.chapter_num, sv.verse_num, sv.verse_text, sv.similarity,
        w.word_text, w.word_position, w.strongs_id, w.grammar_code,
        l.lemma, l.definition, l.transliteration
    FROM 
        similar_verses sv
        JOIN {word_table} w ON w.verse_id = sv.id
        JOIN {lexicon_table} l ON l.strongs_id = w.strongs_id
    ORDER BY 
        sv.similarity DESC, sv.id, w.word_position
    """
    
    # Execute query and return results
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (embedding_array, translation, embedding_array, limit))
        results = cursor.fetchall()
    
    return results
```

### Theological Term Integration

The semantic search system prioritizes critical theological terms:

```python
def get_theological_term_search_results(query, translation="KJV", limit=10):
    """Get semantic search results with theological term highlighting."""
    query_embedding = get_embedding(query)
    embedding_array = format_vector_for_postgres(query_embedding)
    
    # Critical theological terms from docs/rules/theological_terms.md
    critical_terms = ["H430", "H3068", "H113", "H2617", "H539"]  # Elohim, YHWH, Adon, Chesed, Aman
    
    # Weight verses containing critical terms higher in results
    sql = """
    WITH similar_verses AS (
        SELECT 
            v.id, v.book_name, v.chapter_num, v.verse_num, v.verse_text,
            v.translation_source,
            1 - (e.embedding <=> %s::vector) AS base_similarity
        FROM 
            bible.verse_embeddings e
            JOIN bible.verses v ON e.verse_id = v.id
        WHERE 
            v.translation_source = %s
        ORDER BY 
            e.embedding <=> %s::vector
        LIMIT 50
    ),
    term_counts AS (
        SELECT 
            sv.id,
            COUNT(CASE WHEN w.strongs_id IN %s THEN 1 END) AS critical_term_count
        FROM 
            similar_verses sv
            LEFT JOIN bible.hebrew_ot_words w ON w.verse_id = sv.id
        GROUP BY 
            sv.id
    )
    SELECT 
        sv.book_name, sv.chapter_num, sv.verse_num, sv.verse_text,
        sv.base_similarity + (COALESCE(tc.critical_term_count, 0) * 0.1) AS adjusted_similarity
    FROM 
        similar_verses sv
        LEFT JOIN term_counts tc ON sv.id = tc.id
    ORDER BY 
        adjusted_similarity DESC
    LIMIT %s
    """
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (embedding_array, translation, embedding_array, tuple(critical_terms), limit))
        results = cursor.fetchall()
    
    return results
```

## Usage Examples

### Command Line Usage

Generate embeddings for all translations:
```bash
python -m src.utils.generate_verse_embeddings
```

Generate embeddings for specific translations:
```bash
python -m src.utils.generate_verse_embeddings KJV ASV
```

### Web Demo Application

Run the demo application:
```bash
python -m src.utils.vector_search_demo
```

Access the web interface at http://127.0.0.1:5050

### API Usage Examples

Python client:
```python
import requests

# Search for semantically similar verses
response = requests.get(
    "http://127.0.0.1:5050/search/vector",
    params={
        "q": "God created the heavens and the earth",
        "translation": "KJV",
        "limit": 5
    }
)
results = response.json()

# Find verses similar to a specific verse
response = requests.get(
    "http://127.0.0.1:5050/api/similar-verses",
    params={
        "book": "Genesis",
        "chapter": 1,
        "verse": 1,
        "translation": "KJV",
        "limit": 5
    }
)
similar_verses = response.json()
```

PowerShell client:
```powershell
# Search for semantically similar verses
$response = Invoke-WebRequest -Uri 'http://127.0.0.1:5050/search/vector?q=God created the heavens and the earth&translation=KJV&limit=3' -UseBasicParsing
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5

# Test with headers for JSON response
$headers = @{ "Accept" = "application/json" }
Invoke-WebRequest -Uri 'http://127.0.0.1:5050/search/vector?q=creation&translation=KJV' -Headers $headers -UseBasicParsing
```

## Cross-Language Considerations

The semantic search system has important considerations for different languages:

1. **English Translations (KJV, ASV, ESV)**
   - Work well with English queries
   - Generally consistent behavior across English translations

2. **Hebrew Text (TAHOT)**
   - English queries may not effectively match Hebrew content
   - For best results with TAHOT, use Hebrew text in queries
   - Example: Searching בְּרֵאשִׁית works better than "In the beginning"

3. **Greek Text (TAGNT)**
   - English queries may not effectively match Greek content
   - For best results with TAGNT, use Greek text in queries

## Related Documentation

- [API Reference](../reference/API_REFERENCE.md) - Complete API documentation
- [Database Schema](../reference/DATABASE_SCHEMA.md) - Database structure information
- [Theological Terms](theological_terms.md) - Theological term guidelines

## Modification History

| Date | Change | Author |
|------|--------|--------|
| 2025-05-06 | Consolidated semantic search documentation | BibleScholar Team | 