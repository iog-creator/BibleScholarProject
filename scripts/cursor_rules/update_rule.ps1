<#
.SYNOPSIS
    Updates an existing cursor rule with new content.

.DESCRIPTION
    This script updates an existing cursor rule file (.mdc) in the .cursor/rules directory
    with new content while preserving its frontmatter.

.PARAMETER RuleName
    Name of the rule to update (without extension)

.PARAMETER ContentFile
    Path to the new content file (defaults to tmp_rules_rebuild/{RuleName}_content.txt)

.PARAMETER UpdateFrontmatter
    Whether to update the frontmatter parameters (default: false)

.PARAMETER Title
    New title of the rule (if updating frontmatter)

.PARAMETER Description
    New description of the rule (if updating frontmatter)

.PARAMETER Globs
    New array of glob patterns (if updating frontmatter)

.PARAMETER AlwaysApply
    New alwaysApply setting (if updating frontmatter)

.EXAMPLE
    .\update_rule.ps1 -RuleName "documentation_usage"

.EXAMPLE
    .\update_rule.ps1 -RuleName "etl_rules" -UpdateFrontmatter $true -Globs @("etl/**/*.py", "scripts/*_etl.py")
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$RuleName,
    
    [Parameter(Mandatory=$false)]
    [string]$ContentFile = "",
    
    [Parameter(Mandatory=$false)]
    [bool]$UpdateFrontmatter = $false,
    
    [Parameter(Mandatory=$false)]
    [string]$Title = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Description = "",
    
    [Parameter(Mandatory=$false)]
    [string[]]$Globs = @(),
    
    [Parameter(Mandatory=$false)]
    [bool]$AlwaysApply = $false
)

# If content file not provided, use default location
if ([string]::IsNullOrEmpty($ContentFile)) {
    $ContentFile = "tmp_rules_rebuild/${RuleName}_content.txt"
}

# Target file
$ruleFile = ".cursor/rules/${RuleName}.mdc"

# Check if rule file exists
if (-not (Test-Path $ruleFile)) {
    Write-Error "Rule file not found: $ruleFile"
    exit 1
}

# If updating frontmatter, extract current frontmatter first
if ($UpdateFrontmatter) {
    $content = Get-Content -Path $ruleFile -Raw
    
    # Extract current frontmatter values if not provided
    if ([string]::IsNullOrEmpty($Title) -or [string]::IsNullOrEmpty($Description) -or $Globs.Count -eq 0) {
        $match = [regex]::Match($content, "---\s*\n(.*?)---\s*\n", [System.Text.RegularExpressions.RegexOptions]::Singleline)
        
        if ($match.Success) {
            $frontmatter = $match.Groups[1].Value
            
            # Extract title if not provided
            if ([string]::IsNullOrEmpty($Title)) {
                $titleMatch = [regex]::Match($frontmatter, "title:\s*(.*?)\s*\n")
                if ($titleMatch.Success) {
                    $Title = $titleMatch.Groups[1].Value
                }
            }
            
            # Extract description if not provided
            if ([string]::IsNullOrEmpty($Description)) {
                $descMatch = [regex]::Match($frontmatter, "description:\s*(.*?)\s*\n")
                if ($descMatch.Success) {
                    $Description = $descMatch.Groups[1].Value
                }
            }
            
            # Extract globs if not provided
            if ($Globs.Count -eq 0) {
                $globMatches = [regex]::Matches($frontmatter, "\s*-\s*\"(.*?)\"")
                $Globs = @()
                foreach ($m in $globMatches) {
                    $Globs += $m.Groups[1].Value
                }
            }
        }
    }
    
    # Create new frontmatter
    $newFrontmatter = @"
---
type: always
title: $Title
description: $Description
globs:
"@

    # Add each glob pattern
    foreach ($glob in $Globs) {
        $newFrontmatter += @"

  - "$glob"
"@
    }

    # Add alwaysApply setting and close frontmatter
    $newFrontmatter += @"

alwaysApply: $($AlwaysApply.ToString().ToLower())
---

"@
    
    # Replace frontmatter in file
    $content = [regex]::Replace($content, "---\s*\n(.*?)---\s*\n", $newFrontmatter, [System.Text.RegularExpressions.RegexOptions]::Singleline)
    Set-Content -Path $ruleFile -Value $content
    
    Write-Host "Updated frontmatter in rule file: $ruleFile"
} 
elseif (Test-Path $ContentFile) {
    # Just update the content part while preserving frontmatter
    $content = Get-Content -Path $ruleFile -Raw
    $match = [regex]::Match($content, "(---\s*\n.*?---\s*\n)(.*)", [System.Text.RegularExpressions.RegexOptions]::Singleline)
    
    if ($match.Success) {
        $frontmatter = $match.Groups[1].Value
        $newContent = Get-Content -Path $ContentFile -Raw
        
        # Combine frontmatter with new content
        Set-Content -Path $ruleFile -Value ($frontmatter + $newContent)
        
        Write-Host "Updated content in rule file: $ruleFile"
    } else {
        Write-Error "Failed to extract frontmatter from rule file: $ruleFile"
        exit 1
    }
} else {
    Write-Error "Content file not found: $ContentFile"
    exit 1
}

Write-Host "Rule file updated successfully: $ruleFile" 