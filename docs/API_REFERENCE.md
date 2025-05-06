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