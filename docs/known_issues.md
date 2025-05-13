# Known Issues

## Missing Data for Psalms 23:1 and 23:4
- **Issue**: `lexical_data` is empty for `Psalm 23:1` and `Psalm 23:4` in the Contextual Insights API and web UI.
- **Details**:
  - `Psalm 23:1` exists in `bible.verses` (KJV, ASV) but has no entries in `bible.hebrew_ot_words`.
  - `Psalm 23:4` is missing from `bible.verses` entirely.
- **Impact**: No lexical data is displayed for these verses in the UI.
- **Research Findings**:
  - Data gaps in Psalms align with challenges in biblical scholarship, such as incomplete digitization and manuscript variations.
  - Missing lexical data often results from incomplete tagging, a common issue in digital Bible projects.
  - Absence of verses like `Psalm 23:4` may reflect manuscript differences or ETL issues from the source data (STEP Bible).
- **Resolution**: Requires ETL to reload or repair data for these verses.
- **Date Identified**: 2025-05-12

## Modification History
| Date | Change | Author |
|------|--------|--------|
| 2025-05-12 | Documented missing data for Psalms 23:1 and 23:4 | BibleScholar Team |
| 2025-05-12 | Added research findings on data gaps | BibleScholar Team |

## Missing /search Route in Web UI
- **Issue**: GET request to `/search?q=jesus+cast+the+first+stone` returns 404.
- **Details**: The `/search` route is not implemented in `run_contextual_insights_web.py`.
- **Impact**: Users cannot search for phrases via the UI.
- **Resolution**: Implement a `/search` route to handle text snippet queries.
- **Date Identified**: 2025-05-12

## Modification History
| Date | Change | Author |
|------|--------|--------|
| 2025-05-12 | Documented missing /search route | BibleScholar Team | 