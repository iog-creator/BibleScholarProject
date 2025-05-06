@echo off
echo Fixing the comprehensive_semantic_search.mdc rule...

:: Get the project root directory (3 levels up from this script)
set "PROJECT_ROOT=%~dp0..\..\..\"

:: Create the tmp directory if it doesn't exist
if not exist "%PROJECT_ROOT%tmp_rules_rebuild" mkdir "%PROJECT_ROOT%tmp_rules_rebuild"

:: Extract the current content without frontmatter
powershell -Command "if (Test-Path '%PROJECT_ROOT%.cursor\rules\comprehensive_semantic_search.mdc') { $content = Get-Content -Raw '%PROJECT_ROOT%.cursor\rules\comprehensive_semantic_search.mdc'; $match = [regex]::Match($content, '^---\s*\n(.*?)---\s*\n(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { $match.Groups[2].Value } else { $content } } else { '' }" > "%PROJECT_ROOT%tmp_rules_rebuild\comprehensive_semantic_search_content.txt"

:: Create a new rule with proper frontmatter
(
echo ---
echo type: always
echo title: Comprehensive Semantic Search Integration
echo description: Guidelines for integrating all Bible database resources with pgvector semantic search capabilities
echo globs:
echo   - "src/api/comprehensive_search/*.py"
echo   - "src/utils/vector_search_utils.py"
echo   - "tests/integration/test_comprehensive_search/*.py"
echo alwaysApply: false
echo ---
) > "%PROJECT_ROOT%.cursor\rules\comprehensive_semantic_search.mdc.new"

:: Append the extracted content
type "%PROJECT_ROOT%tmp_rules_rebuild\comprehensive_semantic_search_content.txt" >> "%PROJECT_ROOT%.cursor\rules\comprehensive_semantic_search.mdc.new"

:: Replace the old file with the new one
move /y "%PROJECT_ROOT%.cursor\rules\comprehensive_semantic_search.mdc.new" "%PROJECT_ROOT%.cursor\rules\comprehensive_semantic_search.mdc"

echo Fix applied successfully! 