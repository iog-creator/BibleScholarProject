@echo off
REM Script to update the TVTMS Database Handling rule with proper frontmatter

REM Create directory for rule content if it doesn't exist
if not exist "tmp_rules_rebuild" mkdir tmp_rules_rebuild

REM Ensure we're using the standard content file location
set CONTENT_FILE=tmp_rules_rebuild\tvtms_database_handling_content.txt

REM Get rule content from the current file
powershell -Command "if (Test-Path '.cursor/rules/tvtms_database_handling.mdc') { $content = Get-Content -Path '.cursor/rules/tvtms_database_handling.mdc' -Raw; $match = [regex]::Match($content, '---\s*\n.*?---\s*\n(.*)$', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { Set-Content -Path '%CONTENT_FILE%' -Value $match.Groups[1].Value } else { Set-Content -Path '%CONTENT_FILE%' -Value $content } }"

REM Create frontmatter in a separate file
echo --- > tmp_rules_rebuild\tvtms_database_handling_frontmatter.txt
echo type: always >> tmp_rules_rebuild\tvtms_database_handling_frontmatter.txt
echo title: TVTMS Database Handling >> tmp_rules_rebuild\tvtms_database_handling_frontmatter.txt
echo description: Guidelines for TVTMS database operations and versification mapping >> tmp_rules_rebuild\tvtms_database_handling_frontmatter.txt
echo globs: >> tmp_rules_rebuild\tvtms_database_handling_frontmatter.txt
echo   - "src/tvtms/**/*.py" >> tmp_rules_rebuild\tvtms_database_handling_frontmatter.txt
echo   - "src/database/tvtms_*.py" >> tmp_rules_rebuild\tvtms_database_handling_frontmatter.txt
echo   - "tests/unit/test_*tvtms*.py" >> tmp_rules_rebuild\tvtms_database_handling_frontmatter.txt
echo alwaysApply: false >> tmp_rules_rebuild\tvtms_database_handling_frontmatter.txt
echo --- >> tmp_rules_rebuild\tvtms_database_handling_frontmatter.txt
echo. >> tmp_rules_rebuild\tvtms_database_handling_frontmatter.txt

REM Combine frontmatter and content
powershell -Command "Set-Content -Path '.cursor/rules/tvtms_database_handling.mdc' -Value (Get-Content -Path 'tmp_rules_rebuild\tvtms_database_handling_frontmatter.txt' -Raw); Add-Content -Path '.cursor/rules/tvtms_database_handling.mdc' -Value (Get-Content -Path '%CONTENT_FILE%' -Raw);"

echo TVTMS Database Handling rule updated successfully. 