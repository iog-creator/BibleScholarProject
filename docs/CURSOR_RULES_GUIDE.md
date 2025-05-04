# Guide to Creating Cursor Rules for BibleScholarProject

This guide explains how to add new Cursor rules to the BibleScholarProject. Cursor rules help AI assistants understand project-specific standards and requirements, improving their ability to provide relevant code suggestions and maintain project consistency.

## What Are Cursor Rules?

Cursor rules are project-specific guidelines that are used by AI assistants in the Cursor IDE. They provide context about:

- Coding patterns and conventions
- Domain-specific terminology
- Project architecture and organization
- Custom workflows
- Critical requirements

## Rule File Structure

Cursor rules must follow this format:

1. **File Location**: Place all rule files in the `.cursor/rules/` directory
2. **File Extension**: Use `.mdc` extension (Markdown with Configuration)
3. **File Structure**: Each file must have:
   - YAML frontmatter section at the top
   - Markdown content below

### YAML Frontmatter Requirements

```yaml
---
description: Brief description of what the rule covers
globs: file/path/glob/patterns/*.py, another/path/*.js
alwaysApply: true
---
```

- **description**: Short description of the rule (required)
- **globs**: File patterns where the rule applies (required)
- **alwaysApply**: Set to `true` to always apply this rule, even if files don't match globs (optional)

## Adding New Rules

### Step 1: Create the Rules Directory (if it doesn't exist)

```powershell
mkdir -p .cursor/rules
```

### Step 2: Create a New Rule File

Create a new file with the `.mdc` extension in the `.cursor/rules/` directory. Name it descriptively based on its purpose:

```powershell
notepad .cursor\rules\new_rule_name.mdc
```

### Step 3: Add YAML Frontmatter

Start your rule file with proper YAML frontmatter:

```yaml
---
description: Description of your rule
globs: src/relevant/path/**/*.py, scripts/*related*.py
alwaysApply: true
---
```

### Step 4: Add Rule Content

Add your rule content in Markdown format below the YAML frontmatter. Include:

- Clear headings and subheadings
- Code examples in code blocks
- Lists of requirements or standards
- Explanations of domain-specific concepts

Example structure:

```markdown
# Rule Title

## Section 1
Explanation of the first aspect of the rule...

## Section 2
Code patterns that should be followed:

```python
# Example code showing the correct pattern
def correct_pattern():
    # Implementation
    pass
```

## Requirements
1. First requirement
2. Second requirement
3. Third requirement
```

### Step 5: Verify Rule Format

Ensure your rule file has:
1. Proper YAML frontmatter with required fields
2. Clear, well-structured Markdown content
3. Relevant code examples if applicable

### Step 6: Commit and Push

After creating your rule file:

```powershell
git add .cursor/rules/new_rule_name.mdc
git commit -m "Add new Cursor rule for [purpose]"
git push
```

## Troubleshooting Rule Files

If your rules aren't being recognized by Cursor:

1. **Check File Extension**: Ensure you're using `.mdc`, not `.md`
2. **Verify YAML Syntax**: Make sure the frontmatter has correct YAML syntax with no errors
3. **Validate Frontmatter**: Confirm the required fields (description, globs) are present
4. **Check Formatting**: Ensure there are three dashes (---) at the beginning and end of the frontmatter
5. **File Location**: Verify files are in the `.cursor/rules/` directory
6. **Encoding**: Save files with UTF-8 encoding

## Example: Adding a Database Access Rule

Here's a complete example of adding a new rule for database access patterns:

1. Create the file:
   ```powershell
   notepad .cursor\rules\database_access.mdc
   ```

2. Add content to the file:
   ```markdown
   ---
   description: Standards for database access patterns in the BibleScholarProject
   globs: src/database/**/*.py, src/**/models/*.py, scripts/db_*.py
   alwaysApply: true
   ---
   # Database Access Patterns

   ## Connection Management

   Always use the connection utility from database module:

   ```python
   from src.database.connection import get_db_connection

   def my_function():
       conn = get_db_connection()
       try:
           # Use connection
           cursor = conn.cursor()
           cursor.execute("SELECT * FROM table")
           results = cursor.fetchall()
           return results
       finally:
           conn.close()
   ```

   ## Query Construction

   1. Use parameterized queries for all user inputs
   2. Keep SQL statements readable with proper indentation
   3. Use explicit column names instead of wildcards
   ```

3. Commit and push:
   ```powershell
   git add .cursor\rules\database_access.mdc
   git commit -m "Add database access pattern Cursor rule"
   git push
   ```

## Best Practices for Cursor Rules

1. **Keep Rules Focused**: Each rule file should cover a specific aspect of the project
2. **Include Examples**: Provide clear code examples of correct patterns
3. **Explain Why**: Include rationale for critical requirements
4. **Update Rules**: Keep rules updated as project conventions evolve
5. **Use Descriptive Filenames**: Name rule files clearly based on their purpose
6. **Reference Rules**: In code comments and documentation, reference relevant rules

By following this guide, you can effectively add new Cursor rules to the BibleScholarProject, helping maintain consistency and quality across the codebase. 