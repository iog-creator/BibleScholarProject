@echo off
REM Fix script for database_access cursor rule - changing alwaysApply to false
REM Generated on 05/05/2025 18:02:43

REM Create tmp directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Extract current content (without frontmatter)
powershell -Command "& {$content = Get-Content -Raw '.cursor\\rules\\database_access.mdc'; $match = [regex]::Match($content, '---\s*\n.*?---\s*\n(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { $match.Groups[1].Value | Set-Content 'tmp_rules_rebuild\\database_access_content.txt' } else { 'Failed to extract content' | Write-Error }}"

REM Create the frontmatter
echo ---                                                                > .cursor\rules\database_access.mdc
echo type: always                                                      >> .cursor\rules\database_access.mdc
echo title: Database Access Patterns                                                     >> .cursor\rules\database_access.mdc
echo description: Standards for database access patterns in the BibleScholarProject                                         >> .cursor\rules\database_access.mdc
echo globs:                                                            >> .cursor\rules\database_access.mdc
echo   - "src/database/**/*.py"                                                       >> .cursor\rules\database_access.mdc
echo   - "src/api/**/*.py"                                                       >> .cursor\rules\database_access.mdc
echo   - "tests/unit/test_*db*.py"                                                       >> .cursor\rules\database_access.mdc
echo alwaysApply: false                                                >> .cursor\rules\database_access.mdc
echo ---                                                                >> .cursor\rules\database_access.mdc
echo.                                                                  >> .cursor\rules\database_access.mdc

REM Append the content
type tmp_rules_rebuild\\database_access_content.txt                        >> .cursor\rules\database_access.mdc

echo database_access rule updated to be agent-friendly with alwaysApply: false
