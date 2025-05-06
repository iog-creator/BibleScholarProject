# BibleScholarProject API Reference

This document provides a comprehensive reference for all API endpoints in the BibleScholarProject.

## Base URLs
- Lexicon API: `http://localhost:5000`
- Web App: `http://localhost:5001`

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
        "name_id": "N047",
        "name": "Moses",
        "transliteration": "Mosheh",
        "description": "Prophet and lawgiver, who led Israel out of Egypt",
        "forms": [
          {
            "form": "משה",
            "transliteration": "mosheh",
            "language": "hebrew"
          }
        ]
      }
    ],
    "relationships": [
      {
        "name1": "Moses",
        "name2": "Aaron",
        "transliteration1": "Mosheh",
        "transliteration2": "Aharon",
        "relationship_type": "brother"
      }
    ],
    "verses": [
      {
        "reference": "Exodus 3:4",
        "text": "וַיַּ֥רְא יְהוָ֖ה כִּ֣י סָ֣ר לִרְא֑וֹת וַיִּקְרָא֩ אֵלָ֨יו אֱלֹהִ֜ים מִתּ֣וֹךְ הַסְּנֶ֗ה וַיֹּ֛אמֶר מֹשֶׁ֥ה מֹשֶׁ֖ה וַיֹּ֥אמֶר הִנֵּֽנִי׃",
        "translation": "TAHOT",
        "name": "Moses",
        "transliteration": "Mosheh"
      }
    ]
  }
}
```

## API Usage

### Authentication
Currently, the API does not require authentication for local development use.

### Response Format
All API endpoints return JSON responses with the following structure:

```json
{
  "status": "success",
  "data": {
    // Response data specific to the endpoint
  }
}
```

For error responses:

```json
{
  "status": "error",
  "message": "Error message"
}
```

### Rate Limiting
No rate limiting is currently implemented for local development.

## Implementation Details

API endpoints are implemented in:
- `src/api/lexicon_api.py` - Lexicon and term-related endpoints
- `src/web_app.py` - Web interface frontend routes

When running in development mode:
1. Start both servers with: `python start_servers.py`
2. Or start individual servers:
   - API server only: `python start_servers.py --api-only`
   - Web server only: `python start_servers.py --web-only`
3. Customize ports:
   - API port: `python start_servers.py --api-port 8000`
   - Web port: `python start_servers.py --web-port 8001`

The API server starts on http://localhost:5000 by default and the web server on http://localhost:5001.

> **Note**: The Flask applications are configured as `src.api.lexicon_api:app` for the API server and `src.web_app` for the web server. 