@echo off
echo ===================================================
echo Claude API Configuration Check for BibleScholarProject
echo ===================================================

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Check if the environment file exists
if not exist .env.dspy (
    echo Warning: .env.dspy file not found. Please set up your environment file.
    echo You can copy the template file with: copy .env.example.dspy .env.dspy
    exit /b 1
)

echo.
echo Step 1: Checking if Anthropic package is installed...
python -c "import anthropic; print(f'Anthropic package version: {anthropic.__version__}')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo Anthropic package is not installed!
    echo Please install it with: pip install anthropic>=0.21.0
    exit /b 1
) else (
    echo Anthropic package is installed.
)

echo.
echo Step 2: Checking for ANTHROPIC_API_KEY in environment...
python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.dspy'); key=os.getenv('ANTHROPIC_API_KEY'); print(f'API key {\"is set\" if key else \"is NOT set\"}'); has_valid_key = key and len(key)>20; print(f'API key status: {\"Valid format\" if has_valid_key else \"Invalid format\"}'); exit(0 if has_valid_key else 1)"
if %ERRORLEVEL% neq 0 (
    echo API key validation failed! Please check your .env.dspy file.
    exit /b 1
)

echo.
echo Step 3: Checking Claude model configuration...
python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.dspy'); model=os.getenv('CLAUDE_MODEL', 'Not set'); print(f'Current model: {model}'); valid_models=['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307', 'claude-2.1', 'claude-2.0']; is_valid = model in valid_models; print(f'Model status: {\"Valid\" if is_valid else \"Unknown/Not recommended\"}'); exit(0 if is_valid else 1)"
if %ERRORLEVEL% neq 0 (
    echo WARNING: Configured Claude model may not be valid or optimal.
    echo This is not a failure, but you may want to check your configuration.
)

echo.
echo Step 4: Testing simple API call...
python scripts/test_claude_direct.py
if %ERRORLEVEL% neq 0 (
    echo API test failed. Check logs for details.
    exit /b 1
)

echo.
echo Claude API configuration check completed successfully!
echo.
echo For detailed Claude API setup instructions, see:
echo docs/guides/claude_api_setup.md
echo.
echo To test the full Claude API integration:
echo python scripts/test_claude_integration.py
echo.

exit /b 0 