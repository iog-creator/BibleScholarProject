# Cursor Rule Creation Guidelines

## Overview

This guide explains the standardized process for creating and maintaining Cursor rules in the BibleScholar project. Following these guidelines ensures consistent rule formatting and application.

## Standard Rule Structure

All cursor rules must follow this structure:

```markdown
---
type: always
title: Rule Title
description: Brief description
globs:
  - "path/pattern/*.ext"
alwaysApply: true|false
---

# Rule Content
```

## Creating New Rules

### Method 1: Using the Interactive Script (Recommended)

Run the interactive rule management script:

```powershell
.\scripts\cursor_rules\manage_rules.ps1
```

Select option 3 (Create new rule) and follow the prompts.

### Method 2: Using the Template

Run the new rule script with your rule name:

```powershell
.\scripts\cursor_rules\new_rule.ps1 -RuleName "my_new_rule"
```

This will create a rule from the template at `templates/cursor_rule_template.md`.

### Method 3: Direct Creation

Use the creation script directly:

```powershell
.\scripts\cursor_rules\create_rule.ps1 -RuleName "my_rule" -Title "My Rule" -Description "Description" -Globs @("src/**/*.py") -AlwaysApply $true
```

## Updating Existing Rules

### Method 1: Interactive Update

Use the rule management script:

```powershell
.\scripts\cursor_rules\manage_rules.ps1
```

Select option 4 (Update existing rule) and follow the prompts.

### Method 2: Direct Update

Update just the content:

```powershell
.\scripts\cursor_rules\update_rule.ps1 -RuleName "my_rule" -ContentFile "path/to/content.txt"
```

Or update frontmatter as well:

```powershell
.\scripts\cursor_rules\update_rule.ps1 -RuleName "my_rule" -UpdateFrontmatter $true -Title "New Title" -Globs @("new/pattern/*.py")
```

### Method 3: Generated Update Scripts

For each rule, a batch script is available:

```batch
.\scripts\cursor_rules\update_my_rule_rule.bat
```

## Best Practices

1. **Always include frontmatter** with `type`, `title`, `description`, `globs`, and `alwaysApply`
2. **Set appropriate glob patterns** that match files where the rule should apply
3. **Use `alwaysApply: true`** for rules that should be automatically applied
4. **Document the purpose** of each rule clearly in its content
5. **Include examples** of correct and incorrect implementations
6. **Review and test** rules before deployment

## Rule Organization

- Keep all rule content files in `tmp_rules_rebuild/{rule_name}_content.txt`
- Store all cursor rules in `.cursor/rules/{rule_name}.mdc`
- Document all rules in `docs/rules/README.md`

## Creating Effective Glob Patterns

- Use `**` for recursive directory matching: `src/**/*.py`
- Use `*` for wildcard matching: `*.py`
- Target specific directories: `src/etl/**/*.py`
- Use multiple patterns for comprehensive coverage

## Troubleshooting

If rules aren't being applied:
1. Verify the frontmatter is properly formatted
2. Check that the glob patterns match your files
3. Ensure `alwaysApply` is set correctly
4. Regenerate the rule using the management scripts 