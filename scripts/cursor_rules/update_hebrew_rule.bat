@echo off
REM Script to update the Hebrew Rules with proper frontmatter

REM Create directory for rule content if it doesn't exist
if not exist "tmp_rules_rebuild" mkdir tmp_rules_rebuild

REM Ensure we're using the standard content file location
set CONTENT_FILE=tmp_rules_rebuild\hebrew_rules_content.txt

REM Get rule content from the current file
powershell -Command "if (Test-Path '.cursor/rules/hebrew_rules.mdc') { $content = Get-Content -Path '.cursor/rules/hebrew_rules.mdc' -Raw; $match = [regex]::Match($content, '---\s*\n.*?---\s*\n(.*)$', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { Set-Content -Path '%CONTENT_FILE%' -Value $match.Groups[1].Value } else { Set-Content -Path '%CONTENT_FILE%' -Value $content } }"

REM Create frontmatter in a separate file
echo --- > tmp_rules_rebuild\hebrew_rules_frontmatter.txt
echo type: always >> tmp_rules_rebuild\hebrew_rules_frontmatter.txt
echo title: Hebrew Processing Rules >> tmp_rules_rebuild\hebrew_rules_frontmatter.txt
echo description: Guidelines for processing Hebrew text and Strong's IDs >> tmp_rules_rebuild\hebrew_rules_frontmatter.txt
echo globs: >> tmp_rules_rebuild\hebrew_rules_frontmatter.txt
echo   - "**/etl/**/*hebrew*.py" >> tmp_rules_rebuild\hebrew_rules_frontmatter.txt
echo   - "src/etl/hebrew_*.py" >> tmp_rules_rebuild\hebrew_rules_frontmatter.txt
echo   - "src/api/lexicon/hebrew_*.py" >> tmp_rules_rebuild\hebrew_rules_frontmatter.txt
echo   - "tests/unit/test_hebrew_*.py" >> tmp_rules_rebuild\hebrew_rules_frontmatter.txt
echo alwaysApply: true >> tmp_rules_rebuild\hebrew_rules_frontmatter.txt
echo --- >> tmp_rules_rebuild\hebrew_rules_frontmatter.txt
echo. >> tmp_rules_rebuild\hebrew_rules_frontmatter.txt

REM Combine frontmatter and content
powershell -Command "Set-Content -Path '.cursor/rules/hebrew_rules.mdc' -Value (Get-Content -Path 'tmp_rules_rebuild\hebrew_rules_frontmatter.txt' -Raw); Add-Content -Path '.cursor/rules/hebrew_rules.mdc' -Value (Get-Content -Path '%CONTENT_FILE%' -Raw);"

echo Hebrew Rules updated successfully. 