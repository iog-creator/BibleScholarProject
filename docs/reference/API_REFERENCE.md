# BibleScholarProject API Reference

This document provides a comprehensive reference for all API endpoints in the BibleScholarProject.

*This document is complemented by the [api_standards](.cursor/rules/standards/api_standards.mdc) cursor rule.*

## Base URLs
- Lexicon API: `http://localhost:5000`
- Web App: `http://localhost:5001`
- Vector Search Demo: `http://localhost:5050`
- Bible QA API: `http://localhost:8000`

## Health Endpoints

### Check Lexicon API Health
```
GET /health
```
Returns a 200 status code if the API is running properly.

### Check Web App Health
```
GET /health
```
Returns a 200 status code if the web app is running properly.

## Theological Terms Endpoints

### Theological Terms Report
```
GET /api/theological_terms_report
```
Returns a comprehensive report of theological terms with occurrence statistics.

Web App Route:
```
GET /theological_terms_report
```

### Validate Critical Hebrew Terms
```
GET /api/lexicon/hebrew/validate_critical_terms
```
Validates that critical Hebrew theological terms meet minimum occurrence counts.

Web App Route:
```
GET /hebrew_terms_validation
```

### Cross Language Terms
```
GET /api/cross_language/terms
```
Provides comparison of theological terms across different language translations.

Web App Route:
```
GET /cross_language
```

## Semantic Search Endpoints

### Vector Search
```
GET /api/vector-search
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| q | string | (required) | The search query text |
| translation | string | "KJV" | Translation to search (KJV, ASV, TAHOT, TAGNT) |
| limit | integer | 10 | Maximum number of results |

**Example Response:**

```json
[
  {
    "book_name": "Genesis",
    "chapter_num": 1,
    "verse_num": 1,
    "verse_text": "In the beginning God created the heaven and the earth.",
    "similarity": 0.92
  }
]
```

### Similar Verses
```
GET /api/similar-verses
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| book | string | (required) | Book name |
| chapter | integer | (required) | Chapter number |
| verse | integer | (required) | Verse number |
| translation | string | "KJV" | Translation to search |
| limit | integer | 10 | Maximum number of results |

