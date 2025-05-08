# DSPy-Enhanced Semantic Search for Bible Verses

This module enhances the semantic search capabilities for Bible verses by combining pgvector's vector similarity search with DSPy's language model reasoning capabilities.

## Key Features

1. **Query Expansion**: Automatically expands user queries with relevant theological concepts to improve search coverage
2. **Contextual Reranking**: Reranks search results based on contextual relevance to the query
3. **Multi-hop Reasoning**: Handles complex theological queries by exploring related biblical topics
4. **Seamless Integration**: Works with the existing pgvector database infrastructure

## Architecture

The implementation consists of three main components:

1. **Vector Search**: Uses PostgreSQL's pgvector extension to find semantically similar Bible verses
2. **DSPy Modules**: Adds language model capabilities through DSPy signatures and modules
3. **API Layer**: Exposes functionality through REST endpoints

### DSPy Modules

The system uses three key DSPy modules:

- `BibleQueryExpansion`: Expands queries with theological concepts
- `BibleVerseReranker`: Reranks verses based on relevance to the query
- `TopicHopping`: Identifies related biblical topics for complex queries

## Installation and Setup

### Prerequisites

- PostgreSQL with pgvector extension
- LM Studio running locally with a text embedding model
- DSPy installed

### Environment Variables

Create or update `.env.dspy` with:

```
# Database connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bible_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# LM Studio API
LM_STUDIO_API_URL=http://127.0.0.1:1234/v1
LM_STUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0
```

## Usage

### Running the Demo

The demo application provides a web interface to test the enhanced search capabilities:

```bash
python -m src.utils.dspy_search_demo
```

Then open http://127.0.0.1:5060 in your browser.

### API Endpoints

The following endpoints are available when the API server is running:

- `/dspy-search`: Basic DSPy-enhanced semantic search
- `/complex-search`: Advanced search with multi-hop reasoning
- `/expand-query`: Query expansion with theological concepts
- `/related-topics`: Get related biblical topics for a query
- `/compare-search`: Compare DSPy-enhanced and standard vector search

### Example API Usage

```python
# Basic search
response = requests.get(
    "http://localhost:5000/dspy-search",
    params={"q": "God's creation of the world", "translation": "KJV", "limit": 5}
)
results = response.json()

# Complex theological search
response = requests.get(
    "http://localhost:5000/complex-search",
    params={"q": "How does Jesus fulfill Old Testament prophecies?"}
)
complex_results = response.json()
```

## Development and Testing

### Running Tests

```bash
python -m unittest tests.unit.test_dspy_semantic_search
```

### Adding New DSPy Components

To add a new DSPy component:

1. Define a new signature in `semantic_search.py`
2. Add the component to the `EnhancedSemanticSearch` class
3. Update the API endpoints to use the new component
4. Add appropriate tests

## Performance Considerations

1. **Query Expansion**: Each expanded query requires a separate vector search
2. **Reranking**: Reranking adds latency but significantly improves result quality
3. **Multi-hop Reasoning**: More resource-intensive but provides deeper theological insights

## Integration with Existing Systems

This implementation integrates with:

1. **pgvector Database**: Uses the existing verse_embeddings table
2. **LM Studio**: Uses the same embedding model as the vector_search_api
3. **DSPy**: Leverages DSPy for language model reasoning

## Future Enhancements

1. **Fine-tuned Models**: Train domain-specific models for theological query understanding
2. **Hybrid Retrieval**: Combine BM25 keyword search with vector search
3. **Cross-lingual Search**: Search across different Bible translations with language-agnostic embeddings

## Troubleshooting

### Common Issues

1. **LM Studio Connection**: Ensure LM Studio is running and the API URL is correct
2. **Database Connection**: Verify PostgreSQL connection parameters
3. **DSPy Errors**: Check DSPy compatibility with the language model

### Debugging

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
``` 