$theological_terms = @"
---
type: always
description: Guidelines for Hebrew theological term handling
globs:
  - "**/etl/**/*hebrew*.py"
  - "**/etl/fix_hebrew_strongs_ids.py"
  - "**/api/**/*theological*.py"
alwaysApply: false
---
"@

Set-Content -Path ".cursor/rules/theological_terms.mdc" -Value $theological_terms

Add-Content -Path ".cursor/rules/theological_terms.mdc" -Value (Get-Content -Path ".cursor/rules/hebrew_rules.mdc") 