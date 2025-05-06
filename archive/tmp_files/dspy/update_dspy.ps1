# PowerShell script to fix the DSPy rule

# Add frontmatter
@"
  - "**/dspy/**/*.py"
  - "**/data/processed/dspy_*.py"
  - "scripts/generate_dspy_training_data.py"
  - "scripts/refresh_dspy_data.py"
  - "src/utils/dspy_collector.py"
alwaysApply: true
---

"@ | Set-Content -Path ".cursor/rules/dspy_generation.mdc"

# Add content
Get-Content -Path "dspy_content.txt" | Add-Content -Path ".cursor/rules/dspy_generation.mdc"

Write-Host "DSPy rule file updated successfully." 