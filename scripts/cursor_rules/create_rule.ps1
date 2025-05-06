<#
.SYNOPSIS
    Creates a new cursor rule with proper frontmatter and content.

.DESCRIPTION
    This script creates a new cursor rule file (.mdc) in the .cursor/rules directory
    with standardized frontmatter and content from a provided content file.

.PARAMETER RuleName
    Name of the rule (without extension)

.PARAMETER Title
    Title of the rule

.PARAMETER Description
    Brief description of the rule

.PARAMETER Globs
    Array of glob patterns to match files

.PARAMETER AlwaysApply
    Whether the rule should always be applied

.PARAMETER ContentFile
    Path to the content file (defaults to tmp_rules_rebuild/{RuleName}_content.txt)

.EXAMPLE
    .\create_rule.ps1 -RuleName "documentation_usage" -Title "Documentation Standards" -Description "Guidelines for documentation" -Globs @("src/**/*.py") -AlwaysApply $true
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$RuleName,
    
    [Parameter(Mandatory=$true)]
    [string]$Title,
    
    [Parameter(Mandatory=$true)]
    [string]$Description,
    
    [Parameter(Mandatory=$true)]
    [string[]]$Globs,
    
    [Parameter(Mandatory=$false)]
    [bool]$AlwaysApply = $false,
    
    [Parameter(Mandatory=$false)]
    [string]$ContentFile = ""
)

# If content file not provided, use default location
if ([string]::IsNullOrEmpty($ContentFile)) {
    $ContentFile = "tmp_rules_rebuild/${RuleName}_content.txt"
}

# Target file
$outFile = ".cursor/rules/${RuleName}.mdc"

# Create frontmatter
$frontmatter = @"
---
type: always
title: $Title
description: $Description
globs:
"@

# Add each glob pattern
foreach ($glob in $Globs) {
    $frontmatter += @"

  - "$glob"
"@
}

# Add alwaysApply setting and close frontmatter
$frontmatter += @"

alwaysApply: $($AlwaysApply.ToString().ToLower())
---

"@

# Set the frontmatter in the file
Write-Host "Creating rule file: $outFile"
Set-Content -Path $outFile -Value $frontmatter

# If content file exists and is not empty, append it
if (![string]::IsNullOrEmpty($ContentFile) -and (Test-Path $ContentFile)) {
    Write-Host "Adding content from: $ContentFile"
    Add-Content -Path $outFile -Value (Get-Content -Path $ContentFile -Raw)
}
else {
    # Add title as fallback
    Write-Host "Content file not found or empty. Adding title only."
    Add-Content -Path $outFile -Value "# $Title`n"
}

Write-Host "Rule file created successfully: $outFile" 