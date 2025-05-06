@echo off
echo ---                                                                > .cursor\rules\dspy_generation.mdc
echo type: always                                                      >> .cursor\rules\dspy_generation.mdc
echo title: DSPy Training Data Generation Guidelines                    >> .cursor\rules\dspy_generation.mdc
echo description: Guidelines for DSPy training data generation and collection >> .cursor\rules\dspy_generation.mdc
echo globs:                                                            >> .cursor\rules\dspy_generation.mdc
echo   - "**/dspy/**/*.py"                                             >> .cursor\rules\dspy_generation.mdc
echo   - "**/data/processed/dspy_*.py"                                 >> .cursor\rules\dspy_generation.mdc
echo   - "scripts/generate_dspy_training_data.py"                      >> .cursor\rules\dspy_generation.mdc
echo   - "scripts/refresh_dspy_data.py"                                >> .cursor\rules\dspy_generation.mdc
echo   - "src/utils/dspy_collector.py"                                 >> .cursor\rules\dspy_generation.mdc
echo alwaysApply: true                                                 >> .cursor\rules\dspy_generation.mdc
echo ---                                                                >> .cursor\rules\dspy_generation.mdc
echo.                                                                  >> .cursor\rules\dspy_generation.mdc
type dspy_content.txt                                                  >> .cursor\rules\dspy_generation.mdc
echo DSPy rule updated successfully. 