### Compare Translations
```
GET /api/compare-translations
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| book | string | (required) | Book name |
| chapter | integer | (required) | Chapter number |
| verse | integer | (required) | Verse number |
| source_translation | string | "KJV" | Source translation |
| target_translations | string | "ASV,TAHOT,TAGNT" | Comma-separated list of target translations |

## Comprehensive Search API

The Comprehensive Search API enables powerful semantic search across all database resources, including verses, lexicons, proper names, and cross-language mappings.

### Base URL

All Comprehensive Search API endpoints are prefixed with:
```
/api/comprehensive
```

### Endpoints

#### Vector Search

```
GET /api/comprehensive/vector-search
```

Performs semantic vector search across multiple translations with rich contextual data.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| q | string | (required) | The search query text |
| translation | string | "KJV" | Primary translation to search (KJV, ASV, TAHOT, TAGNT) |
| include_lexicon | boolean | true | Include lexical data for words |
| include_related | boolean | true | Include related terms |
| include_names | boolean | true | Include proper name data |
| cross_language | boolean | false | Search across language boundaries |
| limit | integer | 10 | Maximum number of results (max: 50) |

**Example Response:**

```json
{
  "query": "God created",
  "translation": "KJV",
  "cross_language": true,
  "results": [
    {
      "reference": "Genesis 1:1",
      "text": "In the beginning God created the heaven and the earth.",
      "translation": "KJV",
      "similarity": 97.56,
      "lexical_data": [
        {
          "word": "created",
          "position": 4,
          "strongs_id": "H1254",
          "grammar": "Qal",
          "lemma": "בָּרָא",
          "definition": "to create"
        }
      ]
    },
    {
      "reference": "בראשית 1:1",
      "text": "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃",
      "translation": "TAHOT",
      "similarity": 92.34,
      "cross_language": true
    }
  ]
}
```

#### Theological Term Search

```
GET /api/comprehensive/theological-term-search
```

Searches for theological terms across translations and finds occurrences with context.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| term | string | (required) | Theological term to search |
| language | string | "english" | Term language (hebrew, greek, english, arabic) |
| include_equivalent | boolean | true | Include equivalent terms in other languages |
| limit | integer | 10 | Maximum number of results (max: 50) |

**Example Response:**

```json
{
  "term": "elohim",
  "language": "hebrew",
  "term_info": [
    {
      "hebrew_term": "אלהים",
      "greek_term": "θεός",
      "english_term": "God",
      "strongs_id": "H430",
      "theological_category": "deity"
    }
  ],
  "verses": [
    {
      "reference": "Genesis 1:1",
      "text": "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃",
      "translation": "TAHOT",
      "term_info": {
        "word": "אֱלֹהִ֑ים",
        "strongs_id": "H430",
        "lemma": "אֱלֹהִים",
        "definition": "God, gods"
      }
    }
  ],
  "count": 1
}
```

#### Name Search

```
GET /api/comprehensive/name-search
```

Searches for biblical proper names and their relationships.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| name | string | (required) | Proper name to search |
| include_relationships | boolean | true | Include related names |
| relationship_type | string | "" | Filter by relationship type |
| limit | integer | 20 | Maximum number of results (max: 50) |

**Example Response:**

```json
{
  "query": "Moses",
  "count": 1,
  "results": {
    "names": [
      {
        "name": "Moses",
        "hebrew": "מֹשֶׁה",
        "transliteration": "mōšeh",
        "description": "Hebrew prophet and lawgiver",
        "occurrences": 847
      }
    ],
    "relationships": [
      {
        "name1": "Moses",
        "name2": "Aaron",
        "relationship_type": "brother"
      },
      {
        "name1": "Moses",
        "name2": "Pharaoh",
        "relationship_type": "confrontation"
      }
    ]
  }
}
```

## Additional API Endpoints
```
API /api/verse/names
```
Needs documentation.


```
API /api/vector-search-with-lexicon
```
Needs documentation.


```
API /api/vector-search
```
Needs documentation.


```
API /api/theological_terms_report
```
Needs documentation.


```
API /api/tagged/verse
```
Needs documentation.


```
API /api/tagged/search
```
Needs documentation.


```
API /api/similar-verses
```
Needs documentation.


```
API /api/resources/translations
```
Needs documentation.


```
API /api/resources/manuscripts
```
Needs documentation.


```
API /api/resources/commentaries
```
Needs documentation.


```
API /api/resources/archaeology
```
Needs documentation.


```
API /api/resources
```
Needs documentation.


```
API /api/names/search
```
Needs documentation.


```
API /api/names
```
Needs documentation.


```
API /api/morphology/hebrew
```
Needs documentation.


```
API /api/morphology/greek
```
Needs documentation.


```
API /api/lexicon/stats
```
Needs documentation.


```
API /api/lexicon/search
```
Needs documentation.


```
API /api/lexicon/hebrew/validate_critical_terms
```
Needs documentation.


```
API /api/dspy/ask_with_context
```
Needs documentation.


```
API /api/cross_language/terms
```
Needs documentation.


```
API /api/cross-language-search
```
Needs documentation.


```
API /api/compare-translations
```
Needs documentation.



### Lexicon API

```
GET /api/lexicon/stats
```
Returns statistics about the lexicon entries.

```
GET /api/lexicon/search
```
Searches the lexicon entries based on query parameters.

### Tagged Text API

```
GET /api/tagged/verse
```
Returns a verse with tagged words.

```
GET /api/tagged/search
```
Searches for tagged words in the text.

### Morphology API

```
GET /api/morphology/hebrew
```
Returns Hebrew morphology code explanations.

```
GET /api/morphology/greek
```
Returns Greek morphology code explanations.

### Proper Names API

```
GET /api/names
```
Returns a list of biblical proper names.

```
GET /api/names/search
```
Searches for proper names.

```
GET /api/verse/names
```
Returns proper names mentioned in a specific verse.

### Resources API

```
GET /api/resources/commentaries
```
Returns commentaries related to biblical texts.

```
GET /api/resources/archaeology
```
Returns archaeological data related to biblical texts.

```
GET /api/resources/manuscripts
```
Returns information about biblical manuscripts.

```
GET /api/resources/translations
```
Returns information about Bible translations.

### DSPy API

The DSPy API provides endpoints for Bible question answering with enhanced DSPy 2.6 features including multi-turn conversation history.

### Base URL

```
/api/dspy
```

### Health Check

```http
GET /api/dspy/health
```

Returns the status of the DSPy API and model.

**Response**

```json
{
  "status": "ok",
  "message": "DSPy API is running with model loaded",
  "version": "2.0.0",
  "dspy_version": "2.6.23"
}
```

### Ask a Question

```http
POST /api/dspy/ask
Content-Type: application/json
```

Ask a question without providing specific Bible context.

**Request Body**

```json
{
  "question": "Who was Moses?",
  "session_id": "optional-session-id-for-conversation-history"
}
```

**Response**

```json
{
  "question": "Who was Moses?",
  "answer": "Moses was a prophet and leader in the Old Testament who led the Israelites out of slavery in Egypt. He is known for receiving the Ten Commandments from God on Mount Sinai and for writing the first five books of the Bible, known as the Pentateuch or Torah.",
  "session_id": "user-123",
  "history_length": 1
}
```

### Ask with Context

```http
POST /api/dspy/ask_with_context
Content-Type: application/json
```

Ask a question with specific Bible context.

**Request Body**

```json
{
  "question": "What did Moses do?",
  "context": "Moses led the Israelites out of Egypt across the Red Sea.",
  "session_id": "optional-session-id-for-conversation-history"
}
```

**Response**

```json
{
  "question": "What did Moses do?",
  "answer": "According to the context, Moses led the Israelites out of Egypt across the Red Sea.",
  "context": "Moses led the Israelites out of Egypt across the Red Sea.",
  "session_id": "user-123",
  "history_length": 2
}
```

### Get Conversation History

```http
GET /api/dspy/conversation?session_id=user-123
```

Get the conversation history for a session.

**Response**

```json
{
  "session_id": "user-123",
  "conversation": [
    {
      "role": "user",
      "content": "Who was Moses?",
      "turn": 1
    },
    {
      "role": "assistant",
      "content": "Moses was a prophet and leader in the Old Testament who led the Israelites out of slavery in Egypt. He is known for receiving the Ten Commandments from God on Mount Sinai and for writing the first five books of the Bible, known as the Pentateuch or Torah.",
      "turn": 2
    },
    {
      "role": "user",
      "content": "What did Moses do?",
      "turn": 3
    },
    {
      "role": "assistant",
      "content": "According to the context, Moses led the Israelites out of Egypt across the Red Sea.",
      "turn": 4
    }
  ],
  "turns": 2
}
```

### Clear Conversation History

```http
DELETE /api/dspy/conversation?session_id=user-123
```

Clear the conversation history for a session.

**Response**

```json
{
  "status": "ok",
  "message": "Conversation history cleared for session user-123"
}
```

### Bible QA API

```
POST /api/question
```
Answers Bible questions using the trained DSPy model, optionally using Claude API when configured.

**Request:**
```json
{
  "question": "Who created the heavens and the earth?",
  "context": "In the beginning God created the heaven and the earth.",
  "model_version": "latest"
}
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| question | string | (required) | The Bible question to answer |
| context | string | "" | Optional biblical context to improve answer |
| model_version | string | "latest" | Version of the model to use |

