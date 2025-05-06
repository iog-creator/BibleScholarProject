@echo off
REM Fix script for hebrew_rules cursor rule - changing alwaysApply to false
REM Generated on 05/05/2025 18:02:43

REM Create tmp directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Extract current content (without frontmatter)
powershell -Command "& {$content = Get-Content -Raw '.cursor\\rules\\hebrew_rules.mdc'; $match = [regex]::Match($content, '---\s*\n.*?---\s*\n(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { $match.Groups[1].Value | Set-Content 'tmp_rules_rebuild\\hebrew_rules_content.txt' } else { 'Failed to extract content' | Write-Error }}"

REM Create the frontmatter
echo ---                                                                > .cursor\rules\hebrew_rules.mdc
echo type: always                                                      >> .cursor\rules\hebrew_rules.mdc
echo title: Hebrew Processing Rules                                                     >> .cursor\rules\hebrew_rules.mdc
echo description: Guidelines for processing Hebrew text and Strong's IDs                                         >> .cursor\rules\hebrew_rules.mdc
echo globs:                                                            >> .cursor\rules\hebrew_rules.mdc
echo   - "**/etl/**/*hebrew*.py"                                                       >> .cursor\rules\hebrew_rules.mdc
echo   - "src/etl/hebrew_*.py"                                                       >> .cursor\rules\hebrew_rules.mdc
echo   - "src/api/lexicon/hebrew_*.py"                                                       >> .cursor\rules\hebrew_rules.mdc
echo   - "tests/unit/test_hebrew_*.py"                                                       >> .cursor\rules\hebrew_rules.mdc
echo alwaysApply: false                                                >> .cursor\rules\hebrew_rules.mdc
echo ---                                                                >> .cursor\rules\hebrew_rules.mdc
echo.                                                                  >> .cursor\rules\hebrew_rules.mdc

REM Append the content
type tmp_rules_rebuild\\hebrew_rules_content.txt                        >> .cursor\rules\hebrew_rules.mdc

echo hebrew_rules rule updated to be agent-friendly with alwaysApply: false
