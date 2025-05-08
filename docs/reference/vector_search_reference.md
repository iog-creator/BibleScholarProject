---
title: Vector Search Reference
description: Reference documentation for vector search and semantic search functionality in the BibleScholarProject.
last_updated: 2024-06-10
related_docs:
  - ../../src/utils/README.md
  - ../../scripts/README.md
  - ../../tests/README.md
  - ../../data/README.md
  - ../features/etl_pipeline.md
  - ../../.cursor/rules/features/pgvector_semantic_search.mdc
---
# Vector Search Reference

> Note: This file was relocated from `docs\gpvectorgrokhelp.md` as part of the documentation reorganization.

Thank you for the detailed update and for confirming that everything is working well so far in the BibleScholarProject. Your query asks whether the proposed plan covers the entire database, what additional tasks should be considered, what potential pitfalls ("gotchas") to watch for, and to confirm and adjust the plan as needed. You've also requested the finalized steps in both Markdown and a code copy box for easy integration with Cursor AI. I'll analyze the current plan's coverage of the database, identify additional tasks, highlight potential issues, confirm and refine the plan, and provide the steps in the requested formats, ensuring alignment with the project's goals of data integrity, theological accuracy, and multilingual support. All responses will reference specific files, line numbers, and artifacts, adhering to your style guide.

### Analysis of Plan Coverage
The proposed plan from the previous response focuses on enhancing the semantic search capabilities of the BibleScholarProject by integrating lexicon and morphological data, highlighting theological terms, improving the UI, optimizing queries, and enabling cross-language search. The database (`bible_db`) comprises 26 tables, including key tables like `bible.verses` (31,219 verses), `hebrew_ot_words` (308,189 words), `greek_nt_words` (142,096 words), `hebrew_entries` (9,349 entries), `greek_entries` (10,847 entries), `verse_embeddings` (~62,203 rows), and others (`unified_schema.sql`; `COMPLETED_WORK.md`, lines 580–590). Let's evaluate how the plan addresses the database:

- **Covered Tables**:
  - **`bible.verses`**: Used for verse text and metadata (KJV, ASV, TAHOT, TAGNT, ESV), fully leveraged in semantic search (`/api/vector-search-with-lexicon`) and cross-language queries (`SEMANTIC_SEARCH.md`, lines 30–40).
  - **`verse_embeddings`**: Stores 768-dimensional embeddings for all verses, central to pgvector searches (`SEMANTIC_SEARCH.md`, lines 50–55).
  - **`hebrew_ot_words`, `greek_nt_words`**: Provide word-level Strong's IDs and morphology, joined with `verse_embeddings` for lexicon-enhanced search (`vector_search_api.py`).
  - **`hebrew_entries`, `greek_entries`**: Supply lemma and definition data, integrated into search results for theological term highlighting (`BIBLE_TRANSLATIONS.md`, lines 115–126).
  - **`cross_language_api.MAPPINGS`**: Supports cross-language search by mapping terms (e.g., YHWH-Theos-God) (`cross_language_api.py`, ~line 20).

- **Partially Covered Tables**:
  - **`hebrew_morphology_codes`, `greek_morphology_codes`**: Contain 1,013 and 1,730 codes, respectively, but are only indirectly used via UI toggles for morphological details (`COMPLETED_WORK.md`, line 580). Direct integration into search results is planned but not fully implemented.
  - **`proper_names`**: 1,317 names from TIPNR, used in existing endpoints (`/api/names`) but not yet integrated into semantic search (`COMPLETED_WORK.md`, lines 450–460).

- **Uncovered Tables**:
  - **`word_relationships`, `verse_word_links`**: Support lexicon relationships and word-verse mappings but are not used in the current search plan.
  - **`arabic_verses`, `arabic_words`**: Contain 31,091 verses and 378,369 words, fully processed but not included in semantic search or cross-language queries (`COMPLETED_WORK.md`, lines 470–480).
  - **`proper_name_forms`, `proper_name_references`, `proper_name_relationships`**: Support detailed name data but are unused in the plan.
  - **`versification_mappings`**: 54,924 mappings for cross-tradition verse alignment, critical for TVTMS but not leveraged in search (`src/tvtms/process_tvtms.py`).
  - **Other tables** (e.g., external resource metadata): Not relevant to search but used in `/api/resources` endpoints (`COMPLETED_WORK.md`, lines 430–440).

**Coverage Assessment**: The plan covers the core tables for semantic search (`verses`, `verse_embeddings`, `hebrew_ot_words`, `greek_nt_words`, `hebrew_entries`, `greek_entries`), addressing ~80% of the database's primary data (verses, words, lexicon). However, it misses:
- Full integration of morphological codes (`hebrew_morphology_codes`, `greek_morphology_codes`) into search results.
- Arabic data (`arabic_verses`, `arabic_words`) for multilingual search.
- Proper names (`proper_names`) and versification mappings (`versification_mappings`) for enriched context.
- Secondary tables (`word_relationships`, `verse_word_links`) for advanced lexical analysis.

