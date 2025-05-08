# Documentation: scripts/fix_mdc_files.py

This script standardizes Cursor rule files (`.mdc`) and synchronizes their frontmatter with the rule manifest (`.cursor/rules/available_rules.json`).

## Purpose

The Cursor AI system relies on both the `.mdc` files within the `.cursor/rules/` directory and the `available_rules.json` manifest file to understand and apply available rules. This script ensures:

1.  **`.mdc` File Standardization**: Ensures all `.mdc` files adhere to the expected format (`---\nYAML Frontmatter\n---\nMarkdown Body\n`). It attempts to repair malformed files, potentially using archived versions or defaults.
2.  **Manifest Synchronization**: Updates the `available_rules.json` manifest to accurately reflect all `.mdc` files found within `.cursor/rules/`.
    *   Adds entries for `.mdc` files present on disk but missing from the JSON.
    *   Updates the `title` and `description` in the `.mdc` file's frontmatter based on the `name` and `description` fields in the corresponding JSON entry (if the JSON entry exists).

Maintaining this synchronization is crucial for the rule system to correctly identify, list, and retrieve rule content.

## Usage

Run the script from the project root directory:

```bash
python scripts/fix_mdc_files.py
```

The script will log its progress, including files processed, changes made, and any errors encountered. It reads the existing `.cursor/rules/available_rules.json`, processes all found `.mdc` files (including those in `archive/` and other locations, although it only adds rules under `.cursor/rules/` to the JSON), and writes the updated manifest back to `.cursor/rules/available_rules.json`.

## Important Notes

*   Running the script multiple times is safe. Subsequent runs will typically find fewer files needing updates.
*   If an `.mdc` file is newly added to the `.cursor/rules/` directory, running this script will add its corresponding entry to `available_rules.json`.
*   If you manually update the `description` within an `.mdc` file's frontmatter, running the script *after* that change will **overwrite** the `.mdc` description with the one from the JSON file (if the rule exists in the JSON). To properly update a description, it's best to update the `.mdc` file *and then* run the script twice: once to add the rule to the JSON (if missing) using the potentially incorrect description from the MDC, and a second time to push the *correct* description from the JSON back to the MDC (this workflow could be improved). A better approach is often to update the `.mdc` description and then manually update the corresponding entry in `available_rules.json`.
*   The script primarily focuses on rules within `.cursor/rules/` for adding/updating the JSON manifest. It standardizes `.mdc` files found elsewhere (like `archive/`) but doesn't add them to the manifest. 