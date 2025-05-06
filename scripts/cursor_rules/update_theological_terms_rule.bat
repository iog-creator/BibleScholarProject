@echo off
REM Script to update the Theological Terms rule with proper frontmatter

REM Create directory for rule content if it doesn't exist
if not exist "tmp_rules_rebuild" mkdir tmp_rules_rebuild

REM Ensure we're using the standard content file location
set CONTENT_FILE=tmp_rules_rebuild\theological_terms_content.txt

REM Get rule content from the current file
powershell -Command "if (Test-Path '.cursor/rules/theological_terms.mdc') { $content = Get-Content -Path '.cursor/rules/theological_terms.mdc' -Raw; $match = [regex]::Match($content, '---\s*\n.*?---\s*\n(.*)$', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { Set-Content -Path '%CONTENT_FILE%' -Value $match.Groups[1].Value } else { Set-Content -Path '%CONTENT_FILE%' -Value $content } }"

REM Create frontmatter in a separate file
echo --- > tmp_rules_rebuild\theological_terms_frontmatter.txt
echo type: always >> tmp_rules_rebuild\theological_terms_frontmatter.txt
echo title: Theological Terms Guidelines >> tmp_rules_rebuild\theological_terms_frontmatter.txt
echo description: Guidelines for Hebrew theological term handling >> tmp_rules_rebuild\theological_terms_frontmatter.txt
echo globs: >> tmp_rules_rebuild\theological_terms_frontmatter.txt
echo   - "**/etl/**/*hebrew*.py" >> tmp_rules_rebuild\theological_terms_frontmatter.txt
echo   - "**/etl/fix_hebrew_strongs_ids.py" >> tmp_rules_rebuild\theological_terms_frontmatter.txt
echo   - "**/api/**/*theological*.py" >> tmp_rules_rebuild\theological_terms_frontmatter.txt
echo alwaysApply: true >> tmp_rules_rebuild\theological_terms_frontmatter.txt
echo --- >> tmp_rules_rebuild\theological_terms_frontmatter.txt
echo. >> tmp_rules_rebuild\theological_terms_frontmatter.txt

REM Combine frontmatter and content
powershell -Command "Set-Content -Path '.cursor/rules/theological_terms.mdc' -Value (Get-Content -Path 'tmp_rules_rebuild\theological_terms_frontmatter.txt' -Raw); Add-Content -Path '.cursor/rules/theological_terms.mdc' -Value (Get-Content -Path '%CONTENT_FILE%' -Raw);"

echo Theological Terms rule updated successfully. 