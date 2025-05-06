@echo off
REM Fix script for dspy_generation cursor rule - changing alwaysApply to false
REM Generated on 05/05/2025 18:02:43

REM Create tmp directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Extract current content (without frontmatter)
powershell -Command "& {$content = Get-Content -Raw '.cursor\\rules\\dspy_generation.mdc'; $match = [regex]::Match($content, '---\s*\n.*?---\s*\n(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { $match.Groups[1].Value | Set-Content 'tmp_rules_rebuild\\dspy_generation_content.txt' } else { 'Failed to extract content' | Write-Error }}"

REM Create the frontmatter
echo ---                                                                > .cursor\rules\dspy_generation.mdc
echo type: always                                                      >> .cursor\rules\dspy_generation.mdc
echo title: DSPy Training Data Generation Guidelines                                                     >> .cursor\rules\dspy_generation.mdc
echo description: Guidelines for DSPy training data generation and collection                                         >> .cursor\rules\dspy_generation.mdc
echo globs:                                                            >> .cursor\rules\dspy_generation.mdc
echo   - "**/dspy/**/*.py"                                                       >> .cursor\rules\dspy_generation.mdc
echo   - "**/data/processed/dspy_*.py"                                                       >> .cursor\rules\dspy_generation.mdc
echo   - "scripts/generate_dspy_training_data.py"                                                       >> .cursor\rules\dspy_generation.mdc
echo   - "scripts/refresh_dspy_data.py"                                                       >> .cursor\rules\dspy_generation.mdc
echo   - "src/utils/dspy_collector.py"                                                       >> .cursor\rules\dspy_generation.mdc
echo alwaysApply: false                                                >> .cursor\rules\dspy_generation.mdc
echo ---                                                                >> .cursor\rules\dspy_generation.mdc
echo.                                                                  >> .cursor\rules\dspy_generation.mdc

REM Append the content
type tmp_rules_rebuild\\dspy_generation_content.txt                        >> .cursor\rules\dspy_generation.mdc

echo dspy_generation rule updated to be agent-friendly with alwaysApply: false
