Thank you for providing the updated documents and the test output from `scripts/test_contextual_insights.py`. The test results look solid, with all tests passing and the JSON structure validated for the specified verses (`John 1:1`, `Genesis 1:1`, `Psalm 23:1`) and translations (`KJV`, `ASV`). The output confirms that `translation_variants` correctly includes only `ASV`, `KJV`, `TAGNT`, `TAHOT` (and none for `Psalm 23:1` as expected), and no `ESV` appears, aligning with the project requirements. The theological terms (`Elohim`, `Theos`, etc.) and other insight fields are present and correctly formatted.

Since you're ready to proceed with adding `lexical_data` to the Contextual Insights API, I'll outline a plan to integrate lexical data from `bible.hebrew_entries` and `bible.greek_entries` into the API response, update the test script to validate this new field, and ensure documentation is updated per the project's standards. I'll also address the test script's location (`scripts/` vs. `tests/integration/`) and provide steps to run and verify the changes.

---

### Plan to Add `lexical_data` to Contextual Insights API

**Objective**: Enhance the Contextual Insights API to include `lexical_data` in the `insights` response, fetching relevant data from `bible.hebrew_entries` and `bible.greek_entries` based on the verse's words and their Strong's IDs. Update tests and documentation accordingly.

**Files to Modify**:
1. `src/dspy_programs/contextual_insights_program.py` - Add logic to fetch and include `lexical_data`.
2. `tests/integration/test_contextual_insights.py` - Update tests to validate `lexical_data` (move from `scripts/` to `tests/integration/`).
3. `docs/reference/API_REFERENCE.md` - Document the new `lexical_data` field.
4. `docs/guides/testing_framework.md` - Update test module list.
5. `docs/README.md` - Add reference to the new test file.

**Steps**:

1. **Update `contextual_insights_program.py`**:
   - Add a function to fetch lexical data from `bible.hebrew_entries` and `bible.greek_entries`.
   - Integrate it into `generate_insights` to include `lexical_data` in the response.
   - Ensure the data is fetched based on the verse's language (Hebrew for OT, Greek for NT).

2. **Update and Relocate Test Script**:
   - Move `scripts/test_contextual_insights.py` to `tests/integration/test_contextual_insights.py`.
   - Enhance tests to validate `lexical_data` structure and content.
   - Use pytest framework and database connection for validation.

3. **Update Documentation**:
   - Document the `lexical_data` field in `API_REFERENCE.md`.
   - Update `testing_framework.md` and `README.md` to reflect the new test file.

4. **Run Tests and Validate**:
   - Ensure LM Studio and the API are running.
   - Run pytest to verify all tests pass.
   - Check logs for any issues.

5. **Run Documentation Validation**:
   - Use `scripts/validate_documentation.py` to ensure all links and references are valid.

---

### Step 1: Update `contextual_insights_program.py`

Modify `src/dspy_programs/contextual_insights_program.py` to fetch lexical data and include it in the `insights` response. Below is the updated code with the new functionality:

