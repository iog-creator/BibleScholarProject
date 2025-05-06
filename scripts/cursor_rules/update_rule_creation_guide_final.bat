@echo off
REM Update script for rule_creation_guide cursor rule
REM Generated on 2023-10-26 12:00:00

REM Create the tmp_rules_rebuild directory if it doesn't exist
if not exist tmp_rules_rebuild mkdir tmp_rules_rebuild

REM Extract current content 
powershell -Command "& {$content = Get-Content -Raw '.cursor\\rules\\rule_creation_guide.mdc'; $match = [regex]::Match($content, '---\s*\n.*?---\s*\n(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline); if ($match.Success) { $match.Groups[1].Value | Set-Content 'tmp_rules_rebuild\\rule_creation_guide_content.txt' } else { 'Failed to extract content' | Write-Error }}"

REM Create new content file with proper frontmatter
echo # Cursor Rule Creation Guidelines> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ## Rule Structure>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo Each Cursor rule must have two key components:>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 1. **YAML Frontmatter** - Metadata enclosed in `---` tags>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 2. **Rule Content** - Markdown content explaining the rule>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ### YAML Frontmatter Requirements>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ```yaml>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo --->> tmp_rules_rebuild\rule_creation_guide_full.txt
echo type: always          # Rule type (always or agentRequested)>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo title: Rule Title     # Short, descriptive title>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo description: Brief description of what the rule does>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo globs:                # File patterns this rule applies to>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo   - "pattern/to/match/*.py">> tmp_rules_rebuild\rule_creation_guide_full.txt
echo   - "other/pattern/*.js">> tmp_rules_rebuild\rule_creation_guide_full.txt
echo alwaysApply: false    # Whether rule is automatically included for all files>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo --->> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ```>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ## Agent Compatibility>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo To ensure rules work well with AI agents:>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 1. **Set `alwaysApply: false` by default** - This prevents rules from being auto-applied to all conversations, which can overwhelm agents with too many rules.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 2. **Use specific glob patterns** - Target only the files where the rule is relevant to avoid rule noise.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 3. **When to use `alwaysApply: true`**:>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo    - Only for critical rules that must ALWAYS be followed>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo    - For project-wide standards that apply universally>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo    - When providing essential context needed for all interactions>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 4. **Use the audit tools** to identify rules that should be converted to `alwaysApply: false`:>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo    ```powershell>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo    # Run the audit script>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo    .\scripts\cursor_rules\audit_rules_auto.ps1>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo    >> tmp_rules_rebuild\rule_creation_guide_full.txt
echo    # Apply the fixes>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo    .\scripts\cursor_rules\fixes\apply_all_fixes.bat>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo    ```>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ## Rule Types>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo | Type | Description | Use Case |>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo |------|-------------|----------|>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo | `always` | Standard rule type | Most rules |>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo | `agentRequested` | Can be requested by agent | Reference material |>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ## Creating New Rules>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ### Option 1: Use the Management Scripts>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo The easiest way to manage rules is with the provided scripts:>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ```powershell>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo # Interactive rule management>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo .\scripts\cursor_rules\manage_rules.ps1>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo # Create a new rule>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo .\scripts\cursor_rules\create_rule.ps1 -RuleName "your_rule_name" -Title "Your Rule Title" -Description "Your rule description" -Globs @("**/path/to/*.py")>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo # Generate a non-interactive batch script>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo .\scripts\cursor_rules\generate_rule_script.ps1 -RuleName "your_rule_name" -Title "Your Rule Title" -Description "Your rule description" -Globs @("**/path/to/*.py")>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ```>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ### Option 2: Use the Template>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 1. Copy the template from `templates/cursor_rule_template.md`>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 2. Replace the placeholders with your rule content>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 3. Save to `.cursor/rules/your_rule_name.mdc`>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ### Option 3: Manual Creation>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 1. Create a new file in `.cursor/rules/` with `.mdc` extension>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 2. Add YAML frontmatter with required fields>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 3. Add detailed markdown content after the frontmatter>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ## Best Practices>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 1. **Descriptive titles and descriptions** - Make it clear what the rule does>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 2. **Specific glob patterns** - Target only files where the rule applies>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 3. **Avoid `alwaysApply: true`** - Set to false for most rules>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 4. **Include examples** - Show correct and incorrect usage>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 5. **Reference other files** - Use `@filename` syntax to include relevant file content>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 6. **Structure with headers** - Use clear section headings>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 7. **Code blocks with language** - Use proper syntax highlighting>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo ## Testing Rules>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo.>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo To verify a rule is applied correctly:>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 1. Open a file matching the glob pattern>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 2. Check that the rule appears in the Cursor context>> tmp_rules_rebuild\rule_creation_guide_full.txt
echo 3. Verify the rule guidance is followed by the AI assistant>> tmp_rules_rebuild\rule_creation_guide_full.txt

REM Create the frontmatter
echo ---> .cursor\rules\rule_creation_guide.mdc
echo type: always>> .cursor\rules\rule_creation_guide.mdc
echo title: Rule Creation Guidelines>> .cursor\rules\rule_creation_guide.mdc
echo description: Guidelines for creating and managing Cursor rules in the Bible Scholar project>> .cursor\rules\rule_creation_guide.mdc
echo globs:>> .cursor\rules\rule_creation_guide.mdc
echo   - "**/*.mdc">> .cursor\rules\rule_creation_guide.mdc
echo   - "scripts/cursor_rules/*.ps1">> .cursor\rules\rule_creation_guide.mdc
echo   - "scripts/cursor_rules/*.bat">> .cursor\rules\rule_creation_guide.mdc
echo alwaysApply: false>> .cursor\rules\rule_creation_guide.mdc
echo --->> .cursor\rules\rule_creation_guide.mdc
echo.>> .cursor\rules\rule_creation_guide.mdc

REM Append the content
type tmp_rules_rebuild\rule_creation_guide_full.txt >> .cursor\rules\rule_creation_guide.mdc

echo rule_creation_guide rule updated to be agent-friendly with alwaysApply: false 