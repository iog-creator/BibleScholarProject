<#
.SYNOPSIS
    Creates a new cursor rule from the template.

.DESCRIPTION
    This script creates a new cursor rule file (.mdc) in the .cursor/rules directory
    using the template from templates/cursor_rule_template.md.

.PARAMETER RuleName
    Name of the rule (without extension)

.EXAMPLE
    .\new_rule.ps1 -RuleName "documentation_standards"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$RuleName
)

# Define paths
$templateFile = "templates/cursor_rule_template.md"
$ruleFile = ".cursor/rules/${RuleName}.mdc"
$tmpDir = "tmp_rules_rebuild"

# Check if template exists
if (-not (Test-Path $templateFile)) {
    Write-Error "Template file not found: $templateFile"
    exit 1
}

# Check if rule already exists
if (Test-Path $ruleFile) {
    Write-Error "Rule already exists: $ruleFile"
    exit 1
}

# Create tmp directory if it doesn't exist
if (-not (Test-Path $tmpDir)) {
    New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
}

# Copy template to new rule file
Copy-Item -Path $templateFile -Destination $ruleFile

# Open the rule file in the default editor
Write-Host "Opening rule file for editing..."
Invoke-Item $ruleFile

Write-Host @"
Rule created: $ruleFile

Don't forget to:
1. Update the rule title and description
2. Set appropriate glob patterns
3. Save your changes
4. Run .\manage_rules.ps1 to verify the rule

For detailed rule management, run:
.\manage_rules.ps1
"@ -ForegroundColor Green 