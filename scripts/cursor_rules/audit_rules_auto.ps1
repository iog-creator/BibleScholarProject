<#
.SYNOPSIS
    Non-interactive audit and fix for cursor rules.

.DESCRIPTION
    This script audits existing cursor rules and automatically generates fix scripts 
    for rules using alwaysApply: true without requiring user interaction.
    
    It provides detailed reporting on rule compliance and generates scripts to fix issues.

.PARAMETER DetailedReport
    Generate a detailed HTML report in addition to console output.
    
.PARAMETER FixOnly
    Generate fix scripts without detailed reporting.

.EXAMPLE
    # Basic audit with console output
    .\audit_rules_auto.ps1
    
.EXAMPLE
    # Generate detailed HTML report
    .\audit_rules_auto.ps1 -DetailedReport
    
.EXAMPLE
    # Only generate fix scripts without verbose output
    .\audit_rules_auto.ps1 -FixOnly
#>

param(
    [Parameter(Mandatory=$false)]
    [switch]$DetailedReport,
    
    [Parameter(Mandatory=$false)]
    [switch]$FixOnly
)

# Rules directory
$rulesDir = ".cursor/rules"
$fixDir = "scripts\cursor_rules\fixes"
$reportDir = "review"

# Create directories if they don't exist
if (-not (Test-Path $fixDir)) {
    New-Item -ItemType Directory -Path $fixDir -Force | Out-Null
}

