@echo off
REM Script to update the Greek Morphology Count Tolerance rule with proper frontmatter

REM Create directory for rule content if it doesn't exist
if not exist "tmp_rules_rebuild" mkdir tmp_rules_rebuild

REM Ensure we're using the standard content file location
set CONTENT_FILE=tmp_rules_rebuild\greek_morphology_count_tolerance_content.txt

REM Get rule content from the current file
powershell -Command "if (Test-Path '.cursor/rules/greek_morphology_count_tolerance.mdc') { $content = Get-Content -Path '.cursor/rules/greek_morphology_count_tolerance.mdc' -Raw; $match = [regex]::Match($content, '---\s*\n.*?---\s*\n(.*)$', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { Set-Content -Path '%CONTENT_FILE%' -Value $match.Groups[1].Value } else { Set-Content -Path '%CONTENT_FILE%' -Value $content } }"

REM Create frontmatter in a separate file
echo --- > tmp_rules_rebuild\greek_morphology_count_tolerance_frontmatter.txt
echo type: always >> tmp_rules_rebuild\greek_morphology_count_tolerance_frontmatter.txt
echo title: Greek Morphology Count Tolerance >> tmp_rules_rebuild\greek_morphology_count_tolerance_frontmatter.txt
echo description: Guidelines for tolerance levels in Greek morphology code counts >> tmp_rules_rebuild\greek_morphology_count_tolerance_frontmatter.txt
echo globs: >> tmp_rules_rebuild\greek_morphology_count_tolerance_frontmatter.txt
echo   - "src/etl/**/greek_*.py" >> tmp_rules_rebuild\greek_morphology_count_tolerance_frontmatter.txt
echo   - "src/etl/morphology/greek_*.py" >> tmp_rules_rebuild\greek_morphology_count_tolerance_frontmatter.txt
echo   - "tests/unit/test_greek_*.py" >> tmp_rules_rebuild\greek_morphology_count_tolerance_frontmatter.txt
echo alwaysApply: false >> tmp_rules_rebuild\greek_morphology_count_tolerance_frontmatter.txt
echo --- >> tmp_rules_rebuild\greek_morphology_count_tolerance_frontmatter.txt
echo. >> tmp_rules_rebuild\greek_morphology_count_tolerance_frontmatter.txt

REM Combine frontmatter and content
powershell -Command "Set-Content -Path '.cursor/rules/greek_morphology_count_tolerance.mdc' -Value (Get-Content -Path 'tmp_rules_rebuild\greek_morphology_count_tolerance_frontmatter.txt' -Raw); Add-Content -Path '.cursor/rules/greek_morphology_count_tolerance.mdc' -Value (Get-Content -Path '%CONTENT_FILE%' -Raw);"

echo Greek Morphology Count Tolerance rule updated successfully. 