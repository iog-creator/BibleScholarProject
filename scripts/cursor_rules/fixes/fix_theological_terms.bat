@echo off
REM Fix script for theological_terms cursor rule - changing alwaysApply to false
REM Generated on 05/05/2025 18:02:43

REM Create tmp directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Extract current content (without frontmatter)
powershell -Command "& {$content = Get-Content -Raw '.cursor\\rules\\theological_terms.mdc'; $match = [regex]::Match($content, '---\s*\n.*?---\s*\n(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { $match.Groups[1].Value | Set-Content 'tmp_rules_rebuild\\theological_terms_content.txt' } else { 'Failed to extract content' | Write-Error }}"

REM Create the frontmatter
echo ---                                                                > .cursor\rules\theological_terms.mdc
echo type: always                                                      >> .cursor\rules\theological_terms.mdc
echo title: Theological Terms Guidelines                                                     >> .cursor\rules\theological_terms.mdc
echo description: Guidelines for Hebrew theological term handling                                         >> .cursor\rules\theological_terms.mdc
echo globs:                                                            >> .cursor\rules\theological_terms.mdc
echo   - "**/etl/**/*hebrew*.py"                                                       >> .cursor\rules\theological_terms.mdc
echo   - "**/etl/fix_hebrew_strongs_ids.py"                                                       >> .cursor\rules\theological_terms.mdc
echo   - "**/api/**/*theological*.py"                                                       >> .cursor\rules\theological_terms.mdc
echo alwaysApply: false                                                >> .cursor\rules\theological_terms.mdc
echo ---                                                                >> .cursor\rules\theological_terms.mdc
echo.                                                                  >> .cursor\rules\theological_terms.mdc

REM Append the content
type tmp_rules_rebuild\\theological_terms_content.txt                        >> .cursor\rules\theological_terms.mdc

echo theological_terms rule updated to be agent-friendly with alwaysApply: false
