# Cursor Rules Migration Instructions

## Current Status

We've started migrating information from regular Markdown (.md) files to proper Cursor rules in the MDC format (.mdc) format, but there's still work to be done. The goal is to properly set up Cursor rules so they appear in the Cursor IDE settings and can guide AI assistance effectively.

## Issues Identified

1. The new MDC rule files have been created but some have incomplete content:
   - `.cursor/rules/theological_terms.mdc`
   - `.cursor/rules/hebrew_rules.mdc`
   - `.cursor/rules/database_access.mdc`
   - `.cursor/rules/import_structure.mdc`

2. There are import errors affecting the application, showing "ModuleNotFoundError: No module named 'src'" when trying to run Python scripts directly.

## Next Steps

### 1. Complete the MDC Rule Files

For each .md file in the `.cursor/rules/` directory, create a corresponding .mdc file with:

1. First, create the file with proper YAML frontmatter:
   ```
   ---
   name: [Rule Name]
   description: [Brief description]
   globs: [File patterns where this rule applies]
   alwaysApply: true
   ---
   ```

2. Then add the content from the corresponding .md file.

Files to process:
- `column_names.md` → `column_names.mdc`
- `compatibility_rules.md` → `compatibility_rules.mdc`
- `database_rules.md` → `database_rules.mdc`
- `etl_rules.md` → `etl_rules.mdc`
- `fix_hebrew_strongs_ids_pattern.md` → `fix_hebrew_strongs_ids_pattern.mdc`
- `import_rules.md` → `import_rules.mdc`

### 2. Fix the Python Import Structure Rule

Review the import structure issue where Python scripts can't find the 'src' module. Add specific guidance to the `import_structure.mdc` rule file about handling this.

Common solutions:
- Add `sys.path.append()` to scripts
- Use Python's `-m` module flag to run scripts (e.g., `python -m src.web_app` instead of `python src/web_app.py`)
- Create a proper package with `setup.py` for development mode installation

### 3. Test and Verify the Rules

After creating all MDC files, verify they appear in Cursor settings:
1. Check if rules appear in Cursor's project rules section
2. Test if the AI correctly applies the rules when working with relevant files
3. Fix any issues with rule format or content

### 4. Import Error Fixes

Create a separate .mdc rule specifically for addressing the import errors. This should explain:
- How to properly import from the src package
- How to run scripts that avoid "No module named 'src'" errors
- Patterns for modifying scripts to use proper import paths

## File Creation Process

For each .md file, follow this process:
1. Read the original .md file to understand its purpose and content
2. Create a new .mdc file with appropriate YAML frontmatter
3. Transfer the content, ensuring any code examples are properly formatted
4. Add additional explanations or examples if needed
5. Commit the changes and push to the repository

## Resources

- Use `docs/CURSOR_RULES_GUIDE.md` as a reference for the correct MDC file format
- Example .mdc file structure is in the existing rule files
- Refer to the theological_terms.mdc and hebrew_rules.mdc files for formatting examples 