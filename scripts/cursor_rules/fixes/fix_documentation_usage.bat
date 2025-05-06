@echo off
REM Fix script for documentation_usage cursor rule - changing alwaysApply to false
REM Generated on 05/05/2025 18:02:43

REM Create tmp directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Extract current content (without frontmatter)
powershell -Command "& {$content = Get-Content -Raw '.cursor\\rules\\documentation_usage.mdc'; $match = [regex]::Match($content, '---\s*\n.*?---\s*\n(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { $match.Groups[1].Value | Set-Content 'tmp_rules_rebuild\\documentation_usage_content.txt' } else { 'Failed to extract content' | Write-Error }}"

REM Create the frontmatter
echo ---                                                                > .cursor\rules\documentation_usage.mdc
echo type: always                                                      >> .cursor\rules\documentation_usage.mdc
echo title: Documentation Usage Guidelines                                                     >> .cursor\rules\documentation_usage.mdc
echo description: Guidelines for utilizing and updating documentation in the BibleScholarProject                                         >> .cursor\rules\documentation_usage.mdc
echo globs:                                                            >> .cursor\rules\documentation_usage.mdc
echo   - "src/**/*.py"                                                       >> .cursor\rules\documentation_usage.mdc
echo   - "scripts/*.py"                                                       >> .cursor\rules\documentation_usage.mdc
echo   - "tests/**/*.py"                                                       >> .cursor\rules\documentation_usage.mdc
echo alwaysApply: false                                                >> .cursor\rules\documentation_usage.mdc
echo ---                                                                >> .cursor\rules\documentation_usage.mdc
echo.                                                                  >> .cursor\rules\documentation_usage.mdc

REM Append the content
type tmp_rules_rebuild\\documentation_usage_content.txt                        >> .cursor\rules\documentation_usage.mdc

echo documentation_usage rule updated to be agent-friendly with alwaysApply: false
