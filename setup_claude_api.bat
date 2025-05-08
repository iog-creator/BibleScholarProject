@echo off
echo ===================================================
echo Claude API Setup for BibleScholarProject
echo ===================================================

REM Check for interactive mode
set INTERACTIVE=false
if "%1"=="-i" set INTERACTIVE=true
if "%1"=="--interactive" set INTERACTIVE=true

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Ensure Anthropic package is installed
echo Installing Anthropic package...
pip install anthropic>=0.21.0
if %ERRORLEVEL% neq 0 (
    echo Failed to install Anthropic package
    exit /b 1
)

REM Create required directories
if not exist logs mkdir logs

REM Check if the environment file exists
if not exist .env.dspy (
    echo Creating .env.dspy file from template...
    copy .env.example.dspy .env.dspy
    if %ERRORLEVEL% neq 0 (
        echo Failed to create .env.dspy file from template
        exit /b 1
    )
)

REM Handle API key input
set ANTHROPIC_API_KEY=
if "%INTERACTIVE%"=="true" (
    echo.
    echo Please enter your Anthropic API key:
    set /p ANTHROPIC_API_KEY=API Key: 
) else (
    REM Check if API key is provided as argument
    if not "%2"=="" (
        set ANTHROPIC_API_KEY=%2
    ) else (
        echo.
        echo No API key provided. Please run with API key as second parameter:
        echo setup_claude_api.bat [--interactive] YOUR_API_KEY
        echo.
        echo Example: setup_claude_api.bat sk-ant-api03-xxxxxxxxxxxx
        echo Or use interactive mode: setup_claude_api.bat --interactive
        exit /b 1
    )
)

REM Validate API key format
if "%ANTHROPIC_API_KEY%"=="" (
    echo API key is required
    exit /b 1
)
echo %ANTHROPIC_API_KEY% | findstr /r "^sk-ant-api[0-9][0-9]-" >nul
if %ERRORLEVEL% neq 0 (
    echo Warning: API key format does not match expected pattern for Claude API keys
    echo This may be a valid API key using a different format, continuing setup...
)

REM Handle model selection
set CLAUDE_MODEL=claude-3-opus-20240229
if "%INTERACTIVE%"=="true" (
    echo.
    echo Select Claude model:
    echo 1. claude-3-opus-20240229 (highest quality, most capabilities)
    echo 2. claude-3-sonnet-20240229 (balanced quality and speed)
    echo 3. claude-3-haiku-20240307 (fastest, least expensive)
    echo 4. claude-2.1 (legacy)
    echo.
    set /p MODEL_CHOICE=Enter choice (1-4): 
    
    if "%MODEL_CHOICE%"=="2" set CLAUDE_MODEL=claude-3-sonnet-20240229
    if "%MODEL_CHOICE%"=="3" set CLAUDE_MODEL=claude-3-haiku-20240307
    if "%MODEL_CHOICE%"=="4" set CLAUDE_MODEL=claude-2.1
) else (
    REM Check if model is provided as third argument
    if not "%3"=="" (
        set CLAUDE_MODEL=%3
    )
)

REM Update the .env.dspy file with the API key and model
python -c "import os; from dotenv import load_dotenv, set_key; env_file='.env.dspy'; load_dotenv(env_file); set_key(env_file, 'ANTHROPIC_API_KEY', os.environ.get('ANTHROPIC_API_KEY') or '%ANTHROPIC_API_KEY%'); set_key(env_file, 'CLAUDE_MODEL', os.environ.get('CLAUDE_MODEL') or '%CLAUDE_MODEL%'); print('Environment file updated successfully!')"
if %ERRORLEVEL% neq 0 (
    echo Failed to update .env.dspy file
    exit /b 1
)

echo.
echo Claude API setup complete!
echo.
echo Testing Claude API connection...
python scripts/test_claude_direct.py
if %ERRORLEVEL% neq 0 (
    echo API test failed. Please check your API key and try again.
    exit /b 1
)

echo.
echo For more information on Claude API integration, see:
echo docs/guides/claude_api_setup.md
echo.
echo To start the Bible QA system with Claude:
echo python bible_qa_api.py --use-claude
echo.

exit /b 0 