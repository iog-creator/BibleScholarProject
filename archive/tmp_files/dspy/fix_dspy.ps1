# PowerShell script to fix the DSPy rule file

# Path to the rule file
$ruleFile = ".cursor/rules/dspy_generation.mdc"
$contentFile = "dspy_content.txt"

# Write the frontmatter directly
@"
---
type: always
title: DSPy Training Data Generation Guidelines
description: Guidelines for DSPy training data generation and collection
globs:
  - "**/dspy/**/*.py"
  - "**/data/processed/dspy_*.py"
  - "scripts/generate_dspy_training_data.py"
  - "scripts/refresh_dspy_data.py"
  - "src/utils/dspy_collector.py"
alwaysApply: true
---

"@ | Set-Content -Path $ruleFile

# Append content from dspy_content.txt
Get-Content -Path $contentFile | Add-Content -Path $ruleFile

Write-Host "DSPy rule file updated successfully." 