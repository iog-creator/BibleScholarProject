<#
.SYNOPSIS
    All-in-one script for managing cursor rules.

.DESCRIPTION
    This script provides a unified interface for creating, updating, listing,
    and managing cursor rules in the BibleScholar project.

.EXAMPLE
    .\manage_rules.ps1
#>

# Rules directory
$rulesDir = ".cursor/rules"
$tmpDir = "tmp_rules_rebuild"
$rulesDocDir = "docs/rules"

# Create directories if they don't exist
if (-not (Test-Path $rulesDir)) {
    New-Item -ItemType Directory -Path $rulesDir -Force | Out-Null
}

if (-not (Test-Path $tmpDir)) {
    New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
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

# Function to extract content (without frontmatter) from a rule file
function Get-RuleContent {
    param (
        [string]$FilePath
    )
    
    $content = Get-Content -Path $FilePath -Raw
    $match = [regex]::Match($content, "---\s*\n.*?---\s*\n(.*)", [System.Text.RegularExpressions.RegexOptions]::Singleline)
    
    if ($match.Success) {
        return $match.Groups[1].Value
    }
    
    return $content
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

# Function to list all rules
function List-Rules {
    param (
        [string]$RuleName = ""
    )
    
    # If a specific rule is requested, show detailed information
    if (-not [string]::IsNullOrEmpty($RuleName)) {
        $ruleFile = Join-Path $rulesDir "${RuleName}.mdc"
        
        if (-not (Test-Path $ruleFile)) {
            Write-Error "Rule file not found: $ruleFile"
            return
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
        
        return
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
    Write-Host "For detailed information about a specific rule, run: .\manage_rules.ps1 and select option 1"
}

# Function to create a new rule
function Create-Rule {
    Write-Host "Create a new cursor rule" -ForegroundColor Cyan
    
    $ruleName = Read-Host "Rule name (without extension)"
    $title = Read-Host "Rule title"
    $description = Read-Host "Rule description"
    
    $globsInput = Read-Host "Glob patterns (comma-separated, e.g. 'src/**/*.py,tests/**/*.py')"
    $globs = $globsInput -split ',' | ForEach-Object { $_.Trim() }
    
    $alwaysApplyInput = Read-Host "Always apply? (y/n)"
    $alwaysApply = $alwaysApplyInput.ToLower() -eq 'y'
    
    # Content options
    Write-Host "Choose content option:" -ForegroundColor Yellow
    Write-Host "1. Enter content now"
    Write-Host "2. Use content from file"
    Write-Host "3. Empty (just title)"
    $contentOption = Read-Host "Option (1-3)"
    
    $content = ""
    switch ($contentOption) {
        "1" {
            Write-Host "Enter content (press Enter then Ctrl+Z and Enter to finish):" -ForegroundColor Yellow
            $content = @()
            while ($line = Read-Host) {
                $content += $line
            }
            $content = $content -join "`n"
        }
        "2" {
            $contentFile = Read-Host "Path to content file"
            if (Test-Path $contentFile) {
                $content = Get-Content -Path $contentFile -Raw
            } else {
                Write-Error "Content file not found: $contentFile"
                return
            }
        }
        "3" {
            $content = "# $title`n"
        }
        default {
            Write-Error "Invalid option: $contentOption"
            return
        }
    }
    
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

    # Target file
    $outFile = Join-Path $rulesDir "${ruleName}.mdc"
    
    # Write the file
    Set-Content -Path $outFile -Value ($frontmatter + $content)
    
    Write-Host "Rule created successfully: $outFile" -ForegroundColor Green

    # Save content to tmp directory for backup
    $contentFile = Join-Path $tmpDir "${ruleName}_content.txt"
    Set-Content -Path $contentFile -Value $content
    Write-Host "Content saved to: $contentFile" -ForegroundColor Green
}

# Function to update an existing rule
function Update-Rule {
    Write-Host "Update an existing cursor rule" -ForegroundColor Cyan
    
    # List available rules
    $ruleFiles = Get-ChildItem -Path $rulesDir -Filter "*.mdc" | Select-Object -ExpandProperty BaseName
    
    if ($ruleFiles.Count -eq 0) {
        Write-Error "No rules found in $rulesDir"
        return
    }
    
    Write-Host "Available rules:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $ruleFiles.Count; $i++) {
        Write-Host "$($i+1). $($ruleFiles[$i])"
    }
    
    $ruleIndex = [int](Read-Host "Select rule (1-$($ruleFiles.Count))") - 1
    
    if ($ruleIndex -lt 0 -or $ruleIndex -ge $ruleFiles.Count) {
        Write-Error "Invalid selection: $($ruleIndex+1)"
        return
    }
    
    $ruleName = $ruleFiles[$ruleIndex]
    $ruleFile = Join-Path $rulesDir "${ruleName}.mdc"
    
    Write-Host "Selected rule: $ruleName" -ForegroundColor Cyan
    
    # Update options
    Write-Host "What would you like to update?" -ForegroundColor Yellow
    Write-Host "1. Content only"
    Write-Host "2. Frontmatter only"
    Write-Host "3. Both content and frontmatter"
    $updateOption = Read-Host "Option (1-3)"
    
    # Extract current frontmatter and content
    $frontmatter = Get-RuleFrontmatter -FilePath $ruleFile
    $content = Get-RuleContent -FilePath $ruleFile
    
    $title = Get-FrontmatterValue -Frontmatter $frontmatter -Key "title"
    $description = Get-FrontmatterValue -Frontmatter $frontmatter -Key "description"
    $alwaysApply = Get-FrontmatterValue -Frontmatter $frontmatter -Key "alwaysApply"
    $globs = Get-GlobPatterns -Frontmatter $frontmatter
    
    # Update frontmatter if requested
    if ($updateOption -eq "2" -or $updateOption -eq "3") {
        Write-Host "Current title: $title"
        $newTitle = Read-Host "New title (press Enter to keep current)"
        if (-not [string]::IsNullOrEmpty($newTitle)) {
            $title = $newTitle
        }
        
        Write-Host "Current description: $description"
        $newDescription = Read-Host "New description (press Enter to keep current)"
        if (-not [string]::IsNullOrEmpty($newDescription)) {
            $description = $newDescription
        }
        
        Write-Host "Current glob patterns:"
        for ($i = 0; $i -lt $globs.Count; $i++) {
            Write-Host "$($i+1). $($globs[$i])"
        }
        $updateGlobs = Read-Host "Update glob patterns? (y/n)"
        
        if ($updateGlobs.ToLower() -eq "y") {
            $globsInput = Read-Host "New glob patterns (comma-separated, e.g. 'src/**/*.py,tests/**/*.py')"
            $globs = $globsInput -split ',' | ForEach-Object { $_.Trim() }
        }
        
        Write-Host "Current always apply: $alwaysApply"
        $alwaysApplyInput = Read-Host "Always apply? (y/n, press Enter to keep current)"
        if (-not [string]::IsNullOrEmpty($alwaysApplyInput)) {
            $alwaysApply = $alwaysApplyInput.ToLower() -eq "y"
        }
    }
    
    # Update content if requested
    if ($updateOption -eq "1" -or $updateOption -eq "3") {
        # Save current content to tmp file
        $tmpContentFile = Join-Path $tmpDir "${ruleName}_content_backup.txt"
        Set-Content -Path $tmpContentFile -Value $content
        Write-Host "Current content saved to: $tmpContentFile" -ForegroundColor Green
        
        # Content options
        Write-Host "Choose content option:" -ForegroundColor Yellow
        Write-Host "1. Enter content now"
        Write-Host "2. Use content from file"
        Write-Host "3. Keep current content"
        $contentOption = Read-Host "Option (1-3)"
        
        switch ($contentOption) {
            "1" {
                Write-Host "Enter content (press Enter then Ctrl+Z and Enter to finish):" -ForegroundColor Yellow
                $newContent = @()
                while ($line = Read-Host) {
                    $newContent += $line
                }
                $content = $newContent -join "`n"
            }
            "2" {
                $contentFile = Read-Host "Path to content file"
                if (Test-Path $contentFile) {
                    $content = Get-Content -Path $contentFile -Raw
                } else {
                    Write-Error "Content file not found: $contentFile"
                    return
                }
            }
            "3" {
                # Keep current content
            }
            default {
                Write-Error "Invalid option: $contentOption"
                return
            }
        }
    }
    
    # Create new frontmatter
    $newFrontmatter = @"
---
type: always
title: $title
description: $description
globs:
"@

    # Add each glob pattern
    foreach ($glob in $globs) {
        $newFrontmatter += @"

  - "$glob"
"@
    }

    # Add alwaysApply setting and close frontmatter
    $newFrontmatter += @"

alwaysApply: $($alwaysApply.ToString().ToLower())
---

"@

    # Combine frontmatter with content
    Set-Content -Path $ruleFile -Value ($newFrontmatter + $content)
    
    Write-Host "Rule updated successfully: $ruleFile" -ForegroundColor Green
    
    # Save content to tmp directory for backup
    $contentFile = Join-Path $tmpDir "${ruleName}_content.txt"
    Set-Content -Path $contentFile -Value $content
    Write-Host "Content saved to: $contentFile" -ForegroundColor Green
}

# Function to generate batch update scripts
function Generate-UpdateScripts {
    Write-Host "Generate rule update scripts" -ForegroundColor Cyan
    
    # List available rules
    $ruleFiles = Get-ChildItem -Path $rulesDir -Filter "*.mdc" | Select-Object -ExpandProperty BaseName
    
    if ($ruleFiles.Count -eq 0) {
        Write-Error "No rules found in $rulesDir"
        return
    }
    
    Write-Host "Available rules:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $ruleFiles.Count; $i++) {
        Write-Host "$($i+1). $($ruleFiles[$i])"
    }
    
    $ruleIndex = [int](Read-Host "Select rule to generate update script for (1-$($ruleFiles.Count), or 0 for all)") - 1
    
    if ($ruleIndex -eq -1) {
        # Generate for all rules
        foreach ($ruleName in $ruleFiles) {
            Generate-SingleUpdateScript -RuleName $ruleName
        }
    } elseif ($ruleIndex -ge 0 -and $ruleIndex -lt $ruleFiles.Count) {
        Generate-SingleUpdateScript -RuleName $ruleFiles[$ruleIndex]
    } else {
        Write-Error "Invalid selection: $($ruleIndex+1)"
        return
    }
}

# Function to generate a single update script for a rule
function Generate-SingleUpdateScript {
    param (
        [string]$RuleName
    )
    
    $ruleFile = Join-Path $rulesDir "${RuleName}.mdc"
    
    if (-not (Test-Path $ruleFile)) {
        Write-Error "Rule file not found: $ruleFile"
        return
    }
    
    # Extract current frontmatter
    $frontmatter = Get-RuleFrontmatter -FilePath $ruleFile
    $title = Get-FrontmatterValue -Frontmatter $frontmatter -Key "title"
    $description = Get-FrontmatterValue -Frontmatter $frontmatter -Key "description"
    $alwaysApply = Get-FrontmatterValue -Frontmatter $frontmatter -Key "alwaysApply"
    $globs = Get-GlobPatterns -Frontmatter $frontmatter
    
    # Create content for batch file
    $scriptContent = @"
@echo off
REM Update script for $RuleName cursor rule
REM Generated on $(Get-Date)

REM Create the tmp_rules_rebuild directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Extract current content (without frontmatter)
powershell -Command "& {`$content = Get-Content -Raw '.cursor\\rules\\${RuleName}.mdc'; `$match = [regex]::Match(`$content, '---\s*\n.*?---\s*\n(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline); if (`$match.Success) { `$match.Groups[1].Value | Set-Content 'tmp_rules_rebuild\\${RuleName}_content.txt' } else { 'Failed to extract content' | Write-Error }}"

REM Create the frontmatter
echo ---                                                                > .cursor\\rules\\${RuleName}.mdc
echo type: always                                                      >> .cursor\\rules\\${RuleName}.mdc
echo title: $title                                                     >> .cursor\\rules\\${RuleName}.mdc
echo description: $description                                         >> .cursor\\rules\\${RuleName}.mdc
echo globs:                                                            >> .cursor\\rules\\${RuleName}.mdc

"@

    # Add glob patterns
    foreach ($glob in $globs) {
        $scriptContent += @"
echo   - "$glob"                                                       >> .cursor\\rules\\${RuleName}.mdc

"@
    }

    # Add alwaysApply and close frontmatter
    $scriptContent += @"
echo alwaysApply: $($alwaysApply.ToString().ToLower())                                                 >> .cursor\\rules\\${RuleName}.mdc
echo ---                                                                >> .cursor\\rules\\${RuleName}.mdc
echo.                                                                  >> .cursor\\rules\\${RuleName}.mdc

REM Append the content
type tmp_rules_rebuild\\${RuleName}_content.txt                        >> .cursor\\rules\\${RuleName}.mdc

echo ${RuleName} rule updated successfully. 
"@

    # Write script to file
    $scriptFile = Join-Path "scripts\cursor_rules" "update_${RuleName}_rule.bat"
    
    # Create cursor_rules directory if it doesn't exist
    if (-not (Test-Path "scripts\cursor_rules")) {
        New-Item -ItemType Directory -Path "scripts\cursor_rules" -Force | Out-Null
    }
    
    Set-Content -Path $scriptFile -Value $scriptContent
    Write-Host "Update script generated: $scriptFile" -ForegroundColor Green
}

# Main menu
function Show-Menu {
    Write-Host "`nCursor Rules Manager" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    Write-Host "1. List all rules"
    Write-Host "2. Show rule details"
    Write-Host "3. Create new rule"
    Write-Host "4. Update existing rule"
    Write-Host "5. Generate rule update scripts"
    Write-Host "6. Exit"
    
    $choice = Read-Host "Enter your choice (1-6)"
    
    switch ($choice) {
        "1" {
            List-Rules
            Show-Menu
        }
        "2" {
            $ruleName = Read-Host "Enter rule name"
            List-Rules -RuleName $ruleName
            Show-Menu
        }
        "3" {
            Create-Rule
            Show-Menu
        }
        "4" {
            Update-Rule
            Show-Menu
        }
        "5" {
            Generate-UpdateScripts
            Show-Menu
        }
        "6" {
            return
        }
        default {
            Write-Host "Invalid choice. Please try again." -ForegroundColor Red
            Show-Menu
        }
    }
}

# Start the application
Show-Menu 