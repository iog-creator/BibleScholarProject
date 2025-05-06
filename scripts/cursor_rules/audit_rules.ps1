<#
.SYNOPSIS
    Audits existing cursor rules for agent-friendliness.

.DESCRIPTION
    This script audits existing cursor rules to identify those using alwaysApply: true
    and helps you decide which ones should be changed to alwaysApply: false.

.EXAMPLE
    .\audit_rules.ps1
#>

# Rules directory
$rulesDir = ".cursor/rules"

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

# Check if rules directory exists
if (-not (Test-Path $rulesDir)) {
    Write-Error "Rules directory not found: $rulesDir"
    exit 1
}

# Find all rules
$ruleFiles = Get-ChildItem -Path $rulesDir -Filter "*.mdc"
$alwaysApplyRules = @()
$normalRules = @()

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
        Globs = $globs -join ", "
        AlwaysApply = $alwaysApply
    }
    
    if ($alwaysApply -eq "true") {
        $alwaysApplyRules += $rule
    }
    else {
        $normalRules += $rule
    }
}

# Display audit results
Write-Host "=== Rule Audit Results ===" -ForegroundColor Cyan
Write-Host "Total Rules: $($ruleFiles.Count)" -ForegroundColor Green
Write-Host "Rules with alwaysApply: false: $($normalRules.Count)" -ForegroundColor Green
Write-Host "Rules with alwaysApply: true: $($alwaysApplyRules.Count)" -ForegroundColor Yellow

if ($alwaysApplyRules.Count -gt 0) {
    Write-Host "`nRules that may need to be changed to alwaysApply: false:" -ForegroundColor Yellow
    $alwaysApplyRules | Format-Table -Property Name, Title, GlobCount, Globs
    
    Write-Host @"
Consider changing these rules to alwaysApply: false to make them more agent-friendly.
To change a rule, use:

.\scripts\cursor_rules\generate_rule_script.ps1 -RuleName "rule_name" -Title "Rule Title" -Description "Description" -Globs @("glob1", "glob2") -AlwaysApply `$false

Or manually edit the rule file and change alwaysApply to false.
"@ -ForegroundColor Yellow
}
else {
    Write-Host "`nAll rules are already using alwaysApply: false. Great job!" -ForegroundColor Green
}

# Offer to generate fix scripts
if ($alwaysApplyRules.Count -gt 0) {
    $generateFixes = Read-Host "`nWould you like to generate fix scripts for these rules? (y/n)"
    
    if ($generateFixes.ToLower() -eq "y") {
        $fixDir = "scripts\cursor_rules\fixes"
        if (-not (Test-Path $fixDir)) {
            New-Item -ItemType Directory -Path $fixDir -Force | Out-Null
        }
        
        foreach ($rule in $alwaysApplyRules) {
            $ruleName = $rule.Name
            $ruleFile = Join-Path $rulesDir "${ruleName}.mdc"
            $frontmatter = Get-RuleFrontmatter -FilePath $ruleFile
            
            $title = Get-FrontmatterValue -Frontmatter $frontmatter -Key "title"
            $description = Get-FrontmatterValue -Frontmatter $frontmatter -Key "description"
            $globs = Get-GlobPatterns -Frontmatter $frontmatter
            
            # Generate fix script
            $fixScript = Join-Path $fixDir "fix_${ruleName}.bat"
            
            $batchContent = @"
@echo off
REM Fix script for $ruleName cursor rule - changing alwaysApply to false
REM Generated on $(Get-Date)

REM Extract current content (without frontmatter)
powershell -Command "& {`$content = Get-Content -Raw '.cursor\\rules\\${ruleName}.mdc'; `$match = [regex]::Match(`$content, '---\s*\n.*?---\s*\n(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline); if (`$match.Success) { `$match.Groups[1].Value | Set-Content 'tmp_rules_rebuild\\${ruleName}_content.txt' } else { 'Failed to extract content' | Write-Error }}"

REM Create the frontmatter
echo ---                                                                > .cursor\rules\${ruleName}.mdc
echo type: always                                                      >> .cursor\rules\${ruleName}.mdc
echo title: $title                                                     >> .cursor\rules\${ruleName}.mdc
echo description: $description                                         >> .cursor\rules\${ruleName}.mdc
echo globs:                                                            >> .cursor\rules\${ruleName}.mdc

"@

            # Add each glob pattern
            foreach ($glob in $globs) {
                $batchContent += @"
echo   - "$glob"                                                       >> .cursor\rules\${ruleName}.mdc

"@
            }

            # Add alwaysApply (now false) and close frontmatter
            $batchContent += @"
echo alwaysApply: false                                                >> .cursor\rules\${ruleName}.mdc
echo ---                                                                >> .cursor\rules\${ruleName}.mdc
echo.                                                                  >> .cursor\rules\${ruleName}.mdc

REM Append the content
type tmp_rules_rebuild\\${ruleName}_content.txt                        >> .cursor\rules\${ruleName}.mdc

echo ${ruleName} rule updated to be agent-friendly with alwaysApply: false
"@

            # Write batch script to file
            Set-Content -Path $fixScript -Value $batchContent
            Write-Host "Fix script generated: $fixScript" -ForegroundColor Green
        }
        
        Write-Host @"
Fix scripts have been generated in $fixDir.
To apply all fixes, run:
Get-ChildItem $fixDir -Filter "fix_*.bat" | ForEach-Object { & `$_.FullName }
"@ -ForegroundColor Green
    }
} 