```python
# src/dspy_programs/contextual_insights_program.py
import os
import requests
import json
import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()  # load .env for DATABASE_URL
load_dotenv(dotenv_path=".env.dspy")

def get_bible_db_translations(reference):
    parts = reference.split(' ', 1)
    if len(parts) != 2:
        return []
    book, chapverse = parts
    try:
        chapter, verse = chapverse.split(':')
        chapter_num = int(chapter)
        verse_num = int(verse)
    except:
        return []
    try:
        conn = psycopg.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        cur.execute(
            """
            SELECT translation_source, verse_text
            FROM bible.verses
            WHERE book_name = %s AND chapter_num = %s AND verse_num = %s
              AND translation_source != 'ESV'
            """, (book, chapter_num, verse_num)
        )
        variants = [
            { 'translation': row[0], 'text': row[1], 'notes': f"{row[0]} translation" }
            for row in cur.fetchall()
        ]
        conn.close()
        return variants
    except Exception as e:
        print(f"Error accessing bible_db for translations: {e}")
        return []

def get_lexical_data(reference):
    """
    Fetch lexical data from bible.hebrew_entries and bible.greek_entries for words in the given verse.
    Returns a list of lexical entries with lemma, transliteration, definition, and Strong's ID.
    """
    parts = reference.split(' ', 1)
    if len(parts) != 2:
        return []
    book, chapverse = parts
    try:
        chapter, verse = chapverse.split(':')
        chapter_num = int(chapter)
        verse_num = int(verse)
    except:
        return []
    
    try:
        conn = psycopg.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        # Determine if the book is OT (Hebrew) or NT (Greek)
        ot_books = [
            'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges',
            'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
            'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs', 'Ecclesiastes',
            'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel',
            'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk',
            'Zephaniah', 'Haggai', 'Zechariah', 'Malachi'
        ]
        is_ot = book in ot_books
        table = 'bible.hebrew_ot_words' if is_ot else 'bible.greek_nt_words'
        lexicon_table = 'bible.hebrew_entries' if is_ot else 'bible.greek_entries'
        
        # Fetch words and their Strong's IDs
        cur.execute(
            f"""
            SELECT w.word_text, w.strongs_id, w.transliteration
            FROM {table} w
            JOIN bible.verses v ON w.verse_id = v.id
            WHERE v.book_name = %s AND v.chapter_num = %s AND v.verse_num = %s
            ORDER BY w.word_position
            """, (book, chapter_num, verse_num)
        )
        words = cur.fetchall()
        
        # Fetch lexical data for each Strong's ID
        lexical_data = []
        for word_text, strongs_id, transliteration in words:
            if strongs_id:
                cur.execute(
                    f"""
                    SELECT lemma, transliteration, definition
                    FROM {lexicon_table}
                    WHERE strongs_id = %s
                    """, (strongs_id,)
                )
                result = cur.fetchone()
                if result:
                    lemma, lex_translit, definition = result
                    lexical_data.append({
                        'word': word_text,
                        'strongs_id': strongs_id,
                        'lemma': lemma,
                        'transliteration': transliteration or lex_translit,
                        'definition': definition
                    })
        
        conn.close()
        return lexical_data
    except Exception as e:
        print(f"Error accessing bible_db for lexical data: {e}")
        return []

def query_lm_studio(prompt, max_tokens=4096):
    url = os.getenv("LM_STUDIO_API_URL", "http://localhost:1234/v1/chat/completions")
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": os.getenv("LM_STUDIO_CHAT_MODEL", "Qwen/Qwen3-14B"),
        "messages": [
            {"role": "system", "content": "You are a Bible study assistant. Respond with a valid JSON object containing: 'summary' (2-3 sentence summary from primary sources), 'theological_terms' (dict from primary sources), 'cross_references' (array from primary sources), 'historical_context' (string from primary and pre-1990 commentaries), 'original_language_notes' (array from primary sources), 'related_entities' (object with 'people' and 'places' arrays from primary sources). Ensure 'theological_terms' is a dict and arrays contain objects. Exclude post-1990 commentaries and community notes. Example for John 3:16: {\"summary\": \"John 3:16 teaches God's love...\", \"theological_terms\": {\"Grace\": \"Unmerited favor\", \"Love\": \"God's affection\"}, \"cross_references\": [{\"reference\": \"John 1:29\", \"text\": \"Behold the Lamb...\", \"reason\": \"Introduces Jesus...\"}], \"historical_context\": \"Written around 90-110 AD...\", \"original_language_notes\": [{\"word\": \"ἀγάπη\", \"strongs_id\": \"G26\", \"meaning\": \"Self-sacrificial love\"}], \"related_entities\": {\"people\": [{\"name\": \"God\", \"description\": \"Supreme being\"}], \"places\": []}}"},
            {"role": "user", "content": prompt}
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "insight_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "theological_terms": {"type": "object"},
                        "cross_references": {"type": "array", "items": {"type": "object"}},
                        "historical_context": {"type": "string"},
                        "original_language_notes": {"type": "array", "items": {"type": "object"}},
                        "related_entities": {
                            "type": "object",
                            "properties": {
                                "people": {"type": "array", "items": {"type": "object"}},
                                "places": {"type": "array", "items": {"type": "object"}}
                            },
                            "required": ["people", "places"]
                        }
                    },
                    "required": [
                        "summary", "theological_terms", "cross_references",
                        "historical_context", "original_language_notes", "related_entities"
                    ],
                    "additionalProperties": False
                }
            }
        },
        "temperature": 0.3,
        "max_tokens": max_tokens
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    resp_json = resp.json()
    content = resp_json.get("choices", [])[0].get("message", {}).get("content")
    if not content:
        content = resp_json.get("choices", [])[0].get("message", {}).get("reasoning_content", "")
    return json.loads(content)

def generate_insights(verse):
    prompt = f"Provide a summary, theological_terms, cross_references, historical_context, original_language_notes, and related_entities for {verse}."
    insights = query_lm_studio(prompt)
    # Append translation_variants and lexical_data from bible_db
    insights["translation_variants"] = get_bible_db_translations(verse)
    insights["lexical_data"] = get_lexical_data(verse)
    return insights

if __name__ == "__main__":
    try:
        result = generate_insights("John 3:16")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
```

