@echo off
REM Script to update the Public Domain Bible Processing rule with proper frontmatter

REM Create directory for rule content if it doesn't exist
if not exist "tmp_rules_rebuild" mkdir tmp_rules_rebuild

REM Ensure we're using the standard content file location
set CONTENT_FILE=tmp_rules_rebuild\public_domain_bible_processing_content.txt

REM Get rule content from the current file
powershell -Command "if (Test-Path '.cursor/rules/public_domain_bible_processing.mdc') { $content = Get-Content -Path '.cursor/rules/public_domain_bible_processing.mdc' -Raw; $match = [regex]::Match($content, '---\s*\n.*?---\s*\n(.*)$', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { Set-Content -Path '%CONTENT_FILE%' -Value $match.Groups[1].Value } else { Set-Content -Path '%CONTENT_FILE%' -Value $content } }"

REM Create frontmatter in a separate file
echo --- > tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt
echo type: always >> tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt
echo title: Public Domain Bible Processing >> tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt
echo description: Guidelines for processing public domain Bible translations (KJV, ASV, WEB) >> tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt
echo globs: >> tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt
echo   - "load_kjv_bible.py" >> tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt
echo   - "load_asv_bible.py" >> tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt
echo   - "load_public_domain_bibles.py" >> tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt
echo   - "src/etl/public_domain_*.py" >> tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt
echo alwaysApply: false >> tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt
echo --- >> tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt
echo. >> tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt

REM Combine frontmatter and content
powershell -Command "Set-Content -Path '.cursor/rules/public_domain_bible_processing.mdc' -Value (Get-Content -Path 'tmp_rules_rebuild\public_domain_bible_processing_frontmatter.txt' -Raw); Add-Content -Path '.cursor/rules/public_domain_bible_processing.mdc' -Value (Get-Content -Path '%CONTENT_FILE%' -Raw);"

echo Public Domain Bible Processing rule updated successfully. 