# Function to create a rule file with proper frontmatter
function Update-RuleFile {
    param(
        [string]$outFile,
        [string]$title,
        [string]$description,
        [string[]]$globs,
        [bool]$alwaysApply,
        [string]$contentFile
    )

    Write-Host "Creating rule file: $outFile"
    Write-Host "With content from: $contentFile"

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
    Write-Host "Writing frontmatter to file"
    Write-Host $frontmatter
    Set-Content -Path $outFile -Value $frontmatter

    # If content file exists and is not empty, append it
    if (![string]::IsNullOrEmpty($contentFile) -and (Test-Path $contentFile)) {
        Write-Host "Appending content from $contentFile"
        Add-Content -Path $outFile -Value (Get-Content -Path $contentFile -Raw)
    }
    else {
        # Add title as fallback
        Write-Host "Content file not found, adding title only"
        Add-Content -Path $outFile -Value "# $title`n"
    }
}

# Update DSPy Generation Rule
Write-Host "Starting rule update process"
Update-RuleFile `
    -outFile ".cursor/rules/dspy_generation.mdc" `
    -title "DSPy Training Data Generation Guidelines" `
    -description "Guidelines for DSPy training data generation and collection" `
    -globs @(
        "**/dspy/**/*.py", 
        "**/data/processed/dspy_*.py", 
        "scripts/generate_dspy_training_data.py", 
        "scripts/refresh_dspy_data.py", 
        "src/utils/dspy_collector.py"
    ) `
    -alwaysApply $true `
    -contentFile "tmp_rules_rebuild/dspy_generation_content.txt"

Write-Host "Verifying file content:"
Get-Content ".cursor/rules/dspy_generation.mdc" -TotalCount 10

Write-Host "DSPy Generation rule file updated successfully." 