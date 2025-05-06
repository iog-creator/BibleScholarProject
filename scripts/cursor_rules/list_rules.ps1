<#
.SYNOPSIS
    Lists all cursor rules with their details.

.DESCRIPTION
    This script lists all cursor rules (.mdc files) in the .cursor/rules directory
    with their name, title, description, glob patterns, and alwaysApply setting.

.PARAMETER RuleName
    Optional name of a specific rule to show detailed information for

.EXAMPLE
    .\list_rules.ps1

.EXAMPLE
    .\list_rules.ps1 -RuleName "documentation_usage"
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$RuleName = ""
)

# Rules directory
$rulesDir = ".cursor/rules"

# Check if rules directory exists
if (-not (Test-Path $rulesDir)) {
    Write-Error "Rules directory not found: $rulesDir"
    exit 1
}

# Function to extract frontmatter from a rule file
function Get-RuleFrontmatter {
    param (
        [string]$FilePath
    )
    
    $content = Get-Content -Path $FilePath -Raw
    $match = [regex]::Match($content, "---\s*\n(.*?)---\s*\n", [System.Text.RegularExpressions.RegexOptions]::Singleline)
    
    if ($match.Success) {
        return $match.Groups[1].Value
    }
    
    return ""
}

# Function to extract a specific value from frontmatter
function Get-FrontmatterValue {
    param (
        [string]$Frontmatter,
        [string]$Key
    )
    
    $keyPattern = [regex]::Escape($Key)
    $match = [regex]::Match($Frontmatter, "$keyPattern`:\s*(.*?)\s*\n")
    if ($match.Success) {
        return $match.Groups[1].Value
    }
    
    return ""
}

# Function to extract glob patterns from frontmatter
function Get-GlobPatterns {
    param (
        [string]$Frontmatter
    )
    
    $globMatches = [regex]::Matches($Frontmatter, '\s*-\s*"(.*?)"')
    $globs = @()
    foreach ($m in $globMatches) {
        $globs += $m.Groups[1].Value
    }
    
    return $globs
}

# If a specific rule is requested, show detailed information
if (-not [string]::IsNullOrEmpty($RuleName)) {
    $ruleFile = Join-Path $rulesDir "${RuleName}.mdc"
    
    if (-not (Test-Path $ruleFile)) {
        Write-Error "Rule file not found: $ruleFile"
        exit 1
    }
    
    $frontmatter = Get-RuleFrontmatter -FilePath $ruleFile
    $title = Get-FrontmatterValue -Frontmatter $frontmatter -Key "title"
    $description = Get-FrontmatterValue -Frontmatter $frontmatter -Key "description"
    $alwaysApply = Get-FrontmatterValue -Frontmatter $frontmatter -Key "alwaysApply"
    $globs = Get-GlobPatterns -Frontmatter $frontmatter
    
    Write-Host "Rule: $RuleName" -ForegroundColor Cyan
    Write-Host "Title: $title"
    Write-Host "Description: $description"
    Write-Host "Always Apply: $alwaysApply"
    Write-Host "Glob Patterns:" -ForegroundColor Cyan
    foreach ($glob in $globs) {
        Write-Host "  - $glob"
    }
    
    exit 0
}

# List all rules
$rules = @()
$ruleFiles = Get-ChildItem -Path $rulesDir -Filter "*.mdc"

foreach ($file in $ruleFiles) {
    $ruleName = $file.BaseName
    $frontmatter = Get-RuleFrontmatter -FilePath $file.FullName
    
    $title = Get-FrontmatterValue -Frontmatter $frontmatter -Key "title"
    $description = Get-FrontmatterValue -Frontmatter $frontmatter -Key "description"
    $alwaysApply = Get-FrontmatterValue -Frontmatter $frontmatter -Key "alwaysApply"
    $globs = Get-GlobPatterns -Frontmatter $frontmatter
    
    $rule = [PSCustomObject]@{
        Name = $ruleName
        Title = $title
        Description = $description
        GlobCount = $globs.Count
        AlwaysApply = $alwaysApply
    }
    
    $rules += $rule
}

# Display rules in a table
Write-Host "Cursor Rules:" -ForegroundColor Cyan
$rules | Format-Table -Property Name, Title, GlobCount, AlwaysApply

Write-Host "Total Rules: $($rules.Count)" -ForegroundColor Green
Write-Host "For detailed information about a specific rule, run: .\list_rules.ps1 -RuleName '<rule_name>'" 