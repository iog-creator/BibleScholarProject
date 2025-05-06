@echo off
REM Script to update the DSPy Generation rule with proper frontmatter and content

REM Call PowerShell to create the rule file with frontmatter and content
powershell -Command "$frontmatter = @'
---
type: always
title: DSPy Training Data Generation Guidelines
description: Guidelines for DSPy training data generation and collection
globs: 
  - \"**/dspy/**/*.py\"
  - \"**/data/processed/dspy_*.py\"
  - \"scripts/generate_dspy_training_data.py\"
  - \"scripts/refresh_dspy_data.py\"
  - \"src/utils/dspy_collector.py\"
alwaysApply: true
---

'@; $content = Get-Content -Path 'dspy_content.txt' -Raw; Set-Content -Path '.cursor/rules/dspy_generation.mdc' -Value $frontmatter; Add-Content -Path '.cursor/rules/dspy_generation.mdc' -Value $content"

echo DSPy Generation rule updated successfully. 