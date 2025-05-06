<#
.SYNOPSIS
    Generates a batch script for creating or updating a cursor rule.

.DESCRIPTION
    This script generates a non-interactive batch script (.bat) that can create or update
    a cursor rule with proper frontmatter and content. This avoids issues with 
    interactive PowerShell scripts that require user input.

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

.PARAMETER OutputScript
    Path for the output batch script (defaults to scripts/cursor_rules/update_{RuleName}_rule.bat)

.EXAMPLE
    .\generate_rule_script.ps1 -RuleName "documentation_usage" -Title "Documentation Standards" -Description "Guidelines for documentation" -Globs @("src/**/*.py") -AlwaysApply $true
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
    [string]$ContentFile = "",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputScript = ""
)

# If content file not provided, use default location
if ([string]::IsNullOrEmpty($ContentFile)) {
    $ContentFile = "tmp_rules_rebuild\${RuleName}_content.txt"
}

# If output script not provided, use default location
if ([string]::IsNullOrEmpty($OutputScript)) {
    $OutputScript = "scripts\cursor_rules\update_${RuleName}_rule.bat"
}

# Create directory for output script if it doesn't exist
$outputDir = Split-Path -Parent $OutputScript
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Create batch script content
$batchContent = @"
@echo off
REM Update script for $RuleName cursor rule
REM Generated on $(Get-Date)

REM Create the tmp_rules_rebuild directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Make sure the content file exists
if not exist $ContentFile echo ERROR: Content file $ContentFile not found && exit /b 1

REM Create the frontmatter
echo ---                                                                > .cursor\rules\${RuleName}.mdc
echo type: always                                                      >> .cursor\rules\${RuleName}.mdc
echo title: $Title                                                     >> .cursor\rules\${RuleName}.mdc
echo description: $Description                                         >> .cursor\rules\${RuleName}.mdc
echo globs:                                                            >> .cursor\rules\${RuleName}.mdc

"@

# Add each glob pattern
foreach ($glob in $Globs) {
    $batchContent += @"
echo   - "$glob"                                                       >> .cursor\rules\${RuleName}.mdc

"@
}

# Add alwaysApply and close frontmatter
$batchContent += @"
echo alwaysApply: $($AlwaysApply.ToString().ToLower())                                                 >> .cursor\rules\${RuleName}.mdc
echo ---                                                                >> .cursor\rules\${RuleName}.mdc
echo.                                                                  >> .cursor\rules\${RuleName}.mdc

REM Append the content
type $ContentFile                                                     >> .cursor\rules\${RuleName}.mdc

echo ${RuleName} rule updated successfully.
"@

# Write batch script to file
Set-Content -Path $OutputScript -Value $batchContent

# Display warning if alwaysApply is true
if ($AlwaysApply) {
    Write-Host "WARNING: This rule is set with alwaysApply: true" -ForegroundColor Red
    Write-Host "Only use alwaysApply: true when absolutely necessary as it forces the rule to apply automatically." -ForegroundColor Yellow
    Write-Host "Consider changing to alwaysApply: false if this rule doesn't need to be automatically applied." -ForegroundColor Yellow
}

Write-Host "Batch script generated: $OutputScript" -ForegroundColor Green
Write-Host @"

To use this script:
1. Make sure your content file exists at: $ContentFile
2. Run the script: $OutputScript
"@ -ForegroundColor Yellow 