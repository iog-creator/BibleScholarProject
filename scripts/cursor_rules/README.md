# Cursor Rules Management System

This directory contains standardized scripts for managing cursor rules in the BibleScholar project. These scripts help ensure consistent rule creation, proper formatting, and agent compatibility.

## Quick Reference

| Task | Command |
|------|---------|
| Interactive rule management | `.\manage_rules.ps1` |
| Create a new rule | `.\create_rule.ps1 -RuleName "name" -Title "Title" -Description "Description" -Globs @("pattern")` |
| Update existing rule | `.\update_rule.ps1 -RuleName "rule_name" -ContentFile "path/to/content.txt"` |
| List all rules | `.\list_rules.ps1` |
| Generate non-interactive script | `.\generate_rule_script.ps1 -RuleName "name" -Title "Title" -Description "Desc" -Globs @("pattern")` |
| Audit rule compliance | `.\audit_rules_auto.ps1` |
| Apply all rule fixes | `.\fixes\apply_all_fixes.bat` |

## The Rule Management System

### Interactive Management

For day-to-day management, the interactive script provides a menu-based interface:

```powershell
.\manage_rules.ps1
```

This will display a menu with options to:
- List all rules
- View rule details
- Create new rules
- Update existing rules
- Generate rule update scripts
- Audit rule compliance

### Rule Creation

#### Option 1: Interactive PowerShell Script

```powershell
.\create_rule.ps1 -RuleName "rule_name" -Title "Rule Title" -Description "Rule description" -Globs @("glob1", "glob2") -AlwaysApply $false
```

**Parameters:**
- `RuleName`: Name of the rule (without extension)
- `Title`: Title of the rule
- `Description`: Brief description of the rule
- `Globs`: Array of glob patterns to match files
- `AlwaysApply`: Whether the rule should always be applied (default: false)
- `ContentFile`: Path to the content file (optional)

#### Option 2: Using the Template

1. Copy the template from `templates/cursor_rule_template.md`
2. Replace the placeholders with your rule content
3. Save to `.cursor/rules/your_rule_name.mdc`

#### Option 3: Generate a Batch Script

For non-interactive environments or automation:

```powershell
.\generate_rule_script.ps1 -RuleName "rule_name" -Title "Rule Title" -Description "Rule description" -Globs @("glob1", "glob2") -AlwaysApply $false
```

This generates a batch script at `scripts/cursor_rules/update_{rule_name}_rule.bat` that can be run to create or update the rule.

### Rule Updates

To update an existing rule:

```powershell
.\update_rule.ps1 -RuleName "rule_name" -ContentFile "path/to/content.txt"
```

To update frontmatter as well:

```powershell
.\update_rule.ps1 -RuleName "rule_name" -UpdateFrontmatter $true -Title "New Title" -Description "New desc" -Globs @("new/glob/*.py")
```

### Rule Listing and Inspection

To list all rules:

```powershell
.\list_rules.ps1
```

To view details of a specific rule:

```powershell
.\list_rules.ps1 -RuleName "rule_name"
```

### Agent Compatibility Audit

To check if your rules are agent-compatible:

```powershell
# Basic audit
.\audit_rules_auto.ps1

# Generate detailed HTML report
.\audit_rules_auto.ps1 -DetailedReport

# Only generate fix scripts without verbose output
.\audit_rules_auto.ps1 -FixOnly
```

### Applying Rule Fixes

After running the audit, you can apply all the fixes at once:

```
.\fixes\apply_all_fixes.bat
```

Or apply fixes for individual rules:

```
.\fixes\fix_rule_name.bat
```

## Rule-Specific Update Scripts

For each rule, there is a corresponding update script (e.g., `update_dspy_rule.bat`) that handles:
1. Extracting the current rule content
2. Creating a new rule file with proper frontmatter 
3. Appending the extracted content

These scripts are useful for CI/CD pipelines or non-interactive environments.

## Best Practices

- Keep rule content files organized in the tmp_rules_rebuild directory
- Use consistent naming for rule content files: {rule_name}_content.txt
- Document new rules in docs/rules/README.md
- Follow these guidelines for frontmatter:
  ```yaml
  ---
  type: always
  title: Clear, descriptive title
  description: Concise description of the rule's purpose
  globs:
    - "specific/glob/patterns/*.ext"
  alwaysApply: false  # Set to true only when absolutely necessary
  ---
  ```
- Make sure rules have specific glob patterns to match only relevant files
- Default to `alwaysApply: false` to avoid overwhelming agents with rules
- Include examples, guidelines, and implementation patterns in rules

## Agent Compatibility

For optimal agent compatibility:

1. Use `alwaysApply: false` by default
2. Define specific glob patterns
3. Run `audit_rules_auto.ps1` regularly to check for issues
4. Use the fix scripts to convert rules with `alwaysApply: true` to `false` 