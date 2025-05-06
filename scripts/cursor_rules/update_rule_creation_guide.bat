@echo off
REM Update script for rule_creation_guide cursor rule
REM Generated manually

REM Create the tmp_rules_rebuild directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Make sure the content file exists
if not exist tmp_rules_rebuild\rule_creation_guide_updated.md echo ERROR: Content file tmp_rules_rebuild\rule_creation_guide_updated.md not found && exit /b 1

REM Create the frontmatter
echo ---                                                                > .cursor\rules\rule_creation_guide.mdc
echo type: always                                                      >> .cursor\rules\rule_creation_guide.mdc
echo title: Cursor Rule Creation Guidelines                            >> .cursor\rules\rule_creation_guide.mdc
echo description: Guidelines for creating and maintaining Cursor rules using the standardized tools >> .cursor\rules\rule_creation_guide.mdc
echo globs:                                                            >> .cursor\rules\rule_creation_guide.mdc
echo   - ".cursor/rules/*.mdc"                                         >> .cursor\rules\rule_creation_guide.mdc
echo   - "scripts/cursor_rules/*.ps1"                                  >> .cursor\rules\rule_creation_guide.mdc
echo alwaysApply: true                                                 >> .cursor\rules\rule_creation_guide.mdc
echo ---                                                                >> .cursor\rules\rule_creation_guide.mdc
echo.                                                                  >> .cursor\rules\rule_creation_guide.mdc

REM Append the content
type tmp_rules_rebuild\rule_creation_guide_updated.md                  >> .cursor\rules\rule_creation_guide.mdc

echo rule_creation_guide rule updated successfully. 