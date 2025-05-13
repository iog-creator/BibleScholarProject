# Create Cursor Rule Script

This document describes the `create_cursor_rule.py` script, which automates the creation and standardization of cursor rules in the BibleScholarProject.

## Purpose

The script streamlines the process of creating cursor rules (.mdc files) by:

1. Creating properly formatted MDC files with the correct frontmatter
2. Updating the available_rules.json file
3. Running the fix_mdc_files.py script to ensure standardization

## Usage

```bash
python scripts/create_cursor_rule.py rule_name "Rule Title" "Rule description" [glob1 glob2 ...]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `rule_name` | Name of the rule (used for file name) |
| `title` | Title of the rule |
| `description` | Description of the rule |
| `globs` | Glob patterns for files to apply the rule to (optional) |

### Options

| Option | Description |
|--------|-------------|
| `--always-apply` | Set alwaysApply to true (default: false) |
| `--content FILE` | File containing the content of the rule |
| `--type TYPE` | Type of the rule: 'restored' or 'always' (default: 'restored') |
| `--force` | Force overwrite if the file exists |

## Examples

### Create a basic rule

```bash
python scripts/create_cursor_rule.py vector_search "Vector Search" "Guidelines for vector search" 
```

### Create a rule with glob patterns

```bash
python scripts/create_cursor_rule.py vector_search "Vector Search" "Guidelines for vector search" "src/utils/vector_search.py" "src/api/vector_search_api.py"
```

### Create a rule with content from a file

```bash
python scripts/create_cursor_rule.py vector_search "Vector Search" "Guidelines for vector search" --content vector_search_content.md
```

### Force overwrite an existing rule

```bash
python scripts/create_cursor_rule.py vector_search "Vector Search" "Guidelines for vector search" --force
```

## Integration with Cursor

The script handles all the necessary steps to create cursor rules that will be recognized by Cursor:

1. Creates the .mdc file in the .cursor/rules directory
2. Updates the available_rules.json registry file
3. Applies standardization via fix_mdc_files.py

This ensures that new rules will be properly formatted and registered without the manual steps and potential issues encountered when doing this process manually.

## Troubleshooting

If you encounter issues:

1. Check the output of the script for error messages
2. Verify that .cursor/rules/available_rules.json exists
3. Ensure scripts/fix_mdc_files.py is available
4. Use the --force flag if you need to overwrite an existing rule 