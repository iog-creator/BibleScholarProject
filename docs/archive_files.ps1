# Archive script for consolidated documentation files
# This script copies files to the archive directory with a note about where they were moved

# Files to archive
$files_to_archive = @(
    @{
        File = "TESTING_FRAMEWORK.md";
        NewLocation = "guides/testing_framework.md"
    },
    @{
        File = "DATA_VERIFICATION.md";
        NewLocation = "guides/data_verification.md"
    },
    @{
        File = "etl_rules.md";
        NewLocation = "features/etl_pipeline.md"
    },
    @{
        File = "ORGANIZATION.md";
        NewLocation = "reference/SYSTEM_ARCHITECTURE.md"
    },
    @{
        File = "CURSOR_RULES_GUIDE.md";
        NewLocation = ".cursor/rules/README.md"
    },
    @{
        File = "database_rules.md";
        NewLocation = "reference/DATABASE_SCHEMA.md"
    },
    @{
        File = "import_rules.md";
        NewLocation = "rules/import_structure.md"
    },
    @{
        File = "compatibility_rules.md";
        NewLocation = "feature-specific documentation files"
    }
)

# Process each file
foreach ($file in $files_to_archive) {
    $source_path = Join-Path -Path "docs" -ChildPath $file.File
    $dest_path = Join-Path -Path "docs/archive" -ChildPath $file.File
    
    if (Test-Path $source_path) {
        Write-Host "Archiving $($file.File)..."
        
        # Read file content
        $content = Get-Content -Path $source_path -Raw
        
        # Add note at the top
        $note = @"
# ARCHIVED: This file has been consolidated

This file has been archived as part of the documentation reorganization.
The content of this file has been moved to: `docs/$($file.NewLocation)`

Please refer to the new location for the most up-to-date information.

---------------------------------------------

"@
        
        # Write to destination with note
        $note + $content | Out-File -FilePath $dest_path
        
        Write-Host "  - Archived to $dest_path"
    }
    else {
        Write-Host "Warning: $source_path does not exist"
    }
}

Write-Host "Archive process completed." 