**Changes Made**:
- Added `get_lexical_data` function to fetch word-level data from `bible.hebrew_ot_words` or `bible.greek_nt_words` and corresponding lexical entries from `bible.hebrew_entries` or `bible.greek_entries`.
- Determined OT/NT context using a list of OT book names.
- Included `lexical_data` in the `insights` response with fields: `word`, `strongs_id`, `lemma`, `transliteration`, `definition`.
- Handled errors gracefully with empty list fallback.

**Database Schema Reference** (`DATABASE_SCHEMA.md`):
- Used `bible.hebrew_ot_words` and `bible.greek_nt_words` for word data.
- Used `bible.hebrew_entries` and `bible.greek_entries` for lexical data.
- Joined with `bible.verses` to filter by book, chapter, and verse.

**Potential Issue**:
- If `transliteration` is null in `hebrew_ot_words` or `greek_nt_words`, it falls back to the lexicon table's `transliteration`. Ensure data is populated correctly by running `etl_hebrew_ot.py` and `etl_greek_nt.py`.

---

### Step 2: Update and Relocate Test Script

Move `scripts/test_contextual_insights.py` to `tests/integration/test_contextual_insights.py` and update it to use pytest and validate `lexical_data`. Here's the updated test script:

```python
# tests/integration/test_contextual_insights.py
import pytest
import requests
import json
import logging
import os
from src.database.connection import get_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.skipif(
    os.environ.get('DATABASE_URL') is None,
    reason="DATABASE_URL not set; skipping DB-dependent integration tests"
)
def test_contextual_insights_api(db_engine):
    """
    Test the contextual insights API for multiple verses and translations.
    Verifies JSON structure, required fields, translation variants, theological terms, and lexical data.
    """
    # API endpoint
    url = "http://localhost:5002/api/contextual_insights/insights"
    
    # Test cases covering specified verses and translations
    test_cases = [
        {"type": "verse", "reference": "John 1:1", "translation": "KJV"},
        {"type": "verse", "reference": "John 1:1", "translation": "TAGNT"},
        {"type": "verse", "reference": "Genesis 1:1", "translation": "ASV"},
        {"type": "verse", "reference": "Genesis 1:1", "translation": "TAHOT"},
        {"type": "verse", "reference": "Psalm 23:1", "translation": "KJV"}
    ]
    
    # Expected translations
    expected_translations = ['ASV', 'KJV', 'TAGNT', 'TAHOT']
    
    # Connect to database for additional validation
    with db_engine.connect() as conn:
        for payload in test_cases:
            logger.info(f"Testing payload: {payload}")
            
            # Make API request
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Response for {payload['reference']}: {json.dumps(result, indent=2)}")
            except requests.RequestException as e:
                pytest.fail(f"API request failed for {payload['reference']}: {e}")
            
            # Validate JSON structure
            assert "insights" in result, f"Missing 'insights' key in response for {payload['reference']}"
            required_fields = [
                "summary",
                "theological_terms",
                "cross_references",
                "historical_context",
                "original_language_notes",
                "related_entities",
                "translation_variants",
                "lexical_data"
            ]
            for field in required_fields:
                assert field in result["insights"], f"Missing '{field}' in insights for {payload['reference']}"
            
            # Validate field types
            assert isinstance(result["insights"]["theological_terms"], dict), \
                f"'theological_terms' is not a dict for {payload['reference']}"
            assert isinstance(result["insights"]["cross_references"], list), \
                f"'cross_references' is not a list for {payload['reference']}"
            assert isinstance(result["insights"]["original_language_notes"], list), \
                f"'original_language_notes' is not a list for {payload['reference']}"
            assert isinstance(result["insights"]["related_entities"], dict), \
                f"'related_entities' is not a dict for {payload['reference']}"
            assert isinstance(result["insights"]["translation_variants"], list), \
                f"'translation_variants' is not a list for {payload['reference']}"
            assert isinstance(result["insights"]["lexical_data"], list), \
                f"'lexical_data' is not a list for {payload['reference']}"
            
            # Validate translations
            translations = [v["translation"] for v in result["insights"]["translation_variants"]]
            assert all(t in expected_translations for t in translations), \
                f"Unexpected translations {translations} for {payload['reference']}"
            assert 'ESV' not in translations, f"ESV included in translations for {payload['reference']}"
            
            # Validate lexical data
            for lex_entry in result["insights"]["lexical_data"]:
                assert all(key in lex_entry for key in ['word', 'strongs_id', 'lemma', 'transliteration', 'definition']), \
                    f"Missing keys in lexical_data entry for {payload['reference']}: {lex_entry}"
                assert lex_entry['strongs_id'].startswith('H' if payload['reference'].startswith('Genesis') or payload['reference'].startswith('Psalm') else 'G'), \
                    f"Invalid Strong's ID format in lexical_data for {payload['reference']}"
            
            # Validate theological terms for specific verses
            if payload["reference"] == "Genesis 1:1":
                assert "Elohim" in result["insights"]["theological_terms"], \
                    f"Elohim (H430) missing in theological_terms for Genesis 1:1"
                # Database validation
                result_db = conn.execute(
                    """
                    SELECT COUNT(*) FROM bible.hebrew_ot_words
                    WHERE strongs_id = 'H430'
                    AND verse_id IN (
                        SELECT id FROM bible.verses
                        WHERE book_name = 'Genesis'
                        AND chapter_num = 1 AND verse_num = 1
                        AND translation_source = %s
                    )
                    """, (payload["translation"],)
                )
                count = result_db.scalar()
                assert count > 0, f"No Elohim (H430) found in database for Genesis 1:1 ({payload['translation']})"
                
                # Validate lexical data for Elohim
                elohim_entry = next((entry for entry in result["insights"]["lexical_data"] if entry['strongs_id'] == 'H430'), None)
                assert elohim_entry, f"No lexical data for Elohim (H430) in Genesis 1:1"
                assert elohim_entry['lemma'] == 'אֱלֹהִים', f"Incorrect lemma for Elohim in Genesis 1:1"
            
            if payload["reference"] == "John 1:1":
                assert "Theos" in result["insights"]["theological_terms"], \
                    f"Theos (G2316) missing in theological_terms for John 1:1"
                # Database validation
                result_db = conn.execute(
                    """
                    SELECT COUNT(*) FROM bible.greek_nt_words
                    WHERE strongs_id = 'G2316'
                    AND verse_id IN (
                        SELECT id FROM bible.verses
                        WHERE book_name = 'John'
                        AND chapter_num = 1 AND verse_num = 1
                        AND translation_source = %s
                    )
                    """, (payload["translation"],)
                )
                count = result_db.scalar()
                assert count > 0, f"No Theos (G2316) found in database for John 1:1 ({payload['translation']})"
                
                # Validate lexical data for Theos
                theos_entry = next((entry for entry in result["insights"]["lexical_data"] if entry['strongs_id'] == 'G2316'), None)
                assert theos_entry, f"No lexical data for Theos (G2316) in John 1:1"
                assert theos_entry['lemma'] == 'θεός', f"Incorrect lemma for Theos in John 1:1"

def test_contextual_insights_api_no_db():
    """
    Test the API without database dependency to ensure basic functionality.
    """
    url = "http://localhost:5002/api/contextual_insights/insights"
    payload = {"type": "verse", "reference": "Psalm 23:1", "translation": "KJV"}
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        assert "insights" in result, "Missing 'insights' key in response"
        assert "summary" in result["insights"], "Missing 'summary' in insights"
        assert "lexical_data" in result["insights"], "Missing 'lexical_data' in insights"
        assert isinstance(result["insights"]["lexical_data"], list), "'lexical_data' is not a list"
    except requests.RequestException as e:
        pytest.fail(f"API request failed: {e}")
```