if ($DetailedReport -and -not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
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

# Function to calculate rule quality score (0-100)
function Get-RuleQualityScore {
    param (
        [PSCustomObject]$Rule
    )
    
    $score = 0
    
    # Start with base score
    $score += 50
    
    # Add points for good practices
    if ($Rule.AlwaysApply -eq "false") { $score += 30 }
    if ($Rule.GlobCount -gt 0) { $score += 10 }
    if ($Rule.GlobCount -gt 1) { $score += 5 }
    if ($Rule.Title.Length -gt 10) { $score += 5 }
    if ($Rule.Description.Length -gt 20) { $score += 5 }
    
    # Remove points for bad practices
    if ($Rule.AlwaysApply -eq "true") { $score -= 30 }
    if ($Rule.GlobCount -eq 0) { $score -= 20 }
    if ($Rule.Title.Length -lt 5) { $score -= 10 }
    if ($Rule.Description.Length -lt 10) { $score -= 10 }
    
    # Ensure score is within 0-100 range
    if ($score -lt 0) { $score = 0 }
    if ($score -gt 100) { $score = 100 }
    
    return $score
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
$allRules = @()

foreach ($file in $ruleFiles) {
    $ruleName = $file.BaseName
    $frontmatter = Get-RuleFrontmatter -FilePath $file.FullName
    
    $title = Get-FrontmatterValue -Frontmatter $frontmatter -Key "title"
    $description = Get-FrontmatterValue -Frontmatter $frontmatter -Key "description"
    $alwaysApply = Get-FrontmatterValue -Frontmatter $frontmatter -Key "alwaysApply"
    $type = Get-FrontmatterValue -Frontmatter $frontmatter -Key "type"
    $globs = Get-GlobPatterns -Frontmatter $frontmatter
    
    $rule = [PSCustomObject]@{
        Name = $ruleName
        Title = $title
        Description = $description
        Type = $type
        GlobCount = $globs.Count
        Globs = $globs -join ", "
        AlwaysApply = $alwaysApply
        FilePath = $file.FullName
    }
    
    # Calculate quality score
    $rule | Add-Member -MemberType NoteProperty -Name "QualityScore" -Value (Get-RuleQualityScore -Rule $rule)
    
    if ($alwaysApply -eq "true") {
        $alwaysApplyRules += $rule
    }
    else {
        $normalRules += $rule
    }
    
    $allRules += $rule
}

# Skip detailed output if FixOnly is specified
if (-not $FixOnly) {
    # Display audit results
    Write-Host "=== Bible Scholar Cursor Rule Audit Results ===" -ForegroundColor Cyan
    Write-Host "Total Rules: $($ruleFiles.Count)" -ForegroundColor Green
    Write-Host "Rules with alwaysApply: false: $($normalRules.Count)" -ForegroundColor Green
    Write-Host "Rules with alwaysApply: true: $($alwaysApplyRules.Count)" -ForegroundColor Yellow
    
    # Calculate average quality score
    $avgScore = ($allRules | Measure-Object -Property QualityScore -Average).Average
    Write-Host "Average Rule Quality Score: $([math]::Round($avgScore, 1)) / 100" -ForegroundColor Cyan
    
    # List problems if any
    if ($alwaysApplyRules.Count -gt 0) {
        Write-Host "`nRules that need to be changed to alwaysApply: false:" -ForegroundColor Yellow
        $alwaysApplyRules | Format-Table -Property Name, Title, GlobCount, QualityScore
    }
}

# Generate fix scripts for all rules with alwaysApply: true
if ($alwaysApplyRules.Count -gt 0) {
    if (-not $FixOnly) {
        Write-Host "`nGenerating fix scripts..." -ForegroundColor Cyan
    }
    
    foreach ($rule in $alwaysApplyRules) {
        $ruleName = $rule.Name
        $ruleFile = $rule.FilePath
        $frontmatter = Get-RuleFrontmatter -FilePath $ruleFile
        
        $title = Get-FrontmatterValue -Frontmatter $frontmatter -Key "title"
        $description = Get-FrontmatterValue -Frontmatter $frontmatter -Key "description"
        $type = Get-FrontmatterValue -Frontmatter $frontmatter -Key "type"
        $globs = Get-GlobPatterns -Frontmatter $frontmatter
        
        # Generate fix script
        $fixScript = Join-Path $fixDir "fix_${ruleName}.bat"
        
        $batchContent = @"
@echo off
REM Fix script for $ruleName cursor rule - changing alwaysApply to false
REM Generated on $(Get-Date)

REM Create tmp directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Extract current content (without frontmatter)
powershell -Command "& {`$content = Get-Content -Raw '.cursor\\rules\\${ruleName}.mdc'; `$match = [regex]::Match(`$content, '---\s*\n.*?---\s*\n(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline); if (`$match.Success) { `$match.Groups[1].Value | Set-Content 'tmp_rules_rebuild\\${ruleName}_content.txt' } else { 'Failed to extract content' | Write-Error }}"

REM Create the frontmatter
echo ---                                                                > .cursor\rules\${ruleName}.mdc
echo type: $type                                                      >> .cursor\rules\${ruleName}.mdc
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
        
        if (-not $FixOnly) {
            Write-Host "Fix script generated: $fixScript" -ForegroundColor Green
        }
    }
    
    # Create an "apply all" batch script
    $applyAllScript = Join-Path $fixDir "apply_all_fixes.bat"
    
    $applyAllContent = @"
@echo off
echo Applying all rule fixes...
"@

    foreach ($rule in $alwaysApplyRules) {
        $ruleName = $rule.Name
        $applyAllContent += @"

echo Fixing $ruleName...
call fix_${ruleName}.bat
"@
    }

    $applyAllContent += @"

echo All fixes applied successfully!
"@

    Set-Content -Path $applyAllScript -Value $applyAllContent
    
    if (-not $FixOnly) {
        Write-Host @"
`nAll fix scripts have been generated in $fixDir.
To apply all fixes at once, run:
.\scripts\cursor_rules\fixes\apply_all_fixes.bat
"@ -ForegroundColor Green
    }
}
else {
    if (-not $FixOnly) {
        Write-Host "`nAll rules are already using alwaysApply: false. Great job!" -ForegroundColor Green
    }
}

# Generate HTML report if detailed report is requested
if ($DetailedReport) {
    $reportFile = Join-Path $reportDir "cursor_rule_audit_report.html"
    
    $htmlHeader = @"
<!DOCTYPE html>
<html>
<head>
    <title>Bible Scholar Cursor Rule Audit Report</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; }
        h1, h2, h3 { color: #2c3e50; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .good { background-color: #d4edda; }
        .warning { background-color: #fff3cd; }
        .bad { background-color: #f8d7da; }
        .score { font-weight: bold; text-align: center; }
        .progress-bar-container { width: 100%; background-color: #e0e0e0; height: 20px; border-radius: 4px; overflow: hidden; }
        .progress-bar { height: 100%; transition: width 0.5s ease-in-out; }
        .summary { display: flex; justify-content: space-between; margin-bottom: 20px; }
        .summary-box { background-color: #f8f9fa; padding: 15px; border-radius: 5px; flex: 1; margin: 0 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .summary-box h3 { margin-top: 0; }
        .recommendations { background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>Bible Scholar Cursor Rule Audit Report</h1>
    <p>Generated on $(Get-Date)</p>
    
    <div class="summary">
        <div class="summary-box">
            <h3>Total Rules</h3>
            <p style="font-size: 24px;">$($ruleFiles.Count)</p>
        </div>
        <div class="summary-box">
            <h3>Agent-Compatible Rules</h3>
            <p style="font-size: 24px;">$($normalRules.Count)</p>
        </div>
        <div class="summary-box">
            <h3>Rules Needing Fixes</h3>
            <p style="font-size: 24px;">$($alwaysApplyRules.Count)</p>
        </div>
        <div class="summary-box">
            <h3>Average Quality Score</h3>
            <p style="font-size: 24px;">$([math]::Round($avgScore, 1))</p>
        </div>
    </div>
    
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
"@

    $recommendations = @()
    
    if ($alwaysApplyRules.Count -gt 0) {
        $recommendations += "<li>Change <strong>$($alwaysApplyRules.Count) rules</strong> from <code>alwaysApply: true</code> to <code>alwaysApply: false</code> to improve agent compatibility.</li>"
        $recommendations += "<li>Run <code>.\scripts\cursor_rules\fixes\apply_all_fixes.bat</code> to automatically fix these issues.</li>"
    }
    
    $lowQualityRules = $allRules | Where-Object { $_.QualityScore -lt 70 }
    if ($lowQualityRules.Count -gt 0) {
        $recommendations += "<li>Improve the quality of <strong>$($lowQualityRules.Count) rules</strong> with low quality scores (below 70).</li>"
    }
    
    $noGlobRules = $allRules | Where-Object { $_.GlobCount -eq 0 }
    if ($noGlobRules.Count -gt 0) {
        $recommendations += "<li>Add specific glob patterns to <strong>$($noGlobRules.Count) rules</strong> that don't have any globs defined.</li>"
    }
    
    if ($recommendations.Count -eq 0) {
        $recommendations += "<li>All rules are following best practices. Great job!</li>"
    }
    
    $htmlRecommendations = $recommendations -join "`n        "
    
    $htmlContent = $htmlHeader + @"
        $htmlRecommendations
        </ul>
    </div>
    
    <h2>Rule Details</h2>
    <table>
        <tr>
            <th>Rule Name</th>
            <th>Title</th>
            <th>Description</th>
            <th>Glob Count</th>
            <th>alwaysApply</th>
            <th>Quality Score</th>
        </tr>
"@

    foreach ($rule in $allRules | Sort-Object -Property QualityScore -Descending) {
        $rowClass = ""
        if ($rule.QualityScore -ge 80) {
            $rowClass = "good"
        } elseif ($rule.QualityScore -ge 60) {
            $rowClass = ""
        } elseif ($rule.QualityScore -ge 40) {
            $rowClass = "warning"
        } else {
            $rowClass = "bad"
        }
        
        $scoreBarColor = "#4caf50"  # Green
        if ($rule.QualityScore -lt 70) { $scoreBarColor = "#ff9800" }  # Orange
        if ($rule.QualityScore -lt 50) { $scoreBarColor = "#f44336" }  # Red
        
        $htmlContent += @"
        <tr class="$rowClass">
            <td>$($rule.Name)</td>
            <td>$($rule.Title)</td>
            <td>$($rule.Description)</td>
            <td style="text-align: center;">$($rule.GlobCount)</td>
            <td style="text-align: center;">$($rule.AlwaysApply)</td>
            <td class="score">
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: $($rule.QualityScore)%; background-color: $scoreBarColor;"></div>
                </div>
                $($rule.QualityScore)
            </td>
        </tr>
"@
    }

    $htmlContent += @"
    </table>
    
    <h2>Rules Needing Fixes</h2>
"@

    if ($alwaysApplyRules.Count -gt 0) {
        $htmlContent += @"
    <table>
        <tr>
            <th>Rule Name</th>
            <th>Title</th>
            <th>Description</th>
            <th>Glob Count</th>
            <th>Fix Script</th>
        </tr>
"@

        foreach ($rule in $alwaysApplyRules) {
            $htmlContent += @"
        <tr>
            <td>$($rule.Name)</td>
            <td>$($rule.Title)</td>
            <td>$($rule.Description)</td>
            <td style="text-align: center;">$($rule.GlobCount)</td>
            <td><code>.\scripts\cursor_rules\fixes\fix_$($rule.Name).bat</code></td>
        </tr>
"@
        }

        $htmlContent += @"
    </table>
"@
    } else {
        $htmlContent += @"
    <p>No rules need to be fixed. All rules are already using <code>alwaysApply: false</code>.</p>
"@
    }

    $htmlContent += @"
</body>
</html>
"@

    Set-Content -Path $reportFile -Value $htmlContent
    
    Write-Host "`nDetailed HTML report generated: $reportFile" -ForegroundColor Green
} 