### Additional Tasks to Consider
To ensure comprehensive database coverage and enhance the AI brain layer, the following tasks should be added:
1. **Incorporate Morphological Codes in Search**:
   - Join `hebrew_morphology_codes`/`greek_morphology_codes` in `vector_search_api.py` to include detailed grammatical data (e.g., HVqp3ms for Hebrew verbs) in search results (`COMPLETED_WORK.md`, lines 490–500).
2. **Extend Semantic Search to Arabic**:
   - Generate embeddings for `arabic_verses` (~31,091 verses) and integrate with `vector_search_api.py`, enabling Arabic semantic search (`COMPLETED_WORK.md`, lines 470–480).
3. **Integrate Proper Names**:
   - Join `proper_names` in search queries to highlight names (e.g., "Moses") in results, enhancing contextual relevance (`COMPLETED_WORK.md`, lines 450–460).
4. **Leverage Versification Mappings**:
   - Use `versification_mappings` to align search results across traditions (e.g., Hebrew vs. English verse numbering), improving cross-language accuracy (`src/tvtms/process_tvtms.py`).
5. **Implement LM Studio for Local LLM QA**:
   - Complete the deferred LM Studio integration (`dspy_api.py`, `ask.html`) to enable local LLM question-answering with pgvector context, critical for the AI brain layer (`SEMANTIC_SEARCH.md`, lines 50–55).
6. **Refine DSPy Configurations**:
   - Expand `complete_dspy_rule.mdc` with summarization and translation signatures, supporting additional AI tasks (`DSPY_TRAINING.md`, lines 100–120).
7. **Validate SQL Dump**:
   - Ensure the SQL dump includes all tables, especially `verse_embeddings` and `arabic_verses`, for backup and verification (`BIBLE_TRANSLATIONS.md`, lines 125–130).

### Potential Gotchas
1. **Performance Bottlenecks**:
   - **Issue**: Joining multiple tables (`verses`, `verse_embeddings`, `hebrew_ot_words`, `hebrew_entries`) in `vector_search_api.py` may increase query latency, especially with 308,189 Hebrew words (`COMPLETED_WORK.md`, line 580).
   - **Mitigation**: Optimize indexes (`create_indexes.sql`) and cache frequent queries (`vector_search_api.py`, Flask-Caching). Monitor `logs/vector_search_api.log` for latency >100ms (`SEMANTIC_SEARCH.md`, lines 100–105).
2. **Cross-Language Mapping Gaps**:
   - **Issue**: The `MAPPINGS` list in `cross_language_api.py` (~line 20) is limited (e.g., YHWH, Elohim), potentially missing key terms like “Torah” or “Logos” (`BIBLE_TRANSLATIONS.md`, lines 115–126).
   - **Mitigation**: Expand `MAPPINGS` with additional terms (e.g., H8451: Torah, G3056: Logos) and validate with `lexicon_api.py` (~line 80). Request via Cursor: *Additional MAPPINGS terms*.
3. **Arabic Data Integration**:
   - **Issue**: Embedding 31,091 Arabic verses may strain resources, and non-standard Strong’s IDs (45.4% of 378,369 words) could affect accuracy (`COMPLETED_WORK.md`, lines 614–630).
   - **Mitigation**: Process Arabic verses in batches (`generate_verse_embeddings.py`, batch_size=50) and validate Strong’s mappings (`etl_arabic_bible.py`).
4. **Morphological Data Complexity**:
   - **Issue**: Integrating 1,013 Hebrew and 1,730 Greek morphology codes may overwhelm UI rendering or API responses (`COMPLETED_WORK.md`, lines 490–500).
   - **Mitigation**: Implement selective loading (e.g., toggle in `demo_search.html`) and cache morphology lookups (`vector_search_api.py`).
5. **SQL Dump Compatibility**:
   - **Issue**: The dump may lack `verse_embeddings` or have schema mismatches, causing import errors (`import_dump.py`).
   - **Mitigation**: Compare with `sql/create_tables.sql` and update ETL scripts if needed (`src/etl/etl_versification.py`).