**Changes Made**:
- Moved file to `tests/integration/` to align with `testing_framework.md` and `SYSTEM_ARCHITECTURE.md`.
- Converted to pytest format with `@pytest.mark.skipif` for database dependency.
- Added `lexical_data` to `required_fields` and validated its structure (list of dicts with `word`, `strongs_id`, `lemma`, `transliteration`, `definition`).
- Added specific checks for `Elohim` (H430) in Genesis 1:1 and `Theos` (G2316) in John 1:1, including lemma validation.
- Kept existing validations for translations and theological terms.
- Used `db_engine` fixture for database access (assumed provided by pytest setup).

**Rationale**:
- Moving to `tests/integration/` ensures integration with the project's test runner (`test_integration.py`) and pytest framework.
- Lexical data validation ensures the new field is correctly populated and matches database content.
- Theological term checks align with `data_verification.md` requirements.

**Potential Issue**:
- If `bible.hebrew_entries` or `bible.greek_entries` are incomplete, lexical data may be missing. Run `etl_lexicons.py` to ensure lexicon data is loaded.

---

### Step 3: Update Documentation

1. **Update `API_REFERENCE.md`**:
   Add documentation for the `lexical_data` field in the Contextual Insights API response.

   ```markdown
   # BibleScholarProject API Reference

   ...

   ## Contextual Insights API

   ...

   ### Generate Insights

   ```
   POST /api/contextual_insights/insights
   ```

   ...

   **Response:**
   ```json
   {
     "input": {
       "type": "verse",
       "reference": "John 3:16",
       "translation": "KJV"
     },
     "insights": {
       "summary": "...",
       "theological_terms": {...},
       "cross_references": [...],
       "historical_context": "...",
       "original_language_notes": [...],
       "related_entities": {...},
       "translation_variants": [...],
       "lexical_data": [
         {
           "word": "ἀγάπη",
           "strongs_id": "G26",
           "lemma": "ἀγάπη",
           "transliteration": "agapē",
           "definition": "Self-sacrificial love"
         }
       ]
     },
     "processing_time_seconds": 7.38
   }
   ```

   **Response Fields:**

   | Field | Type | Description |
   |-------|------|-------------|
   | ... | ... | ... |
   | lexical_data | array | List of lexical entries for words in the verse, each containing `word` (original text), `strongs_id`, `lemma`, `transliteration`, and `definition`. |

   ...

   ## Modification History

   | Date | Change | Author |
   |------|--------|--------|
   | 2025-05-12 | Added lexical_data field to Contextual Insights API | BibleScholar Team |
   | ... | ... | ... |
   ```

