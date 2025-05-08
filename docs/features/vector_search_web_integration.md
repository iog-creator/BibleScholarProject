# Vector Search Web Integration Guide

This guide documents the integration of pgvector semantic search functionality with the BibleScholarProject web application.

## Overview

The vector search web integration provides users with a powerful semantic search capability for Bible verses, leveraging PostgreSQL's pgvector extension and embedding models. This feature enables searching by meaning rather than exact words.

## Components

The integration consists of:

1. **API Layer** (`src/api/vector_search_api.py`):
   - Standardized endpoints for vector-based semantic search
   - Read-only secure database connections
   - Consistent response schema

2. **Web Interface** (`templates/vector_search.html` and `templates/similar_verses.html`):
   - User-friendly search interface
   - Results display with similarity scores
   - Dynamic translation selection

3. **Integration Options**:
   - Full web application integration (`src/web_app.py`) 
   - Simplified standalone application (`vector_search_web.py`)

## API Endpoints

### Vector Search

`GET /api/vector-search`

**Parameters:**
- `q`: Search query (required)
- `translation`: Bible translation code (default: KJV)
- `limit`: Maximum number of results (default: 10, max: 50)

**Response:**
```json
{
  "results": [
    {
      "verse_id": 12345,
      "book_name": "Genesis",
      "chapter_num": 1, 
      "verse_num": 1,
      "verse_text": "In the beginning...",
      "translation_source": "KJV",
      "similarity": 0.95
    }
  ]
}
```

### Similar Verses

`GET /api/similar-verses`

**Parameters:**
- `book`: Book name (required)
- `chapter`: Chapter number (required)
- `verse`: Verse number (required)
- `translation`: Bible translation code (default: KJV)
- `limit`: Maximum number of results (default: 10, max: 50)

### Available Translations

`GET /api/available-translations`

Returns a list of translations with verse embeddings available in the database.

## Security Implementation

The vector search web application uses a secure database connection system that:

1. **Enforces Read-Only Access:**
   - All web requests use read-only database connections
   - Prevents accidental data modification
   - SQL-level protection against DELETE, UPDATE, INSERT, DROP operations

2. **Provides Graceful Fallbacks:**
   - Falls back to standard connection if secure connection is unavailable
   - Transparent error handling
   - Comprehensive logging

## Running the Web Applications

### Full Web Application

```bash
.\start_bible_qa_web.bat
```
This starts the complete web application with all features.

### Simplified Vector Search Only

```bash
.\start_vector_search_web.bat
```
This starts a lightweight application focused only on vector search functionality.

Access the interfaces at:
- http://localhost:5001/vector-search
- http://localhost:5001/similar-verses

## Testing with PowerShell

When testing the API endpoints with PowerShell:

```powershell
# Recommended approach for API testing
Invoke-RestMethod -Uri 'http://localhost:5001/api/vector-search?q=love+your+enemies&translation=KJV&limit=3'

# Health check
Invoke-WebRequest -Uri 'http://localhost:5001/health' -UseBasicParsing | Select-Object -ExpandProperty Content

# With parameters object
$params = @{
    'q' = 'faith without works'
    'translation' = 'KJV'
    'limit' = 3
}
Invoke-RestMethod -Uri 'http://localhost:5001/api/vector-search' -Body $params
```

Note: Avoid using `curl` in PowerShell as it's an alias for `Invoke-WebRequest` with different behavior.

## Troubleshooting

### Import Errors
- Check for missing modules in the `archive/` directory
- Ensure your PYTHONPATH includes the project root
- If `scripts` modules are missing, check `archive/scripts/`

### API Connection Issues
- Verify API services are running (check port 5000 for API endpoints)
- Confirm environment variables are properly set in `.env`
- Check logs for connection errors

### Database Connection Issues
- Verify PostgreSQL is running and accessible
- Check secure connection credentials in `.env`
- Confirm pgvector extension is installed 