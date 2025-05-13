# Server Startup Standard

All server startup scripts (Flask, FastAPI, etc.) must use the shared utility in `src/utils/server_utils.py` to:
- Check if the intended port is already in use (i.e., if the server is already running).
- If not running, start the server automatically in the background (non-blocking for the terminal/chat).
- Avoid duplicate server instances.

Reference: `docs/roadmaps/contextual_insights_feature_roadmap.md` section X.

Rationale:
- Prevents accidental duplicate servers
- Ensures background, non-blocking startup for developer workflows
- Standardizes server management across the project

All new server scripts must follow this pattern.

---

# Original Language Word-Level Data Standard

- The function `get_original_language_verse_words` is now the standard for retrieving word-level data for Hebrew and Greek verses.
- Implemented, tested, and non-interactive (no terminal prompts required).
- Fields: surface, lemma (None), strongs_id, morphology, transliteration, gloss, theological_term; all mapped to schema.
- Unicode/terminal logging caveat: Windows terminal may show encoding errors, but data is correct.
- The API now includes `original_language_words` for verse queries, with all fields, as the standard for downstream UI and feature integration.
- See roadmap (Phase 4) and `.cursor/rules/features/theological_terms.mdc` for details.

---

# Theological Term Mapping Standard

- The function `get_theological_term` is now implemented and tested.
- Returns the critical term name for key Hebrew Strong's IDs and the lexicon gloss/definition for all others.
- This is now the standard for linking Strong's IDs to theological terms in all downstream features.
- The function `get_original_language_verse_words` now includes a `theological_term` field for each word, fully tested and mapped.
- Strong's ID to theological term mapping is complete at the data layer.
- Next step: propagate theological term linking to API and UI.
- Morphological tagging is available at the data layer and ready for downstream use.
- See roadmap (Phase 4) and `.cursor/rules/features/theological_terms.mdc` for details. 