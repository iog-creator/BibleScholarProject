# API Documentation for BibleScholarProject

This directory contains the REST API endpoints for the BibleScholarProject. The API provides programmatic access to Bible data, lexicons, morphology information, and more.

## API Structure

- `lexicon_api.py`: Main API module for lexicon access and search
- `cross_language_api.py`: API for cross-language term relationships
- `external_resources_api.py`: API for external biblical resources

## Endpoints

### Lexicon API

- `/api/lexicon/hebrew/{strongs_id}`: Get Hebrew lexicon entry
- `/api/lexicon/search`: Search lexicon entries
- `/api/lexicon/stats`: Get lexicon statistics
- `/api/theological_terms_report`: Get theological term statistics
- `/api/lexicon/hebrew/validate_critical_terms`: Validate critical Hebrew terms

### Morphology API

- `/api/morphology/hebrew`: Get Hebrew morphology codes
- `/api/morphology/greek`: Get Greek morphology codes
- `/api/morphology/hebrew/{code}`: Get Hebrew morphology code details
- `/api/morphology/greek/{code}`: Get Greek morphology code details

### Names API

- `/api/names`: Get biblical names
- `/api/names/search`: Search biblical names

### Cross-Language API

- `/api/cross_language/terms`: Get cross-language term relationships

## DSPy Training Data Integration

The API endpoints are integrated with the DSPy training data collection system to capture real user interactions as training data.

### How It Works

1. **Automatic Logging**: API endpoint calls are automatically logged using decorators
2. **Request Capture**: API request parameters are captured
3. **Response Capture**: API responses are captured
4. **Training Data Generation**: The data is formatted and added to DSPy training datasets

### Decorator Usage

```python
from scripts.log_user_interactions import log_api_endpoint

@app.route('/api/lexicon/hebrew/<strongs_id>', methods=['GET'])
@log_api_endpoint
def get_hebrew_entry(strongs_id):
    # API implementation
    # ...
    return jsonify(entry)
```

The `@log_api_endpoint` decorator automatically:
- Logs the endpoint path
- Captures request method and parameters
- Captures the response data
- Formats the interaction as a training example
- Adds it to the appropriate DSPy training dataset

### Manual Logging

You can also manually log API interactions:

```python
from scripts.log_user_interactions import log_api_interaction

# Log an API interaction
log_api_interaction(
    endpoint="/api/lexicon/hebrew/H7225",
    method="GET",
    params={},
    response={"strongs_id": "H7225", "lemma": "רֵאשִׁית"},
    success=True
)
```

### Generated Training Data

The logged API interactions are used to create various training examples:

1. **API Usage Examples**: How to use specific API endpoints
2. **Problem-Solution Pairs**: Common issues and their solutions
3. **Question-Answer Pairs**: Questions about the API and their answers

## Adding New API Endpoints

When adding new API endpoints, follow these guidelines:

1. **Apply the Decorator**: Add the `@log_api_endpoint` decorator to each endpoint
2. **Include Documentation**: Add clear docstrings explaining the endpoint
3. **Return Meaningful Errors**: Use standardized error responses
4. **Handle Edge Cases**: Consider and handle edge cases gracefully
5. **Test the Endpoint**: Include tests in the integration test suite

## Example Usage

### Python

```python
import requests

# Get a Hebrew lexicon entry
response = requests.get("http://localhost:5000/api/lexicon/hebrew/H7225")
data = response.json()
print(data)

# Search the lexicon
response = requests.get("http://localhost:5000/api/lexicon/search", 
                       params={"q": "beginning", "lang": "hebrew"})
results = response.json()
for entry in results:
    print(f"{entry['strongs_id']}: {entry['lemma']} - {entry['gloss']}")
```

### JavaScript

```javascript
// Get a Hebrew lexicon entry
fetch('http://localhost:5000/api/lexicon/hebrew/H7225')
  .then(response => response.json())
  .then(data => console.log(data));

// Search the lexicon
fetch('http://localhost:5000/api/lexicon/search?q=beginning&lang=hebrew')
  .then(response => response.json())
  .then(results => {
    results.forEach(entry => {
      console.log(`${entry.strongs_id}: ${entry.lemma} - ${entry.gloss}`);
    });
  });
```

## API Response Format

All API responses are in JSON format. Successful responses have the following structure:

```json
{
  "data": {
    // Response data specific to the endpoint
  }
}
```

Error responses have the following structure:

```json
{
  "error": "Error message",
  "status_code": 404
}
```

## Running the API Server

```bash
# Start only the API server
python start_servers.py --api-only

# Start both API and web servers
python start_servers.py

# Using Make
make run-api
```

The API server runs on http://localhost:5000 by default. 