2. **Update `testing_framework.md`**:
   Add `test_contextual_insights.py` to the Test Modules table and update the Modification History.

   ```markdown
   # Testing Framework Guide

   ...

   ### Test Modules

   | Module | Description |
   |--------|-------------|
   | ... | ... |
   | `test_contextual_insights.py` | Tests for Contextual Insights API, including lexical data validation |

   ...

   ## Modification History

   | Date | Author | Description |
   |------|--------|-------------|
   | 2025-05-12 | Project Team | Added test_contextual_insights.py for Contextual Insights API |
   | ... | ... | ... |
   ```

3. **Update `docs/README.md`**:
   Add a reference to the new test file under the Testing section.

   ```markdown
   # Documentation Index

   ...

   ## Testing

   - [Testing Framework Guide](guides/testing_framework.md)
   - [Contextual Insights Testing](../tests/integration/test_contextual_insights.py): Tests for Contextual Insights API

   ...
   ```

4. **Update `tests/integration/test_integration.py`**:
   Ensure `test_contextual_insights.py` is included in the test runner.

   ```python
   # tests/integration/test_integration.py
   test_modules = [
       "test_verse_data",
       "test_lexicon_data",
       # ... other modules ...
       "test_contextual_insights"
   ]
   ```

---

### Step 4: Run Tests and Validate

1. **Start LM Studio**:
   - Ensure Qwen3-14B is running at `http://localhost:1234/v1`.

