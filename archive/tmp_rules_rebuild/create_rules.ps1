# Script to create Cursor rules with proper YAML frontmatter

# Function to create a rule file with proper frontmatter
function Create-RuleFile {
    param(
        [string]$outFile,
        [string]$title,
        [string]$description,
        [string[]]$globs,
        [bool]$alwaysApply,
        [string]$contentFile = ""
    )

    # Create frontmatter
    $frontmatter = @"
---
type: always
title: $title
description: $description
globs:
"@

    # Add each glob pattern
    foreach ($glob in $globs) {
        $frontmatter += @"

  - "$glob"
"@
    }

    # Add alwaysApply setting and close frontmatter
    $frontmatter += @"

alwaysApply: $($alwaysApply.ToString().ToLower())
---

"@

    # Set the frontmatter in the file
    Set-Content -Path $outFile -Value $frontmatter

    # If content file exists and is not empty, append it
    if (![string]::IsNullOrEmpty($contentFile) -and (Test-Path $contentFile)) {
        Add-Content -Path $outFile -Value (Get-Content -Path $contentFile -Raw)
    }
    else {
        # Add title as fallback
        Add-Content -Path $outFile -Value "# $title`n"
    }
}

# 1. Documentation Usage Rule
Create-RuleFile `
    -outFile ".cursor/rules/documentation_usage.mdc" `
    -title "Documentation Usage Guidelines" `
    -description "Guidelines for utilizing and updating documentation in the BibleScholarProject" `
    -globs @("src/**/*.py", "scripts/*.py", "tests/**/*.py") `
    -alwaysApply $true `
    -contentFile "tmp_rules_rebuild/documentation_usage_content.txt"

# 2. Theological Terms Rule  
Create-RuleFile `
    -outFile ".cursor/rules/theological_terms.mdc" `
    -title "Theological Terms Guidelines" `
    -description "Guidelines for Hebrew theological term handling" `
    -globs @("**/etl/**/*hebrew*.py", "**/etl/fix_hebrew_strongs_ids.py", "**/api/**/*theological*.py") `
    -alwaysApply $false

# 3. DB Test Skip Rule
Create-RuleFile `
    -outFile ".cursor/rules/db_test_skip.mdc" `
    -title "Database Test Skip Guidelines" `
    -description "Guidelines for skipping database tests" `
    -globs @("**/tests/**/*db*.py", "**/tests/**/*database*.py") `
    -alwaysApply $false

# 4. DSPy Generation Rule
Create-RuleFile `
    -outFile ".cursor/rules/dspy_generation.mdc" `
    -title "DSPy Training Data Generation Guidelines" `
    -description "Guidelines for DSPy training data generation" `
    -globs @("**/dspy/**/*.py", "**/data/processed/dspy_*.py") `
    -alwaysApply $false

# 5. Pandas Rules
Create-RuleFile `
    -outFile ".cursor/rules/pandas_dataframe_type_enforcement.mdc" `
    -title "Pandas DataFrame Type Enforcement" `
    -description "Guidelines for enforcing data types in pandas DataFrames" `
    -globs @("**/etl/**/*.py", "**/scripts/**/*pandas*.py") `
    -alwaysApply $false

Create-RuleFile `
    -outFile ".cursor/rules/pandas_null_handling.mdc" `
    -title "Pandas Null Handling Guidelines" `
    -description "Guidelines for handling null values in pandas DataFrames" `
    -globs @("**/etl/**/*.py", "**/scripts/**/*pandas*.py") `
    -alwaysApply $false

# 6. ETL Rules
Create-RuleFile `
    -outFile ".cursor/rules/etl_rules.mdc" `
    -title "ETL Process Guidelines" `
    -description "Standards for ETL processes and data pipeline processing" `
    -globs @("**/etl/**/*.py", "**/scripts/**/*.py") `
    -alwaysApply $false

# 7. TVTMS Rules
Create-RuleFile `
    -outFile ".cursor/rules/tvtms_expected_count.mdc" `
    -title "TVTMS Expected Count Guidelines" `
    -description "Expected count validations for TVTMS processing" `
    -globs @("**/tvtms/**/*.py", "**/scripts/*tvtms*.py") `
    -alwaysApply $false

Create-RuleFile `
    -outFile ".cursor/rules/tvtms_txt_only.mdc" `
    -title "TVTMS Text File Format Guidelines" `
    -description "TVTMS file format handling guidelines" `
    -globs @("**/tvtms/**/*.py", "**/scripts/*tvtms*.py") `
    -alwaysApply $false

# 8. Model Validation Rule
Create-RuleFile `
    -outFile ".cursor/rules/model_validation.mdc" `
    -title "Model Validation Guidelines" `
    -description "Guidelines for ML model validation and evaluation" `
    -globs @("**/model/**/*.py", "**/dspy/**/*.py") `
    -alwaysApply $false

Write-Host "Cursor rule files created successfully." 