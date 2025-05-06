# Bible Semantic Search Implementation with pgvector

This documentation describes the implementation of semantic search capabilities in the BibleScholarProject using PostgreSQL's pgvector extension.

## Overview

The BibleScholarProject implements semantic search for Bible verses using vector embeddings stored in PostgreSQL with the pgvector extension. This enables:

1. Finding verses similar to a text query
2. Finding verses similar to a specific reference verse
3. Comparing translations of the same verse
4. Exploring thematic connections between different parts of the Bible

## Database Implementation

### Schema

The verse embeddings are stored in a dedicated table:

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

### Supported Translations

The system currently supports generating embeddings for these translations:

- King James Version (KJV)
- American Standard Version (ASV)
- Tagged Hebrew Old Testament (TAHOT)
- Tagged Greek New Testament (TAGNT)
- English Standard Version (ESV) - sample only, not required for production use

## Embedding Generation

### Process

Embeddings are generated using the following process:

1. Verses are retrieved from the database for specified translations
2. Text is processed in batches of 50 for optimal GPU utilization
3. Embeddings are generated using LM Studio API with the `text-embedding-nomic-embed-text-v1.5@q8_0` model
4. Embeddings are stored in the database with proper vector formatting

### Command Line Usage

```bash
# Generate embeddings for all supported translations
python -m src.utils.generate_verse_embeddings

# Generate embeddings for specific translations
python -m src.utils.generate_verse_embeddings KJV ASV
```

## API Endpoints

### Vector Search API

The system provides these semantic search endpoints:

1. `/api/vector-search`: Search for verses semantically related to a query
   - Parameters: `q` (query text), `translation` (e.g., KJV), `limit` (default: 10)

2. `/api/similar-verses`: Find verses similar to a specified verse
   - Parameters: `book`, `chapter`, `verse`, `translation`, `limit`

3. `/api/compare-translations`: Compare translations of the same verse
   - Parameters: `book`, `chapter`, `verse`, `source_translation`, `target_translations`

## Web Demo Application

A demo application is available for testing the semantic search capabilities:

### Features

- Web interface for comparing semantic vs. keyword search
- Support for multiple translations
- Real-time search with similarity scores
- Language-specific search guidance

### Usage

```bash
# Start the demo application
python -m src.utils.vector_search_demo

# Access in your browser
# http://127.0.0.1:5050
```

## Cross-Language Considerations

The semantic search system has important considerations for different languages:

1. **English Translations (KJV, ASV, ESV)**
   - Work well with English queries
   - Generally consistent behavior across different English translations

2. **Hebrew Text (TAHOT)**
   - English queries may not effectively match Hebrew content
   - For best results with TAHOT, use Hebrew text in queries
   - Example: Searching בְּרֵאשִׁית works better than "In the beginning"

3. **Greek Text (TAGNT)**
   - English queries may not effectively match Greek content
   - For best results with TAGNT, use Greek text in queries

## Integration with Lexicons and Word Analysis

The semantic search system can be enhanced with lexicon and morphological data integration:

### Lexicon Integration

Connect vector search results with Hebrew and Greek lexicon entries using these approaches:

1. **Strong's ID-Based Enrichment**
   - Enhance verse search results with lexicon definitions from matching Strong's IDs
   - Join `bible.verse_embeddings` results with `bible.hebrew_entries` or `bible.greek_entries`
   - Example: Show Hebrew/Greek definitions for key terms in semantically similar verses

2. **Theological Term Highlighting**
   - Highlight critical theological terms in search results (e.g., H430/Elohim, H3068/YHWH)
   - Prioritize verses containing high-value theological terms in semantic search results

### Morphological Analysis Integration

Add word-level information to semantic search results:

1. **Grammatical Search Filtering**
   - Filter semantic search results by grammatical constructs (e.g., verb forms, noun cases)
   - Combine vector similarity with grammatical pattern matching

2. **Word Position Analysis**
   - Use `word_position` from `hebrew_ot_words` and `greek_nt_words` tables to locate specific terms
   - Provide context around key words in semantically similar verses

### Example Database Queries

Join verse embeddings with Strong's lexicon data:

```sql
-- Find verses similar to a query and enrich with Hebrew lexicon data
WITH similar_verses AS (
    SELECT 
        v.id, v.book_name, v.chapter_num, v.verse_num, v.verse_text,
        v.translation_source,
        1 - (e.embedding <=> %s::vector) AS similarity
    FROM 
        bible.verse_embeddings e
        JOIN bible.verses v ON e.verse_id = v.id
    WHERE 
        v.translation_source = 'TAHOT'
    ORDER BY 
        e.embedding <=> %s::vector
    LIMIT 5
)
SELECT 
    sv.*,
    w.word_text, w.strongs_id,
    l.lemma, l.definition
FROM 
    similar_verses sv
    JOIN bible.hebrew_ot_words w ON w.verse_id = sv.id
    JOIN bible.hebrew_entries l ON l.strongs_id = w.strongs_id
WHERE 
    w.strongs_id IN ('H430', 'H3068', 'H7225')  -- Elohim, YHWH, beginning
ORDER BY 
    sv.similarity DESC, sv.id, w.word_position;
```

## Testing

Several test scripts are available to verify functionality:

```bash
# Test database connectivity and vector search
python test_pgvector_search.py

# Debug specific translation issues
python debug_vector_search.py

# Test with the web interface
python -m src.utils.vector_search_demo
```

## PowerShell Testing Commands

When testing the API with PowerShell, use these commands:

```powershell
# Basic vector search query
$response = Invoke-WebRequest -Uri 'http://127.0.0.1:5050/search/vector?q=God created the heavens and the earth&translation=KJV&limit=3' -UseBasicParsing
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5

# Test LM Studio API directly
$headers = @{ "Content-Type" = "application/json" }
$body = @{ 
    model = "text-embedding-nomic-embed-text-v1.5@q8_0"
    input = "In the beginning God created the heaven and the earth" 
} | ConvertTo-Json
Invoke-WebRequest -Uri 'http://127.0.0.1:1234/v1/embeddings' -Method Post -Headers $headers -Body $body -UseBasicParsing
```

## Future Enhancements

1. **Theological Concept Vectors**
   - Generate embeddings for specific theological concepts
   - Create vector representations for theological terms across multiple translations
   - Enable searching for theological concepts rather than just verses

2. **Cross-Reference Enhanced Search**
   - Incorporate cross-reference data to improve semantic search results
   - Boost semantic similarity scores for verses that are traditionally cross-referenced

3. **Strong's ID Vector Search**
   - Implement vector search based on patterns of Strong's IDs rather than text
   - Enable finding passages with similar word usage patterns regardless of translation

## Performance Considerations

1. **Database Indexing**
   - The IVFFlat index type is used for efficient similarity search
   - 100 lists provides a good balance of speed and accuracy

2. **Embedding Generation**
   - Batch processing (50 verses at a time) optimizes GPU utilization
   - Full database embedding generation takes approximately 2-3 hours

3. **API Response Times**
   - Vector search queries typically complete in under 200ms
   - Response time increases with the number of verses in the database

## Troubleshooting

### LM Studio Issues

- Ensure LM Studio is running at http://127.0.0.1:1234
- Verify the embedding model is loaded
- Check API errors in logs or direct API calls

### Database Issues

- Ensure pgvector extension is installed: `CREATE EXTENSION vector;`
- Check for proper unique constraint on verse_id in verse_embeddings table
- Verify vector dimension is consistently 768 for all embeddings

### Search Issues

- For Hebrew/Greek texts, use queries in the appropriate script
- Verify database connection parameters in .env file
- Check log files for error messages in embedding generation 