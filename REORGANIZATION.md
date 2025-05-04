<<<<<<< HEAD
# BibleScholarProject Reorganization

## Recent Changes

### Added Missing Components (2023-05-05)

The following components were added from the root project:

1. `src/utils/` directory - Utility functions for file handling, logging, and database operations
2. Missing API files:
   - `src/api/proper_names_api.py`
   - `src/api/morphology_api.py`
   - `src/api/tagged_text_api.py`
3. `src/tvtms/` module - Translators' Versification and Textual Markup System processing
4. `src/web_app_minimal.py` - Minimal version of the web application
5. Updated `src/web_app.py` - Main web application

The Makefile was also updated to include targets for the new components (`etl-tvtms`, `run-minimal`).

### Removed Redundant Files (2023-05-04)

The following files were removed from the BibleScholarProject folder because they are duplicated in the root project directory:

1. `optimize_database.py` - Identical to the root version
2. `fix_extended_hebrew_strongs.py` - Identical to the root version
3. `process_lexicons.py` - Similar to the root version with minor differences in column names
4. `debug_lexicon.py` - Redundant with root version

## Recommendations

For future work:
1. Consolidate scripts in either the root directory or a dedicated `scripts` folder
2. Use relative imports to maintain a clean project structure
3. Consider standardizing the codebase to follow the BibleScholarProject structure
4. Update the Makefile to reference the correct script locations

## ETL Best Practices

- All ETL scripts should be kept in the `src/etl` directory
- Database utilities should be maintained in `src/database`
- Keep utility and test scripts separate from main application code
=======
# BibleScholarProject Reorganization

## Recent Changes

### Added Missing Components (2023-05-05)

The following components were added from the root project:

1. `src/utils/` directory - Utility functions for file handling, logging, and database operations
2. Missing API files:
   - `src/api/proper_names_api.py`
   - `src/api/morphology_api.py`
   - `src/api/tagged_text_api.py`
3. `src/tvtms/` module - Translators' Versification and Textual Markup System processing
4. `src/web_app_minimal.py` - Minimal version of the web application
5. Updated `src/web_app.py` - Main web application

The Makefile was also updated to include targets for the new components (`etl-tvtms`, `run-minimal`).

### Removed Redundant Files (2023-05-04)

The following files were removed from the BibleScholarProject folder because they are duplicated in the root project directory:

1. `optimize_database.py` - Identical to the root version
2. `fix_extended_hebrew_strongs.py` - Identical to the root version
3. `process_lexicons.py` - Similar to the root version with minor differences in column names
4. `debug_lexicon.py` - Redundant with root version

## Recommendations

For future work:
1. Consolidate scripts in either the root directory or a dedicated `scripts` folder
2. Use relative imports to maintain a clean project structure
3. Consider standardizing the codebase to follow the BibleScholarProject structure
4. Update the Makefile to reference the correct script locations

## ETL Best Practices

- All ETL scripts should be kept in the `src/etl` directory
- Database utilities should be maintained in `src/database`
- Keep utility and test scripts separate from main application code
>>>>>>> 7ce9bae97b2e6d0fe65169a363af093a8e5043a4
- TVTMS (versification and markup) processing should be handled by the `src/tvtms` module 