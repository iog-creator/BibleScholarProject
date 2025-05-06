# PowerShell script to write the DSPy rule with proper frontmatter

# Define file paths
$ruleFile = ".cursor/rules/dspy_generation.mdc"
$contentFile = "dspy_content.txt"

# Write the frontmatter
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

# Append the content
Add-Content -Path $ruleFile -Value (Get-Content -Path $contentFile -Raw)

Write-Host "DSPy rule file updated successfully with proper frontmatter." 