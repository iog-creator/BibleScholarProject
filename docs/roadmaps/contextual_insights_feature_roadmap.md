# Contextual Insights Feature Roadmap

This document outlines the development plan for the Contextual Insights feature, which will provide users with rich, multi-faceted insights for Bible verses, topics, or text snippets.

## I. Feature Overview
The Contextual Insights feature uses direct LM Studio integration (via `query_lm_studio`) to provide a variety of insights for Bible study, including (DSPy-based modules may be added later):
- Summaries
- Cross-references
- Theological term explanations
- Historical context
- Original language notes
- Related entities (people, places)

## II. Phase 1: Core Components (COMPLETED)
- [x] **DSPy Signature Classes:**
    - [x] Define all required signature classes for each insight generator.
    - [x] Create modular components that can be optimized independently.
- [x] **Focus Processor:**
    - [x] Create a component to process user inputs (verse, topic, or text).
    - [x] Implement parsing for verse references.
    - [x] Add database retrieval for verse text.
- [x] **Insight Generator:**
    - [x] Develop the main component that orchestrates all insight generation.
    - [x] Implement each insight type (summary, cross-references, etc.).
    - [x] Add error handling for LLM-specific issues.

## III. Phase 2: API Interface (COMPLETED)
- [x] **Flask API Blueprint:**
    - [x] Create RESTful API endpoints for insights.
    - [x] Add documentation and example usage.
    - [x] Implement health check endpoint.
- [x] **Integration Testing:**
    - [x] Create test scripts for API functionality.
    - [x] Test with different input types.
    - [x] Verify response formats.
- [x] **Expanded API Tests:**
    - [x] Enhanced `test_contextual_insights.py` to cover multiple verses (`John 1:1`, `Genesis 1:1`, `Psalm 23:1`) and verify all insight fields.
    - [x] Assert `translation_variants` contains only `ASV`, `KJV`, `TAGNT`, `TAHOT` and excludes `ESV`.

## IV. Phase 3: LM Studio Minimal Integration (COMPLETED)
- [x] **Minimal LM Studio Integration:**
    - [x] Implemented `contextual_insights_minimal.py` to call LM Studio chat completions directly via `query_lm_studio`.
    - [x] Defined explicit JSON schema in request payload to ensure structured output for all insight types.
    - [x] Ensured `theological_terms` is returned as an object and all six insight fields are produced.
- [x] **API Integration & Testing:**
    - [x] Updated `contextual_insights_api.py` to import and use `query_lm_studio` for insights endpoint.
    - [x] Created and updated `test_contextual_insights.py` to validate all insight types without DSPy dependencies.
    - [x] Added `scripts/print_contextual_insights.py` helper for manual verification.

## V. Phase 4: Optimization (IN PROGRESS)
- [ ] **DSPy Optimization:**
    - [ ] Run optimization experiments for each insight generator.
    - [ ] Use MLflow to track model performance.
    - [ ] Select best models based on metrics.
- [x] **Original Language Integration:**
    - [x] Fix get_original_language_verse_text function for verse parsing.
    - [x] Implement get_original_language_verse_words for word-level data (tested, non-interactive, schema-mapped, Unicode-safe; terminal logging may show encoding errors but data is correct).
    - [x] Add 'theological_term' field to word-level data (tested, mapped for all words; enables downstream linking).
    - [x] Implement get_theological_term for Strong's ID to theological term mapping (tested, supports critical terms and lexicon fallback; enables downstream linking).
    - [x] Link Strong's IDs to theological terms automatically at the data layer. (**COMPLETE**)
    - [x] Propagate word-level data (original_language_words) to API for verse queries (all fields: surface, strongs_id, morphology, transliteration, gloss, theological_term; ready for UI integration). (**COMPLETE**)
    - [ ] Display word-level data in the web frontend. (**NEXT STEP**)
    - [ ] Add morphological tagging for original language words in downstream features. (**READY FOR DOWNSTREAM**)
- [x] **Performance Improvements:**
    - [x] Add caching for common verses/topics.
    - [ ] Optimize database queries.
    - [ ] Implement batching for multiple insights.

## VI. Phase 5: UI Integration (IN PROGRESS)
- [ ] **Web Frontend:**
    - [ ] Design UI components for displaying insights.
    - [ ] Create expandable/collapsible sections for each insight type.
    - [ ] Add loading indicators during generation.
- [ ] **Feedback Mechanism:**
    - [ ] Add user feedback collection for insight quality.
    - [ ] Create rating system to improve training data.
    - [ ] Implement logging for common failures.

## VII. Next Steps
- [x] JSON Schema compatibility fix for LM Studio integration (including CLI-driven troubleshooting and dynamic patch).
- [ ] Display word-level data with morphological tagging in the web frontend.
- [ ] Complete DSPy optimization experiments with MLflow tracking.
- [ ] Design and implement user feedback and rating mechanism in the UI frontend.

## VIII. Known Issues
1. ~~LM Studio requires a specific JSON schema format with 'json_schema' type and proper nesting structure.~~ (**RESOLVED**)
2. The original language text retrieval needs to parse verse references correctly.
3. DSPy's JSONAdapter doesn't support the required schema format for LM Studio. (**RESOLVED** by patch)
4. Flask Blueprint initialization needs to use before_app_request instead of before_app_first_request. (**RESOLVED**)

## IX. Success Metrics and Evaluation
- [x] **Basic Functionality:**
    - [x] System can generate insights for all three input types (verses, topics, text snippets).
    - [x] All insight types are implemented and provide meaningful content with correct JSON schema handling.
    - [x] API endpoints function without errors related to JSON schema handling.

- [ ] **Quality Metrics:**
    - [ ] **INCOMPLETE:** Theological accuracy of insights (to be evaluated by domain experts).
    - [ ] **INCOMPLETE:** Relevance of cross-references and related terms (precision/recall measures).
    - [ ] **INCOMPLETE:** User satisfaction ratings for generated insights.
    - [ ] **INCOMPLETE:** Performance metrics for response time and resource usage.

## X. Server Startup Standard

All server startup scripts (Flask, FastAPI, etc.) must:
- Check if the intended port is already in use (i.e., if the server is already running).
- If not running, start the server automatically in the background (non-blocking for the terminal/chat).
- Avoid duplicate server instances.

This is implemented via a shared utility in `src/utils/server_utils.py`:

```python
from src.utils.server_utils import start_server_if_not_running
start_server_if_not_running(5002, os.path.abspath(__file__))
```

**Scripts using this pattern:**
- `run_contextual_insights_web.py`
- `vector_search_web.py`

**Rationale:**
- Prevents accidental duplicate servers
- Ensures background, non-blocking startup for developer workflows
- Standardizes server management across the project

All new server scripts must follow this pattern.

## XI. Schema Compatibility Note

**The LM Studio JSON schema compatibility issue is now resolved.**
- The system now uses the correct `json_schema` type and nesting for all structured outputs.
- LM Studio accepts and processes structured outputs as expected.
- This enables robust, error-free integration for all downstream features. 