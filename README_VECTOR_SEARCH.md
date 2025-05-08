# pgVector Semantic Search for Bible Verses

This document outlines the implementation of semantic search capabilities in the BibleScholarProject using PostgreSQL's pgvector extension.

## Overview

The semantic search system enables you to:
- Search for Bible verses related to a specific concept or topic
- Find verses similar to a reference verse
- Compare different translations of the same verse using vector similarity

## Prerequisites

1. **PostgreSQL with pgvector extension**
   - PostgreSQL 12+ with pgvector extension installed
   - Database configured with the `vector` extension enabled

2. **LM Studio for Embeddings**
   - Local LM Studio installation with embedding model
   - Default model: `text-embedding-nomic-embed-text-v1.5@q8_0`
   - API should be running on http://localhost:1234/v1 (configurable via .env)

## Setup Instructions

### 1. Install pgvector Extension

In your PostgreSQL database:
```sql
CREATE EXTENSION vector;
```

### 2. Configure Environment Variables

Make sure these variables are set in your `.env` file:
```
# LM Studio API settings
LM_STUDIO_API_URL=http://localhost:1234/v1
LM_STUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0

# Database connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bible_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### 3. Generate Verse Embeddings

Run the embedding generation script:
```
# Generate embeddings for all verses
./generate_verse_embeddings.bat

# Generate for a specific translation
./generate_verse_embeddings.bat --translation KJV

# Limit the number of verses processed
./generate_verse_embeddings.bat --limit 1000 --batch-size 50
```

### 4. Test Vector Search

Verify that the search functionality is working:
```
./test_vector_search.bat
```

## API Endpoints

### Vector Search

`GET /api/vector-search`

Query parameters:
- `q`: Search query (required)
- `translation`: Bible translation code (default: KJV)
- `limit`: Maximum number of results (default: 10, max: 50)

Example:
```
/api/vector-search?q=love your neighbor&translation=KJV&limit=5
```

### Similar Verses

`GET /api/similar-verses`

Query parameters:
- `reference`: Verse reference, e.g., "John 3:16" (required)
- `translation`: Bible translation code (default: KJV)
- `limit`: Maximum number of results (default: 10, max: 50)

Example:
```
/api/similar-verses?reference=Matthew 5:44&translation=KJV&limit=5
```

### Compare Translations

`GET /api/compare-translations`

Query parameters:
- `reference`: Verse reference, e.g., "John 3:16" (required)
- `base_translation`: Base translation to compare against (default: KJV)

Example:
```
/api/compare-translations?reference=Genesis 1:1&base_translation=KJV
```

### Available Translations

`GET /api/available-translations`

Returns a list of translations with verse embeddings available in the database.

## Web Interfaces

The system includes web interfaces for:
- Vector search: `/vector-search`
- Similar verses: `/similar-verses`

## Web Application Integration

The vector search functionality is fully integrated with the web application:

### Vector Search Page
- **URL:** `/vector-search`
- **Features:**
  - Simple interface for semantic search
  - Dynamic translation selection based on available embeddings
  - Displays search results with similarity percentages
  - Shows book distribution statistics
  - Links to find similar verses for each result

### Similar Verses Page
- **URL:** `/similar-verses`
- **Features:**
  - Find verses semantically similar to a reference verse
  - Input book, chapter, and verse numbers
  - Select from available translations
  - Displays source verse and similar verses with similarity scores
  - Navigate between verses with "Make this the source verse" links

### Integration with Secure Database

The web application automatically uses the secure database connection in read-only mode when available:
- Prevents accidental data modification from the web interface
- Falls back to standard connection if secure connection is not available
- Standardized API responses for consistent UI display
- Dynamic translation selection based on available embeddings in the database

### Running the Web Application

There are two options for running the web application:

#### 1. Full Web Application
Start the complete web application with:
```
./start_bible_qa_web.bat
```

#### 2. Simplified Vector Search Web Application
For a dedicated vector search interface only:
```
./start_vector_search_web.bat
```
This simplified version provides just the vector search functionality without other components.

Access the vector search features at:
- http://localhost:5001/vector-search
- http://localhost:5001/similar-verses

## Testing API Endpoints

When testing API endpoints with PowerShell, use these approaches:

```powershell
# Test API endpoints with proper PowerShell syntax
Invoke-RestMethod -Uri 'http://localhost:5001/api/vector-search?q=love+your+enemies&translation=KJV&limit=3'

# Health check
Invoke-WebRequest -Uri 'http://localhost:5001/health' -UseBasicParsing | Select-Object -ExpandProperty Content

# Use parameters object for more complex queries
$params = @{
    'q' = 'faith without works'
    'translation' = 'KJV'
    'limit' = 3
}
Invoke-RestMethod -Uri 'http://localhost:5001/api/vector-search' -Body $params
```

Note: In PowerShell, avoid using `curl` as it's an alias for `Invoke-WebRequest` and can behave differently than expected.

## Technical Implementation

The vector search system uses:
- 768-dimensional text embeddings from LM Studio
- Cosine similarity for semantic matching (`<=>` operator in pgvector)
- IVFFlat index for efficient similarity search
- Batch processing (50 verses per batch) for efficient embedding generation

## Database Security

The Bible database is protected with a secure access system that prevents accidental modification or deletion:

### Setup

Run the database security setup script:
```
./setup_db_security.bat
```

This script will:
1. Create PostgreSQL roles for read-only and write access
2. Configure appropriate permissions for each role
3. Add required credentials to your .env file
4. Test the secure connection

### Using Secure Connections

In your code, use the secure connection utility:

```python
from src.database.secure_connection import get_secure_connection

# For read-only access (default, safe mode)
conn = get_secure_connection()  # mode='read' is default

# For write access (requires POSTGRES_WRITE_PASSWORD)
conn = get_secure_connection(mode='write')
```

Read-only mode is enforced at the PostgreSQL level and provides these benefits:
- Prevents accidental modification of Bible data
- Blocks DROP, INSERT, UPDATE, DELETE operations
- Limits query runtime with timeout settings
- Works with all existing API endpoints

### Environment Variables

The following environment variables control database access:
- `POSTGRES_READ_USER` - Username for read-only access
- `POSTGRES_READ_PASSWORD` - Password for read-only access
- `POSTGRES_WRITE_USER` - Username for write access
- `POSTGRES_WRITE_PASSWORD` - Password for write access (required for data modification)

## Troubleshooting

1. **Vector Extension Issues**
   - Ensure the `vector` extension is installed in your database
   - Run `SELECT * FROM pg_extension WHERE extname = 'vector'` to verify

2. **LM Studio Connection Issues**
   - Verify LM Studio is running and accessible at the configured URL
   - Check that the embedding model is loaded in LM Studio

3. **Embedding Generation Issues**
   - Check the logs at `logs/verse_embeddings.log` for errors
   - Try with a smaller batch size if you encounter memory issues

4. **Search Performance Issues**
   - Verify the IVFFlat index exists on the embedding column
   - Adjust the number of lists in the index based on your dataset size

## Next Steps and Improvements

Potential enhancements:
- Add support for more embedding models
- Implement query expansion for better search results
- Add cross-lingual search capabilities
- Integrate with DSPy for enhanced semantic understanding
- Create a comprehensive search interface combining multiple search methods 