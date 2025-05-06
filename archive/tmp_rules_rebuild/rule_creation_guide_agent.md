# Cursor Rule Creation Guidelines

## Overview

This guide explains the standardized process for creating and maintaining Cursor rules in the BibleScholar project. These rules should be designed to be agent-friendly and only auto-attach when absolutely necessary.

## Standard Rule Structure

All cursor rules must follow this structure:

```markdown
---
type: always
title: Rule Title
description: Brief description
globs:
  - "path/pattern/*.ext"
alwaysApply: false
---

# Rule Content
```

## Important: Cautious Use of alwaysApply

The `alwaysApply` setting should be set to `true` **only when absolutely necessary**:

- **Use `alwaysApply: false` (default)** for most rules to allow agents to selectively apply them
- **Use `alwaysApply: true` only when** the rule must be applied automatically to all matching files (e.g., critical formatting, security rules)

Setting `alwaysApply: true` forces the rule to be applied in all contexts, which can:
1. Reduce agent flexibility
2. Create unnecessary processing overhead
3. Potentially conflict with other rules

## Agent-Friendly Rule Creation

### Method 1: Batch Script Creation (Recommended)

1. Create content file in `tmp_rules_rebuild/{rule_name}_content.txt`
2. Use the rule script generator:

```powershell
.\scripts\cursor_rules\generate_rule_script.ps1 -RuleName "my_rule" -Title "Rule Title" -Description "Rule description" -Globs @("glob1", "glob2") -AlwaysApply $false -ContentFile "path/to/content.txt"
```

3. Run the generated batch script:

```batch
.\scripts\cursor_rules\update_my_rule_rule.bat
```

### Method 2: Direct Manual Creation

```batch
@echo off
REM Create the rule with frontmatter
echo ---                                                > .cursor\rules\{rule_name}.mdc
echo type: always                                      >> .cursor\rules\{rule_name}.mdc
echo title: Your Rule Title                            >> .cursor\rules\{rule_name}.mdc
echo description: Your rule description                >> .cursor\rules\{rule_name}.mdc
echo globs:                                            >> .cursor\rules\{rule_name}.mdc
echo   - "path/to/files/*.ext"                         >> .cursor\rules\{rule_name}.mdc
echo alwaysApply: false                                >> .cursor\rules\{rule_name}.mdc
echo ---                                               >> .cursor\rules\{rule_name}.mdc
echo.                                                  >> .cursor\rules\{rule_name}.mdc

REM Append the content
type tmp_rules_rebuild\{rule_name}_content.txt         >> .cursor\rules\{rule_name}.mdc
```

## Effective Glob Patterns for Agents

Agents work best with precise glob patterns:

- **Be specific**: Use narrow patterns matching only relevant files
- **Avoid overly broad patterns**: Don't use patterns like `**/*.*` that match everything
- **Group related files**: Use patterns like `src/api/**/*.js` to target specific components
- **Consider file extensions**: Use patterns like `*.py` to target specific languages

## Best Practices for Agent-Friendly Rules

1. **Default to `alwaysApply: false`** unless there's a compelling reason otherwise
2. **Create focused rules** with clear, single purposes
3. **Use descriptive titles and descriptions** to help agents understand when to apply rules
4. **Provide examples in the rule content** showing correct implementation
5. **Document rule interactions or dependencies** with other rules
6. **Use specific glob patterns** that accurately target relevant files
7. **Keep rules concise** and easy to digest

## Rule Testing for Agent Compatibility

Before finalizing a rule:

1. Test with `alwaysApply: false` to verify it can be selectively applied
2. Verify the glob patterns match only the intended files
3. Ensure the content is clear and helpful for an agent to understand
4. Only set `alwaysApply: true` after confirming it's absolutely necessary

## Troubleshooting Agent Rule Issues

If agents aren't correctly using rules:

1. Verify the rule has a clear, descriptive title and description
2. Check that glob patterns are specific and accurate
3. Confirm `alwaysApply` is set appropriately (usually `false`)
4. Ensure rule content provides clear guidance and examples
5. Remove any vague or ambiguous instructions 