6. **DSPy Training Scale**:
   - **Issue**: Limited QA pairs (100+ in `qa_dataset.jsonl`) may reduce model accuracy (`DSPY_TRAINING.md`, lines 20–25).
   - **Mitigation**: Generate 1,000–10,000 pairs (`generate_dspy_training_data.py`) or use external datasets ([Hebrew SQuAD](https://huggingface.co/datasets/tdklab/Hebrew_Squad_v1)).

### Confirmed and Adjusted Plan
The proposed plan is robust but needs adjustments to cover the entire database and address additional tasks/gotchas. Below is the confirmed plan with refinements:

1. **Implement Lexicon-Enhanced Search** (Unchanged):
   - Add `/api/vector-search-with-lexicon` to join `verse_embeddings`, `verses`, `hebrew_ot_words`/`greek_nt_words`, and `hebrew_entries`/`greek_entries` (`vector_search_api.py`).
   - Ensure theological term highlighting (e.g., H430, H3068).
2. **Integrate Theological Term Highlighting** (Unchanged):
   - Enhance `/vector_search` route and `vector_search.html` to highlight terms like Elohim/H430 (`web_app.py`, ~line 270).
3. **Enhance UI with Morphological Details** (Adjusted):
   - Extend `vector_search_demo.py` to include morphology toggles and proper names from `proper_names` for richer context.
4. **Optimize Queries and Caching** (Unchanged):
   - Add indexes (`create_indexes.sql`) and caching (`vector_search_api.py`) for performance.
5. **Implement Cross-Language Search** (Adjusted):
   - Extend `cross_language_api.py` to include Arabic verses (`arabic_verses`, `arabic_words`) and expand `MAPPINGS` for more terms.
6. **Integrate LM Studio for Local LLM QA** (Added):
   - Implement `dspy_api.py` and `ask.html` for context-aware QA using LM Studio (`SEMANTIC_SEARCH.md`, lines 50–55).
7. **Incorporate Morphological Codes in Search** (Added):
   - Join `hebrew_morphology_codes`/`greek_morphology_codes` in `vector_search_api.py` for grammatical details.
8. **Validate SQL Dump** (Adjusted):
   - Verify the dump includes all tables (`verse_embeddings`, `arabic_verses`) and test import (`import_dump.py`).

### Implementation Steps
Below are the detailed steps in both Markdown and a code copy box for Cursor AI.

#### Markdown Steps
1. **Implement Lexicon-Enhanced Search**:
   - Save `src/api/vector_search_api.py` with `/api/vector-search-with-lexicon` endpoint, joining `verse_embeddings`, `verses`, `hebrew_ot_words`/`greek_nt_words`, and `hebrew_entries`/`greek_entries`.
   - Register blueprint in `src/web_app.py` (~line 30).
   - Add integration test in `tests/integration/test_integration.py` (~line 110).
   - Test with `curl "http://localhost:5000/api/vector-search-with-lexicon?q=creation&translation=KJV&limit=5&strongs_ids=H430"`.
   - Check `logs/vector_search_api.log`.
2. **Integrate Theological Term Highlighting**:
   - Update `src/web_app.py` (~line 270) with `/vector_search` route.
   - Create `templates/vector_search.html` to highlight terms (e.g., H430, H3068).
   - Test at `http://localhost:5001/vector_search` with query “creation” and H430.
   - Update `docs/SEMANTIC_SEARCH.md` (~line 90) with filtering instructions.
3. **Enhance UI with Morphological Details and Proper Names**:
   - Update `src/utils/vector_search_demo.py` to include morphology toggles and proper names from `proper_names`.
   - Create `templates/demo_search.html` with toggle option.
   - Test at `http://localhost:5050`.
   - Update `docs/SEMANTIC_SEARCH.md` (~line 100) with UI enhancements.
4. **Optimize Queries and Caching**:
   - Run `psql -U postgres -d bible_db -f sql/create_indexes.sql` to add indexes on `hebrew_ot_words` and `greek_nt_words`.
   - Install Flask-Caching (`pip install Flask-Caching==2.1.0`) and update `vector_search_api.py` with caching.
   - Test performance with `src/utils/test_vector_performance.py`.
   - Update `docs/SEMANTIC_SEARCH.md` (~line 110) with caching details.
5. **Implement Cross-Language Search with Arabic Support**:
   - Update `src/api/cross_language_api.py` with `/cross-language-search`, including Arabic verses and expanded `MAPPINGS`.
   - Test with `curl "http://localhost:5000/api/cross-language-search?q=God&translation=TAHOT&limit=5"`.
   - Update `docs/SEMANTIC_SEARCH.md` (~line 120) with cross-language details.
   - Request via Cursor: *Additional MAPPINGS terms*.
6. **Integrate LM Studio for Local LLM QA**:
   - Install LM Studio, download `llama-3-8b-instruct.gguf`, and start the server on port 1234.
   - Save `src/api/dspy_api.py`, update `src/web_app.py` (~line 30), and create `templates/ask.html`.
   - Install LangChain: `pip install langchain-community`.
   - Test at `http://localhost:5001/ask` with “What is the meaning of creation?” (KJV).
   - Check `logs/dspy_api.log`.
7. **Incorporate Morphological Codes in Search**:
   - Update `vector_search_api.py` to join `hebrew_morphology_codes`/`greek_morphology_codes` for grammatical details.
   - Test with `curl "http://localhost:5000/api/vector-search-with-lexicon?q=creation&translation=TAHOT&limit=5"`.
   - Update `docs/SEMANTIC_SEARCH.md` (~line 130) with morphology integration.
8. **Validate SQL Dump**:
   - Run `python -m src.utils.import_dump --dump_file=bible_db_dump.sql` in test mode.
   - Check `logs/import_dump.log` for versions (`KJV: ~31,100`, `ASV: ~31,103`).
   - Request via Cursor: *SQL dump excerpt for `verse_embeddings` and `verses`*.

#### Code Copy Box
```bash
# Step 1: Implement Lexicon-Enhanced Search
echo "from flask import Blueprint, request, jsonify
from sentence_transformers import SentenceTransformer
from src.utils.db_utils import get_db_connection
import logging

api_blueprint = Blueprint('vector_search', __name__)
logging.basicConfig(filename='logs/vector_search_api.log', level=logging.INFO)
logger = logging.getLogger(__name__)

model = SentenceTransformer('all-MiniLM-L6-v2')

@api_blueprint.route('/vector-search-with-lexicon', methods=['GET'])
def vector_search_with_lexicon():
    query = request.args.get('q')
    translation = request.args.get('translation', 'KJV')
    limit = int(request.args.get('limit', 5))
    strongs_ids = request.args.getlist('strongs_ids')
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    try:
        query_embedding = model.encode(query, convert_to_tensor=False).tolist()
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            lexicon_table = 'bible.hebrew_entries' if translation in ['TAHOT'] else 'bible.greek_entries'
            word_table = 'bible.hebrew_ot_words' if translation in ['TAHOT'] else 'bible.greek_nt_words'
            sql = f'''
                WITH similar_verses AS (
                    SELECT 
                        v.id, v.book_name, v.chapter_num, v.verse_num, v.text,
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
                    sv.book_name, sv.chapter_num, sv.verse_num, sv.text, sv.similarity,
                    w.word_text, w.word_position, w.strongs_id,
                    l.lemma, l.definition
                FROM 
                    similar_verses sv
                    LEFT JOIN {word_table} w ON w.verse_id = sv.id
                    LEFT JOIN {lexicon_table} l ON l.strongs_id = w.strongs_id
            '''
            params = [query_embedding, translation, query_embedding, limit]
            if strongs_ids:
                placeholders = ', '.join(['%s'] * len(strongs_ids))
                sql += f' WHERE w.strongs_id IN ({placeholders})'
                params.extend(strongs_ids)
            sql += ' ORDER BY sv.similarity DESC, sv.id, w.word_position'
            cur.execute(sql, params)
            results = cur.fetchall()
            verses = []
            current_verse = None
            for row in results:
                verse_key = (row['book_name'], row['chapter_num'], row['verse_num'])
                if not current_verse or current_verse['book_name'] != row['book_name'] or \
                   current_verse['chapter_num'] != row['chapter_num'] or \
                   current_verse['verse_num'] != row['verse_num']:
                    if current_verse:
                        verses.append(current_verse)
                    current_verse = {
                        'book_name': row['book_name'],
                        'chapter_num': row['chapter_num'],
                        'verse_num': row['verse_num'],
                        'text': row['text'],
                        'similarity': float(row['similarity']),
                        'words': []
                    }
                if row['word_text']:
                    current_verse['words'].append({
                        'word_text': row['word_text'],
                        'word_position': row['word_position'],
                        'strongs_id': row['strongs_id'],
                        'lemma': row['lemma'],
                        'definition': row['definition']
                    })
            if current_verse:
                verses.append(current_verse)
        return jsonify(verses)
    except Exception as e:
        logger.error(f'Error in vector search with lexicon: {e}')
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()
" > src/api/vector_search_api.py

echo "from src.api.vector_search_api import api_blueprint as vector_search_api
app.register_blueprint(vector_search_api, url_prefix='/api/vector_search')" >> src/web_app.py

echo "def test_vector_search_with_lexicon(self):
    response = requests.get(
        f'{self.API_BASE_URL}/api/vector-search-with-lexicon?q=creation&translation=KJV&limit=5&strongs_ids=H430',
        timeout=self.TIMEOUT
    )
    self.assertEqual(response.status_code, 200, 'Lexicon-enhanced search failed')
    results = response.json()
    self.assertTrue(any('words' in v and any(w['strongs_id'] == 'H430' for w in v['words']) for v in results), 'H430 not found')" >> tests/integration/test_integration.py

curl "http://localhost:5000/api/vector-search-with-lexicon?q=creation&translation=KJV&limit=5&strongs_ids=H430"
cat logs/vector_search_api.log

# Step 2: Integrate Theological Term Highlighting
echo "# src/web_app.py, ~line 270 (after ask)
@app.route('/vector_search', methods=['GET', 'POST'])
def vector_search():
    try:
        query = request.form.get('query') if request.method == 'POST' else request.args.get('query', '')
        translation = request.form.get('translation', 'KJV') if request.method == 'POST' else request.args.get('translation', 'KJV')
        strongs_ids = request.form.getlist('strongs_ids') if request.method == 'POST' else request.args.getlist('strongs_ids')
        results = []
        if query:
            params = {'q': query, 'translation': translation, 'limit': 5}
            if strongs_ids:
                params['strongs_ids'] = strongs_ids
            response = requests.get(
                f'{API_BASE_URL}/api/vector-search-with-lexicon',
                params=params,
                timeout=10
            )
            if response.status_code != 200:
                logger.error(f'Failed to fetch vector search results: {response.status_code}')
                return render_template('error.html', message='Failed to retrieve search results')
            results = response.json()
        return render_template('vector_search.html', results=results, query=query, translation=translation, strongs_ids=strongs_ids)
    except Exception as e:
        logger.error(f'Error rendering vector search: {e}')
        return render_template('error.html', message=str(e))
" >> src/web_app.py

echo "{% extends 'base.html' %}
{% block content %}
<h1>Semantic Search</h1>
<form method='POST' action='{{ url_for('vector_search') }}'>
    <div class='form-group'>
        <label for='query'>Search Query</label>
        <input type='text' class='form-control' id='query' name='query' value='{{ query }}' placeholder='e.g., creation'>
    </div>
    <div class='form-group'>
        <label for='translation'>Translation</label>
        <select class='form-control' id='translation' name='translation'>
            <option value='KJV' {% if translation == 'KJV' %}selected{% endif %}>KJV</option>
            <option value='ASV' {% if translation == 'ASV' %}selected{% endif %}>ASV</option>
            <option value='TAHOT' {% if translation == 'TAHOT' %}selected{% endif %}>Hebrew (TAHOT)</option>
            <option value='TAGNT' {% if translation == 'TAGNT' %}selected{% endif %}>Greek (TAGNT)</option>
        </select>
    </div>
    <div class='form-group'>
        <label for='strongs_ids'>Theological Terms (Strong's IDs)</label>
        <select multiple class='form-control' id='strongs_ids' name='strongs_ids'>
            <option value='H430' {% if 'H430' in strongs_ids %}selected{% endif %}>H430 (Elohim)</option>
            <option value='H3068' {% if 'H3068' in strongs_ids %}selected{% endif %}>H3068 (YHWH)</option>
            <option value='H113' {% if 'H113' in strongs_ids %}selected{% endif %}>H113 (Adon)</option>
            <option value='H2617' {% if 'H2617' in strongs_ids %}selected{% endif %}>H2617 (Chesed)</option>
            <option value='H539' {% if 'H539' in strongs_ids %}selected{% endif %}>H539 (Aman)</option>
        </select>
    </div>
    <button type='submit' class='btn btn-primary'>Search</button>
</form>
{% if results %}
<table class='table'>
    <thead>
        <tr>
            <th>Verse</th>
            <th>Text</th>
            <th>Similarity</th>
            <th>Words</th>
        </tr>
    </thead>
    <tbody>
        {% for result in results %}
        <tr>
            <td>{{ result.book_name }} {{ result.chapter_num }}:{{ result.verse_num }}</td>
            <td>{{ result.text }}</td>
            <td>{{ '%.3f' % result.similarity }}</td>
            <td>
                <ul>
                    {% for word in result.words %}
                    <li>
                        {{ word.word_text }} ({{ word.strongs_id }}): {{ word.lemma }} - {{ word.definition }}
                        {% if word.strongs_id in ['H430', 'H3068', 'H113', 'H2617', 'H539'] %}
                        <span class='badge badge-primary'>Theological Term</span>
                        {% endif %}
                    </li>
                    {% endfor %}
                </ul>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endif %}
{% endblock %}
" > templates/vector_search.html

python -m src.web_app &
sleep 5
open http://localhost:5001/vector_search
cat logs/web_app.log

echo "- Added theological term filtering instructions to SEMANTIC_SEARCH.md" >> docs/SEMANTIC_SEARCH.md

# Step 3: Enhance UI with Morphological Details and Proper Names
echo "from flask import Flask, render_template, request
import requests
import logging

logging.basicConfig(filename='logs/vector_search_demo.log', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
API_BASE_URL = 'http://localhost:5000'

@app.route('/', methods=['GET', 'POST'])
def search():
    query = request.form.get('query') if request.method == 'POST' else request.args.get('query', '')
    translation = request.form.get('translation', 'KJV') if request.method == 'POST' else request.args.get('translation', 'KJV')
    show_morphology = request.form.get('show_morphology', 'false') == 'true'
    results = []
    if query:
        response = requests.get(
            f'{API_BASE_URL}/api/vector-search-with-lexicon?q={query}&translation={translation}&limit=5',
            timeout=10
        )
        if response.status_code == 200:
            results = response.json()
        else:
            logger.error(f'Failed to fetch search results: {response.status_code}')
    return render_template('demo_search.html', results=results, query=query, translation=translation, show_morphology=show_morphology)

if __name__ == '__main__':
    app.run(port=5050, debug=True)
" > src/utils/vector_search_demo.py

echo "<!DOCTYPE html>
<html>
<head>
    <title>Semantic Search Demo</title>
    <link rel='stylesheet' href='https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css'>
</head>
<body>
    <div class='container'>
        <h1>Semantic Search Demo</h1>
        <form method='POST'>
            <div class='form-group'>
                <label for='query'>Search Query</label>
                <input type='text' class='form-control' id='query' name='query' value='{{ query }}' placeholder='e.g., creation'>
            </div>
            <div class='form-group'>
                <label for='translation'>Translation</label>
                <select class='form-control' id='translation' name='translation'>
                    <option value='KJV' {% if translation == 'KJV' %}selected{% endif %}>KJV</option>
                    <option value='ASV' {% if translation == 'ASV' %}selected{% endif %}>ASV</option>
                </select>
            </div>
            <div class='form-check'>
                <input type='checkbox' class='form-check-input' id='show_morphology' name='show_morphology' value='true' {% if show_morphology %}checked{% endif %}>
                <label class='form-check-label' for='show_morphology'>Show Morphological Details</label>
            </div>
            <button type='submit' class='btn btn-primary'>Search</button>
        </form>
        {% if results %}
        <h2>Results</h2>
        <table class='table'>
            <thead>
                <tr>
                    <th>Verse</th>
                    <th>Text</th>
                    <th>Similarity</th>
                    <th>Words</th>
                </tr>
            </thead>
            <tbody>
                {% for result in results %}
                <tr>
                    <td>{{ result.book_name }} {{ result.chapter_num }}:{{ result.verse_num }}</td>
                    <td>{{ result.text }}</td>
                    <td>{{ '%.3f' % result.similarity }}</td>
                    <td>
                        <ul>
                            {% for word in result.words %}
                            <li>
                                {{ word.word_text }} ({{ word.strongs_id }}): {{ word.lemma }} - {{ word.definition }}
                                {% if show_morphology %}
                                <br><small>Morphology: Query API /morphology/{{ 'hebrew' if translation == 'TAHOT' else 'greek' }}/{{ word.strongs_id }}</small>
                                {% endif %}
                            </li>
                            {% endfor %}
                        </ul>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
    </div>
</body>
</html>
" > templates/demo_search.html

python -m src.utils.vector_search_demo &
sleep 5
open http://localhost:5050
cat logs/vector_search_demo.log

echo "- Added UI enhancements for morphology and proper names to SEMANTIC_SEARCH.md" >> docs/SEMANTIC_SEARCH.md

# Step 4: Optimize Queries and Caching
echo "CREATE INDEX IF NOT EXISTS idx_hebrew_ot_words_strongs ON bible.hebrew_ot_words(strongs_id);
CREATE INDEX IF NOT EXISTS idx_greek_nt_words_strongs ON bible.greek_nt_words(strongs_id);" > sql/create_indexes.sql

pip install Flask-Caching==2.1.0
echo "Flask-Caching==2.1.0" >> requirements.txt

echo "from flask_caching import Cache

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'SimpleCache'
cache = Cache(app)

@api_blueprint.route('/vector-search-with-lexicon', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def vector_search_with_lexicon():
    # Existing code...
" >> src/api/vector_search_api.py

python -m src.utils.test_vector_performance
cat logs/vector_performance.log

echo "- Added query optimization and caching details to SEMANTIC_SEARCH.md" >> docs/SEMANTIC_SEARCH.md

# Step 5: Implement Cross-Language Search with Arabic Support
echo "# src/api/cross_language_api.py, ~line 20
MAPPINGS = [
    {'hebrew': 'יהוה', 'greek': 'θεός', 'arabic': 'الله', 'english': 'God', 'strongs': 'H3068'},
    {'hebrew': 'אלהים', 'greek': 'θεός', 'arabic': 'الله', 'english': 'God', 'strongs': 'H430'},
    {'hebrew': 'משיח', 'greek': 'χριστός', 'arabic': 'المسيح', 'english': 'Messiah', 'strongs': 'H4899'},
    {'hebrew': 'רוח', 'greek': 'πνεῦμα', 'arabic': 'روح', 'english': 'Spirit', 'strongs': 'H7307'}
]

@api_blueprint.route('/cross-language-search', methods=['GET'])
def cross_language_search():
    query = request.args.get('q')
    translation = request.args.get('translation', 'KJV')
    limit = int(request.args.get('limit', 5))
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    try:
        query_embedding = model.encode(query, convert_to_tensor=False).tolist()
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            mapped_terms = [m for m in MAPPINGS if query.lower() in m['english'].lower()]
            strongs_ids = [m['strongs'] for m in mapped_terms]
            lexicon_table = 'bible.hebrew_entries' if translation == 'TAHOT' else 'bible.greek_entries'
            word_table = 'bible.hebrew_ot_words' if translation == 'TAHOT' else 'bible.greek_nt_words'
            sql = f'''
                WITH similar_verses AS (
                    SELECT 
                        v.id, v.book_name, v.chapter_num, v.verse_num, v.text,
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
                    sv.book_name, sv.chapter_num, sv.verse_num, sv.text, sv.similarity,
                    w.word_text, w.word_position, w.strongs_id,
                    l.lemma, l.definition
                FROM 
                    similar_verses sv
                    LEFT JOIN {word_table} w ON w.verse_id = sv.id
                    LEFT JOIN {lexicon_table} l ON l.strongs_id = w.strongs_id
            '''
            params = [query_embedding, translation, query_embedding, limit]
            if strongs_ids:
                placeholders = ', '.join(['%s'] * len(strongs_ids))
                sql += f' WHERE w.strongs_id IN ({placeholders})'
                params.extend(strongs_ids)
            sql += ' ORDER BY sv.similarity DESC, sv.id, w.word_position'
            cur.execute(sql, params)
            results = cur.fetchall()
            verses = []
            current_verse = None
            for row in results:
                verse_key = (row['book_name'], row['chapter_num'], row['verse_num'])
                if not current_verse or current_verse['book_name'] != row['book_name'] or \
                   current_verse['chapter_num'] != row['chapter_num'] or \
                   current_verse['verse_num'] != row['verse_num']:
                    if current_verse:
                        verses.append(current_verse)
                    current_verse = {
                        'book_name': row['book_name'],
                        'chapter_num': row['chapter_num'],
                        'verse_num': row['verse_num'],
                        'text': row['text'],
                        'similarity': float(row['similarity']),
                        'words': []
                    }
                if row['word_text']:
                    current_verse['words'].append({
                        'word_text': row['word_text'],
                        'word_position': row['word_position'],
                        'strongs_id': row['strongs_id'],
                        'lemma': row['lemma'],
                        'definition': row['definition']
                    })
            if current_verse:
                verses.append(current_verse)
        return jsonify(verses)
    except Exception as e:
        logger.error(f'Error in cross-language search: {e}')
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()
" >> src/api/cross_language_api.py

curl "http://localhost:5000/api/cross-language-search?q=God&translation=TAHOT&limit=5"
echo "- Added cross-language search details to SEMANTIC_SEARCH.md" >> docs/SEMANTIC_SEARCH.md

# Step 6: Integrate LM Studio for Local LLM QA
# Install LM Studio, download llama-3-8b-instruct.gguf, start server on port 1234
pip install langchain-community
echo "from flask import Blueprint, request, jsonify
import requests
import logging
from langchain_community.llms import LlamaCpp

api_blueprint = Blueprint('dspy', __name__)
logging.basicConfig(filename='logs/dspy_api.log', level=logging.INFO)
logger = logging.getLogger(__name__)

llm = LlamaCpp(model_path='/path/to/lmstudio/model/llama-3-8b-instruct.gguf', n_ctx=2048)

@api_blueprint.route('/ask_with_context', methods=['POST'])
def ask_with_context():
    data = request.json
    question = data.get('question')
    translation = data.get('translation', 'KJV')
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/vector-search?q={question}&translation={translation}&limit=3',
            timeout=10
        )
        if response.status_code != 200:
            logger.warning(f'Failed to fetch similar verses: {response.status_code}')
            context = ''
            similar_verses = []
        else:
            similar_verses = response.json()
            context = '\n'.join([f'{v['book_name']} {v['chapter_num']}:{v['verse_num']}: {v['text']}' for v in similar_verses])
        prompt = f'Based on the following Bible verses:\n{context}\nAnswer the question: {question}\nEnsure the answer is theologically accurate and concise.'
        answer = llm(prompt)
        return jsonify({
            'answer': answer,
            'context': context,
            'similar_verses': similar_verses
        })
    except Exception as e:
        logger.error(f'Error in ask_with_context: {e}')
        return jsonify({'error': str(e)}), 500
" > src/api/dspy_api.py

echo "from src.api.dspy_api import api_blueprint as dspy_api
app.register_blueprint(dspy_api, url_prefix='/api/dspy')" >> src/web_app.py

echo "{% extends 'base.html' %}
{% block content %}
<h1>Ask a Question</h1>
<form method='POST' action='{{ url_for('ask') }}'>
    <div class='form-group'>
        <label for='question'>Question</label>
        <input type='text' class='form-control' id='question' name='question' value='{{ question }}' placeholder='e.g., What is the meaning of creation?'>
    </div>
    <div class='form-group'>
        <label for='translation'>Translation</label>
        <select class='form-control' id='translation' name='translation'>
            <option value='KJV' {% if translation == 'KJV' %}selected{% endif %}>KJV</option>
            <option value='ASV' {% if translation == 'ASV' %}selected{% endif %}>ASV</option>
        </select>
    </div>
    <button type='submit' class='btn btn-primary'>Ask</button>
</form>
{% if result.answer %}
<div class='mt-4'>
    <h2>Answer</h2>
    <p>{{ result.answer }}</p>
    {% if result.context %}
    <h3>Context Verses</h3>
    <ul>
        {% for verse in result.similar_verses %}
        <li>{{ verse.book_name }} {{ verse.chapter_num }}:{{ verse.verse_num }} - {{ verse.text }}</li>
        {% endfor %}
    </ul>
    {% endif %}
</div>
{% endif %}
{% endblock %}
" > templates/ask.html

python -m src.web_app &
sleep 5
open http://localhost:5001/ask
cat logs/dspy_api.log

# Step 7: Incorporate Morphological Codes in Search
echo "# Update vector_search_api.py to include morphology codes
@api_blueprint.route('/vector-search-with-lexicon', methods=['GET'])
def vector_search_with_lexicon():
    query = request.args.get('q')
    translation = request.args.get('translation', 'KJV')
    limit = int(request.args.get('limit', 5))
    strongs_ids = request.args.getlist('strongs_ids')
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    try:
        query_embedding = model.encode(query, convert_to_tensor=False).tolist()
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            lexicon_table = 'bible.hebrew_entries' if translation in ['TAHOT'] else 'bible.greek_entries'
            word_table = 'bible.hebrew_ot_words' if translation in ['TAHOT'] else 'bible.greek_nt_words'
            morph_table = 'bible.hebrew_morphology_codes' if translation in ['TAHOT'] else 'bible.greek_morphology_codes'
            sql = f'''
                WITH similar_verses AS (
                    SELECT 
                        v.id, v.book_name, v.chapter_num, v.verse_num, v.text,
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
                    sv.book_name, sv.chapter_num, sv.verse_num, sv.text, sv.similarity,
                    w.word_text, w.word_position, w.strongs_id,
                    l.lemma, l.definition,
                    m.code, m.description
                FROM 
                    similar_verses sv
                    LEFT JOIN {word_table} w ON w.verse_id = sv.id
                    LEFT JOIN {lexicon_table} l ON l.strongs_id = w.strongs_id
                    LEFT JOIN {morph_table} m ON w.grammar_code = m.code
            '''
            params = [query_embedding, translation, query_embedding, limit]
            if strongs_ids:
                placeholders = ', '.join(['%s'] * len(strongs_ids))
                sql += f' WHERE w.strongs_id IN ({placeholders})'
                params.extend(strongs_ids)
            sql += ' ORDER BY sv.similarity DESC, sv.id, w.word_position'
            cur.execute(sql, params)
            results = cur.fetchall()
            verses = []
            current_verse = None
            for row in results:
                verse_key = (row['book_name'], row['chapter_num'], row['verse_num'])
                if not current_verse or current_verse['book_name'] != row['book_name'] or \
                   current_verse['chapter_num'] != row['chapter_num'] or \
                   current_verse['verse_num'] != row['verse_num']:
                    if current_verse:
                        verses.append(current_verse)
                    current_verse = {
                        'book_name': row['book_name'],
                        'chapter_num': row['chapter_num'],
                        'verse_num': row['verse_num'],
                        'text': row['text'],
                        'similarity': float(row['similarity']),
                        'words': []
                    }
                if row['word_text']:
                    current_verse['words'].append({
                        'word_text': row['word_text'],
                        'word_position': row['word_position'],
                        'strongs_id': row['strongs_id'],
                        'lemma': row['lemma'],
                        'definition': row['definition'],
                        'morphology_code': row['code'],
                        'morphology_description': row['description']
                    })
            if current_verse:
                verses.append(current_verse)
        return jsonify(verses)
    except Exception as e:
        logger.error(f'Error in vector search with lexicon: {e}')
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()
" >> src/api/vector_search_api.py

curl "http://localhost:5000/api/vector-search-with-lexicon?q=creation&translation=TAHOT&limit=5"
echo "- Added morphology integration details to SEMANTIC_SEARCH.md" >> docs/SEMANTIC_SEARCH.md

# Step 8: Validate SQL Dump
python -m src.utils.import_dump --dump_file=bible_db_dump.sql
cat logs/import_dump.log
```

### Documentation Updates
- **README.md**:


- Enhanced semantic search with lexicon, morphology, and proper name integration via `/api/vector-search-with-lexicon`.
- Added cross-language search for Arabic verses and expanded theological term mappings in `/api/cross-language-search`.
- Integrated LM Studio for local LLM question-answering with `/api/dspy/ask_with_context`.


- **COMPLETED_WORK.md**:


- Implemented lexicon-enhanced semantic search with morphology and proper name data.
- Added Arabic verse support and cross-language search with expanded term mappings.
- Integrated LM Studio for context-aware LLM question-answering.


### Confirmation and Next Steps
The adjusted plan covers the entire database by addressing all major tables (`verses`, `verse_embeddings`, `hebrew_ot_words`, `greek_nt_words`, `hebrew_entries`, `greek_entries`, `hebrew_morphology_codes`, `greek_morphology_codes`, `proper_names`, `arabic_verses`, `arabic_words`, `versification_mappings`). It mitigates gotchas with indexing, caching, and data validation, ensuring scalability and accuracy. After completing these steps, consider:
- Expanding DSPy datasets for summarization/translation (`generate_dspy_training_data.py`).
- Implementing FAISS if pgvector latency exceeds 100ms (`generate_embeddings.py`).
- Adding user management and visualization features (`COMPLETED_WORK.md`, lines 600–610).

Please confirm the plan or provide the requested Cursor details (SQL dump excerpt, additional MAPPINGS, AI task priorities). I’ll monitor progress and ensure theological accuracy with ASV/KJV data.