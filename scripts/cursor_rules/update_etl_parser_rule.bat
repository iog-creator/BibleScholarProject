@echo off
REM Script to update the ETL Parser Strictness rule with proper frontmatter and content

REM Create directory for rule content if it doesn't exist
if not exist "tmp_rules_rebuild" mkdir tmp_rules_rebuild

REM Create content file with ETL parser guidelines
echo # ETL Parser Strictness Guidelines > tmp_rules_rebuild\etl_parser_strictness_content.txt
echo. >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo ## Overview >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo. >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo This rule defines standards for parser strictness levels in ETL processes. >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo. >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo ## Parser Strictness Levels >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo. >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo ETL parsers should support the following strictness levels: >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo. >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo 1. **STRICT**: Fail on any formatting or data quality issue >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo 2. **NORMAL**: Fail on critical issues, log warnings for minor issues >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo 3. **LENIENT**: Attempt to recover from all errors, log warnings >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo. >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo ## Implementation Guidelines >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo. >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo ```python >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo from enum import Enum >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo. >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo class ParserStrictness(Enum): >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo     STRICT = "strict"   # Fail on any issue >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo     NORMAL = "normal"   # Default behavior >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo     LENIENT = "lenient" # Best-effort parsing >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo. >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo def parse_file(file_path, strictness=ParserStrictness.NORMAL): >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo     # Implementation that respects strictness level >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo     # ... >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo ``` >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo. >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo ## Error Handling >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo. >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo 1. Document which errors are considered critical vs. minor >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo 2. Log all issues regardless of strictness level >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo 3. Always include line number and context in error messages >> tmp_rules_rebuild\etl_parser_strictness_content.txt
echo 4. Provide summary statistics of issues encountered >> tmp_rules_rebuild\etl_parser_strictness_content.txt

REM Create frontmatter in a separate file
echo --- > tmp_rules_rebuild\etl_parser_strictness_frontmatter.txt
echo type: always >> tmp_rules_rebuild\etl_parser_strictness_frontmatter.txt
echo title: ETL Parser Strictness Guidelines >> tmp_rules_rebuild\etl_parser_strictness_frontmatter.txt
echo description: Standards for configuring parser strictness levels in ETL processes >> tmp_rules_rebuild\etl_parser_strictness_frontmatter.txt
echo globs: >> tmp_rules_rebuild\etl_parser_strictness_frontmatter.txt
echo   - "src/etl/**/*.py" >> tmp_rules_rebuild\etl_parser_strictness_frontmatter.txt
echo   - "scripts/etl_*.py" >> tmp_rules_rebuild\etl_parser_strictness_frontmatter.txt
echo alwaysApply: false >> tmp_rules_rebuild\etl_parser_strictness_frontmatter.txt
echo --- >> tmp_rules_rebuild\etl_parser_strictness_frontmatter.txt
echo. >> tmp_rules_rebuild\etl_parser_strictness_frontmatter.txt

REM Combine frontmatter and content
powershell -Command "Set-Content -Path '.cursor/rules/etl_parser_strictness.mdc' -Value (Get-Content -Path 'tmp_rules_rebuild\etl_parser_strictness_frontmatter.txt' -Raw); Add-Content -Path '.cursor/rules/etl_parser_strictness.mdc' -Value (Get-Content -Path 'tmp_rules_rebuild\etl_parser_strictness_content.txt' -Raw);"

echo ETL Parser Strictness rule updated successfully. 