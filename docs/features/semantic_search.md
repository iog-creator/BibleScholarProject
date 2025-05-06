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

### Embedding Generation

Embeddings are generated using:
- LM Studio API with `text-embedding-nomic-embed-text-v1.5@q8_0` model
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
            "http://127.0.0.1:1234/v1/embeddings",
            headers={"Content-Type": "application/json"},
            json={"model": "text-embedding-nomic-embed-text-v1.5@q8_0", "input": texts}
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

### Supported Translations

The system supports embeddings for these translations:

- King James Version (KJV)
- American Standard Version (ASV)
- Tagged Hebrew Old Testament (TAHOT)
- Tagged Greek New Testament (TAGNT)
- English Standard Version (ESV) - sample only

### API Implementation

The semantic search API is implemented in `src/api/vector_search_api.py` with these endpoints:

1. `/api/vector-search`: Search for verses semantically related to a query
   ```python
   @app.route('/api/vector-search')
   def vector_search():
       query = request.args.get('q')
       translation = request.args.get('translation', 'KJV')
       limit = request.args.get('limit', 10, type=int)
       
       # Generate embedding for query
       embedding = get_embedding(query)
       embedding_array = format_vector_for_postgres(embedding)
       
       # Perform semantic search
       with get_connection() as conn:
           cursor = conn.cursor()
           cursor.execute("""
               SELECT v.book_name, v.chapter_num, v.verse_num, v.verse_text, 
                      1 - (e.embedding <=> %s::vector) AS similarity
               FROM bible.verse_embeddings e
               JOIN bible.verses v ON e.verse_id = v.id
               WHERE v.translation_source = %s
               ORDER BY e.embedding <=> %s::vector
               LIMIT %s
           """, (embedding_array, translation, embedding_array, limit))
           
           results = cursor.fetchall()
           
       return jsonify(results)
   ```

2. `/api/similar-verses`: Find verses similar to a specified verse
3. `/api/compare-translations`: Compare translations using vector similarity

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

## Troubleshooting

### LM Studio Connection Issues

- Ensure LM Studio is running at http://127.0.0.1:1234
- Verify the `text-embedding-nomic-embed-text-v1.5@q8_0` model is loaded
- Check LM Studio API errors with direct API calls:
  ```powershell
  $headers = @{ "Content-Type" = "application/json" }
  $body = @{ 
      model = "text-embedding-nomic-embed-text-v1.5@q8_0"
      input = "Test text" 
  } | ConvertTo-Json
  Invoke-WebRequest -Uri 'http://127.0.0.1:1234/v1/embeddings' -Method Post -Headers $headers -Body $body -UseBasicParsing
  ```

### Database Schema Issues

- Ensure proper unique constraint on verse_id in verse_embeddings table
- Check ON CONFLICT handling in INSERT statements
- Verify proper vector dimension (768) in all embeddings

### Search Query Issues

- Verify correct book names (e.g., "Psalms" not "Psalm")
- For Hebrew/Greek texts, use queries in the appropriate script
- Check database connectivity and table existence

## Related Documentation

- [API Reference](../reference/API_REFERENCE.md) - Complete API documentation
- [Database Schema](../reference/DATABASE_SCHEMA.md) - Database structure information
- [Theological Terms](theological_terms.md) - Theological term guidelines

## Modification History

| Date | Change | Author |
|------|--------|--------|
| 2025-05-06 | Consolidated semantic search documentation | BibleScholar Team | 