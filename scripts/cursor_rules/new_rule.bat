@echo off
REM Script to generate a new cursor rule from template
REM Usage: new_rule.bat rule_name "Rule Title" "Rule Description" "glob/pattern/*.ext"

REM Check for required parameters
if "%~1"=="" (
    echo ERROR: Missing rule name
    echo Usage: new_rule.bat rule_name "Rule Title" "Rule Description" "glob/pattern/*.ext"
    exit /b 1
)

if "%~2"=="" (
    echo ERROR: Missing rule title
    echo Usage: new_rule.bat rule_name "Rule Title" "Rule Description" "glob/pattern/*.ext"
    exit /b 1
)

if "%~3"=="" (
    echo ERROR: Missing rule description
    echo Usage: new_rule.bat rule_name "Rule Title" "Rule Description" "glob/pattern/*.ext"
    exit /b 1
)

if "%~4"=="" (
    echo ERROR: Missing glob pattern
    echo Usage: new_rule.bat rule_name "Rule Title" "Rule Description" "glob/pattern/*.ext"
    exit /b 1
)

REM Set variables
set RULE_NAME=%~1
set RULE_TITLE=%~2
set RULE_DESCRIPTION=%~3
set RULE_GLOB=%~4
set TEMPLATE_FILE=templates\cursor_rule_template.md
set OUTPUT_FILE=.cursor\rules\%RULE_NAME%.mdc

REM Check if template exists
if not exist %TEMPLATE_FILE% (
    echo ERROR: Template file not found: %TEMPLATE_FILE%
    exit /b 1
)

REM Check if rule already exists
if exist %OUTPUT_FILE% (
    echo ERROR: Rule already exists: %OUTPUT_FILE%
    echo Use update_rule.ps1 to update an existing rule
    exit /b 1
)

REM Create tmp directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Create temporary working file
copy %TEMPLATE_FILE% tmp_rules_rebuild\temp_rule.md > nul

REM Replace placeholders
powershell -Command "& {(Get-Content tmp_rules_rebuild\temp_rule.md) -replace '{{RULE_TITLE}}', '%RULE_TITLE%' -replace '{{RULE_DESCRIPTION}}', '%RULE_DESCRIPTION%' -replace '{{RULE_GLOB_PATTERN}}', '%RULE_GLOB%' -replace '{{LANGUAGE}}', 'python' | Set-Content %OUTPUT_FILE%}"

REM Clean up
del tmp_rules_rebuild\temp_rule.md > nul

echo New rule created: %OUTPUT_FILE%
echo.
echo To edit the rule content:
echo 1. Open the file in your editor
echo 2. Replace the placeholder content with your actual rule guidance
echo 3. Add examples and guidelines specific to your rule 