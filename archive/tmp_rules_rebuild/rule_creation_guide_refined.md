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

## Recommended Approach: Non-Interactive Batch Scripts

Due to limitations with interactive PowerShell scripts in some environments, the **most reliable** approach is to use batch scripts for rule management:

### For New Rules:

1. Create content file in `tmp_rules_rebuild/{rule_name}_content.txt`
2. Create batch script in `scripts/cursor_rules/create_{rule_name}_rule.bat`:

```batch
@echo off
REM Create the tmp_rules_rebuild directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Create the rule with frontmatter
echo ---                                                > .cursor\rules\{rule_name}.mdc
echo type: always                                      >> .cursor\rules\{rule_name}.mdc
echo title: Your Rule Title                            >> .cursor\rules\{rule_name}.mdc
echo description: Your rule description                >> .cursor\rules\{rule_name}.mdc
echo globs:                                            >> .cursor\rules\{rule_name}.mdc
echo   - "path/to/files/*.ext"                         >> .cursor\rules\{rule_name}.mdc
echo alwaysApply: true                                 >> .cursor\rules\{rule_name}.mdc
echo ---                                               >> .cursor\rules\{rule_name}.mdc
echo.                                                  >> .cursor\rules\{rule_name}.mdc

REM Append the content
type tmp_rules_rebuild\{rule_name}_content.txt         >> .cursor\rules\{rule_name}.mdc

echo {rule_name} rule created successfully.
```

3. Run the batch script to create the rule

### For Updating Rules:

1. Update content in `tmp_rules_rebuild/{rule_name}_content.txt`
2. Create/run batch script in `scripts/cursor_rules/update_{rule_name}_rule.bat`:

```batch
@echo off
REM Create the tmp_rules_rebuild directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Make sure the content file exists
if not exist tmp_rules_rebuild\{rule_name}_content.txt echo ERROR: Content file not found && exit /b 1

REM Update the rule with frontmatter
echo ---                                                > .cursor\rules\{rule_name}.mdc
echo type: always                                      >> .cursor\rules\{rule_name}.mdc
echo title: Your Rule Title                            >> .cursor\rules\{rule_name}.mdc
echo description: Your rule description                >> .cursor\rules\{rule_name}.mdc
echo globs:                                            >> .cursor\rules\{rule_name}.mdc
echo   - "path/to/files/*.ext"                         >> .cursor\rules\{rule_name}.mdc
echo alwaysApply: true                                 >> .cursor\rules\{rule_name}.mdc
echo ---                                               >> .cursor\rules\{rule_name}.mdc
echo.                                                  >> .cursor\rules\{rule_name}.mdc

REM Append the content
type tmp_rules_rebuild\{rule_name}_content.txt         >> .cursor\rules\{rule_name}.mdc

echo {rule_name} rule updated successfully.
```

## Alternative Methods (When Interactive Tools Work)

### Method 1: Using the Template and Direct Script

```powershell
# Create a new rule from template
.\scripts\cursor_rules\new_rule.ps1 -RuleName "my_new_rule"

# Update a rule's content only
.\scripts\cursor_rules\update_rule.ps1 -RuleName "my_rule" -ContentFile "path/to/content.txt"

# Update a rule's frontmatter and content
.\scripts\cursor_rules\update_rule.ps1 -RuleName "my_rule" -UpdateFrontmatter $true -Title "New Title" -Description "New description" -Globs @("glob1", "glob2") -AlwaysApply $true -ContentFile "path/to/content.txt"
```

### Method 2: Using the Management Script (If Interactive Input Works)

```powershell
.\scripts\cursor_rules\manage_rules.ps1
```

## Simplified Rule Generation Script

To automatically generate a batch script for updating a rule, use:

```powershell
.\scripts\cursor_rules\generate_rule_script.ps1 -RuleName "my_rule" -Title "Rule Title" -Description "Rule description" -Globs @("glob1", "glob2") -AlwaysApply $true -ContentFile "path/to/content.txt" -OutputScript "scripts/cursor_rules/update_my_rule.bat"
```

## Best Practices

1. **Always use batch scripts** for critical rule operations to avoid interactive input issues
2. **Pre-create content files** in the `tmp_rules_rebuild` directory
3. **Include proper frontmatter** with `type`, `title`, `description`, `globs`, and `alwaysApply`
4. **Set appropriate glob patterns** that match files where the rule should apply
5. **Use `alwaysApply: true`** for rules that should be automatically applied
6. **Document the purpose** of each rule clearly in its content
7. **Keep individual update scripts** for each rule for easy maintenance

## Troubleshooting

If rules aren't being applied:
1. Verify the frontmatter is properly formatted (no YAML syntax errors)
2. Check that the glob patterns match your files
3. Ensure `alwaysApply` is set correctly
4. Regenerate the rule using a batch script approach
5. Check for proper line endings and encoding issues in rule files
6. If using PowerShell scripts, ensure they're being run with proper execution policy 