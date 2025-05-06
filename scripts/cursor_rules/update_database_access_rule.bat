@echo off
REM Script to update the Database Access rule with proper frontmatter

REM Create directory for rule content if it doesn't exist
if not exist "tmp_rules_rebuild" mkdir tmp_rules_rebuild

REM Ensure we're using the standard content file location
set CONTENT_FILE=tmp_rules_rebuild\database_access_content.txt

REM Get rule content from the current file
powershell -Command "if (Test-Path '.cursor/rules/database_access.mdc') { $content = Get-Content -Path '.cursor/rules/database_access.mdc' -Raw; $match = [regex]::Match($content, '---\s*\n.*?---\s*\n(.*)$', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { Set-Content -Path '%CONTENT_FILE%' -Value $match.Groups[1].Value } else { $match2 = [regex]::Match($content, '^.*?globs:.*?\n(.*?)$', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match2.Success) { Set-Content -Path '%CONTENT_FILE%' -Value $match2.Groups[1].Value } else { Set-Content -Path '%CONTENT_FILE%' -Value $content } } }"

REM Create frontmatter in a separate file
echo --- > tmp_rules_rebuild\database_access_frontmatter.txt
echo type: always >> tmp_rules_rebuild\database_access_frontmatter.txt
echo title: Database Access Patterns >> tmp_rules_rebuild\database_access_frontmatter.txt
echo description: Standards for database access patterns in the BibleScholarProject >> tmp_rules_rebuild\database_access_frontmatter.txt
echo globs: >> tmp_rules_rebuild\database_access_frontmatter.txt
echo   - "src/database/**/*.py" >> tmp_rules_rebuild\database_access_frontmatter.txt
echo   - "src/api/**/*.py" >> tmp_rules_rebuild\database_access_frontmatter.txt
echo   - "tests/unit/test_*db*.py" >> tmp_rules_rebuild\database_access_frontmatter.txt
echo alwaysApply: true >> tmp_rules_rebuild\database_access_frontmatter.txt
echo --- >> tmp_rules_rebuild\database_access_frontmatter.txt
echo. >> tmp_rules_rebuild\database_access_frontmatter.txt

REM Combine frontmatter and content
powershell -Command "Set-Content -Path '.cursor/rules/database_access.mdc' -Value (Get-Content -Path 'tmp_rules_rebuild\database_access_frontmatter.txt' -Raw); Add-Content -Path '.cursor/rules/database_access.mdc' -Value (Get-Content -Path '%CONTENT_FILE%' -Raw);"

echo Database Access rule updated successfully. 