**Response:**
```json
{
  "answer": "God created the heavens and the earth.",
  "model_info": {
    "model_type": "T5 Bible QA",
    "model_path": "models/dspy/bible_qa_t5/bible_qa_t5_latest"
  },
  "status": "success"
}
```

```
GET /api/models
```
Lists available models in the registry.

**Response:**
```json
{
  "available_models": [
    {
      "version_id": "mlflow_12345678_20250507_120000",
      "run_id": "12345678abcdef1234567890",
      "creation_time": "20250507_120000",
      "model_type": "bible_qa_t5",
      "description": "T5 model trained with Claude teacher",
      "is_production": true
    }
  ],
  "current_production": "mlflow_12345678_20250507_120000",
  "latest": "mlflow_12345678_20250507_120000"
}
```

```
POST /api/models/register
```
Registers a model from MLflow into the model registry.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| run_id | string | (required) | MLflow run ID for the model |
| description | string | null | Description of this model version |

```
POST /api/models/{version_id}/promote
```
Promotes a model version to production.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| version_id | string | (required) | ID of the model version to promote |

### Advanced Vector Search

```
GET /api/vector-search-with-lexicon
```
Performs semantic search with lexicon integration.

```
GET /api/cross-language-search
```
Performs semantic search across multiple languages.

## API Usage Examples

### Python Example

```python
import requests

# Get theological terms report
response = requests.get("http://localhost:5000/api/theological_terms_report")
terms_report = response.json()

# Use vector search
response = requests.get(
    "http://localhost:5050/api/vector-search",
    params={
        "q": "God created the heavens and the earth",
        "translation": "KJV",
        "limit": 5
    }
)
search_results = response.json()
```

### PowerShell Example

```powershell
# Get theological terms validation
$response = Invoke-WebRequest -Uri 'http://localhost:5000/api/lexicon/hebrew/validate_critical_terms' -UseBasicParsing
$validation = $response.Content | ConvertFrom-Json

# Use vector search
$response = Invoke-WebRequest -Uri 'http://localhost:5050/api/vector-search?q=God created the heavens and the earth&translation=KJV&limit=5' -UseBasicParsing
$searchResults = $response.Content | ConvertFrom-Json
```

## Related Documentation

- [Database Schema](DATABASE_SCHEMA.md) - Database structure details
- [Semantic Search](../features/semantic_search.md) - Semantic search implementation
- [Theological Terms](../features/theological_terms.md) - Theological term handling

## Modification History

| Date | Change | Author |
|------|--------|--------|
| 2025-05-06 | Moved to reference directory and updated cross-references | BibleScholar Team |
| 2025-05-01 | Added semantic search endpoints | BibleScholar Team |
| 2025-04-15 | Added comprehensive search API documentation | BibleScholar Team |
| 2025-03-20 | Added theological terms endpoints | BibleScholar Team |
| 2025-02-10 | Initial API documentation | BibleScholar Team | 