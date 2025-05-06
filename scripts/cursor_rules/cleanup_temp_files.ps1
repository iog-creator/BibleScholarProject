<#
.SYNOPSIS
    Cleans up temporary files created during cursor rule management.

.DESCRIPTION
    This script organizes the tmp_rules_rebuild directory by:
    1. Moving well-structured content files to an archive folder
    2. Deleting redundant or unnecessary temporary files
    3. Creating a backup of current rule files

.PARAMETER ArchiveUnused
    Whether to archive unused temporary files (default: false)

.EXAMPLE
    .\cleanup_temp_files.ps1

.EXAMPLE
    .\cleanup_temp_files.ps1 -ArchiveUnused $true
#>

param(
    [Parameter(Mandatory=$false)]
    [bool]$ArchiveUnused = $false
)

# Create backup directory if it doesn't exist
$backupDir = "tmp_rules_rebuild/backups"
if (-not (Test-Path $backupDir)) {
    New-Item -Path $backupDir -ItemType Directory | Out-Null
    Write-Host "Created backup directory: $backupDir" -ForegroundColor Green
}

# Create archive directory if it doesn't exist and archiving is enabled
$archiveDir = "tmp_rules_rebuild/archive"
if ($ArchiveUnused -and -not (Test-Path $archiveDir)) {
    New-Item -Path $archiveDir -ItemType Directory | Out-Null
    Write-Host "Created archive directory: $archiveDir" -ForegroundColor Green
}

# Backup current rule files
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$backupDir/rules_backup_$timestamp.zip"
Compress-Archive -Path ".cursor/rules/*.mdc" -DestinationPath $backupFile
Write-Host "Created backup of rule files: $backupFile" -ForegroundColor Green

# Get all content files
$contentFiles = Get-ChildItem -Path "tmp_rules_rebuild" -Filter "*_content.txt"

# Get all rule files
$ruleFiles = Get-ChildItem -Path ".cursor/rules" -Filter "*.mdc" | ForEach-Object { $_.BaseName }

# Process content files
foreach ($file in $contentFiles) {
    $ruleName = $file.BaseName -replace "_content$", ""
    $ruleExists = $ruleFiles -contains $ruleName
    
    if ($ruleExists) {
        Write-Host "Keeping content file for active rule: $($file.Name)" -ForegroundColor Cyan
    } elseif ($ArchiveUnused) {
        # Move to archive
        Move-Item -Path $file.FullName -Destination "$archiveDir/$($file.Name)"
        Write-Host "Archived unused content file: $($file.Name)" -ForegroundColor Yellow
    } else {
        Write-Host "Found unused content file: $($file.Name)" -ForegroundColor Yellow
    }
}

# Clean up other temporary files
$tempFiles = Get-ChildItem -Path "tmp_rules_rebuild" -Exclude "*_content.txt", "backups", "archive"
foreach ($file in $tempFiles) {
    if ($file.PSIsContainer) {
        # Skip directories
        continue
    }
    
    # Check if file is a frontmatter or temporary script
    if ($file.Name -like "*_frontmatter.txt" -or $file.Name -like "*.tmp") {
        Remove-Item -Path $file.FullName
        Write-Host "Removed temporary file: $($file.Name)" -ForegroundColor Gray
    }
}

Write-Host "`nCleanup complete. Current tmp_rules_rebuild directory structure:" -ForegroundColor Green
Get-ChildItem -Path "tmp_rules_rebuild" -Recurse | Format-Table -AutoSize 