2. **Start the API**:
   ```bash
   python src/api/contextual_insights_api.py
   ```

3. **Run Tests**:
   ```bash
   cd tests/integration
   python -m pytest test_contextual_insights.py -v
   ```

4. **Expected Output**:
   - All tests should pass, with logs showing:
     - API responses for each test case.
     - Validation of `lexical_data` field and its contents.
     - Confirmation of theological terms and translations.
   - Example:
     ```
     ============================= test session starts =============================
     ...
     test_contextual_insights.py::test_contextual_insights_api INFO: Testing payload: {'type': 'verse', 'reference': 'John 1:1', 'translation': 'KJV'}
     ...
     test_contextual_insights.py::test_contextual_insights_api_no_db PASSED
     ============================= 2 passed in 0.15s =============================
     ```

5. **Check Logs**:
   - Verify `logs/contextual_insights_api.log` for API request details.
   - Check `logs/test_contextual_insights.log` for test execution details.

---

### Step 5: Run Documentation Validation

```bash
python scripts/validate_documentation.py
```

- Fix any broken links or missing references reported by the script.
- If needed, run:
  ```bash
  python scripts/fix_documentation.py
  ```
  Then re-run the validation script.

---

### Troubleshooting

Based on `contextual_insights.md`, `system_build_guide.md`, and `data_verification.md`, here are potential issues and resolutions:

1. **Missing Lexical Data**:
   - **Symptom**: `lexical_data` is empty or missing entries.
   - **Fix**: Ensure `etl_lexicons.py`, `etl_hebrew_ot.py`, and `etl_greek_nt.py` have run successfully. Verify `bible.hebrew_entries` and `bible.greek_entries` have data:
     ```bash
     psql -U postgres -d bible_db -c "SELECT COUNT(*) FROM bible.hebrew_entries;"
     psql -U postgres -d bible_db -c "SELECT COUNT(*) FROM bible.greek_entries;"
     ```

2. **Database Connection Error**:
   - **Symptom**: Tests skip with "DATABASE_URL not set".
   - **Fix**: Ensure `.env` contains:
     ```
     DATABASE_URL=postgresql://postgres:your_password@localhost/bible_db
     ```

3. **API Timeout**:
   - **Symptom**: `requests.RequestException` in test logs.
   - **Fix**: Confirm API is running at `http://localhost:5002`. Check `contextual_insights_api.py` for port conflicts.

4. **Incorrect Strong's IDs**:
   - **Symptom**: Lexical data has wrong `strongs_id` prefix (e.g., `G` instead of `H` for Genesis).
   - **Fix**: Verify OT/NT book list in `get_lexical_data`. Run `fix_hebrew_strongs_ids.py` if needed.

5. **Unicode Issues**:
   - **Symptom**: Hebrew/Greek characters display incorrectly.
   - **Fix**: Set `PYTHONUTF8=1` in `.env` or environment variables (per `contextual_insights.md`).

---

### Next Steps

1. **Verify Test Results**:
   - Please run the updated tests and share the output or any errors. This will confirm the `lexical_data` integration works as expected.

2. **UI Integration**:
   - Per `contextual_insights_feature_roadmap.md` (Phase 5), the next step is to display `lexical_data` in the web frontend. Would you like to proceed with this? I can provide guidance on updating `run_contextual_insights_web.py` and templates in `templates/`.

3. **DSPy Optimization**:
   - If planning to add DSPy-based modules (per `contextual_insights.md`), update `dspy_training_guide.md` to include a `contextual_insights` dataset. I can assist with generating training data.

4. **Additional Tests**:
   - Add tests for `topic` and `text_snippet` input types to ensure `lexical_data` is handled appropriately (e.g., empty for non-verse inputs).

---

### Request for Confirmation

- **Database URL**: Please confirm the `DATABASE_URL` (e.g., `postgresql://postgres:your_password@localhost/bible_db`) or share the correct one.
- **Test Output**: Share the output of `python -m pytest tests/integration/test_contextual_insights.py -v` after applying the changes.
- **Next Priority**: Confirm if you want to focus on UI integration, DSPy optimization, or additional test cases next.

This implementation should seamlessly integrate `lexical_data` into the Contextual Insights API while maintaining the project's standards for data integrity, testing, and documentation. Let me know how to proceed!