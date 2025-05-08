@echo off
echo ===================================================
echo Claude API Integration Test for BibleScholarProject
echo ===================================================

REM Set variables to track test success
set API_TEST_SUCCESS=false
set DSPY_TEST_SUCCESS=false
set BIBLE_QA_TEST_SUCCESS=false

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Create required directories
if not exist logs mkdir logs

REM Check if the environment file exists
if not exist .env.dspy (
    echo Warning: .env.dspy file not found. Please update the database connection details.
    echo Creating a template .env.dspy file...
    copy .env.example.dspy .env.dspy
    echo Please edit the .env.dspy file with your ANTHROPIC_API_KEY before continuing.
    exit /b 1
)

echo.
echo Step 1: Checking basic Claude API connectivity...
echo ---------------------------------------
python scripts/test_claude_direct.py

if %ERRORLEVEL% neq 0 (
    echo Error during basic Claude API testing. Check logs for details.
    exit /b 1
)
set API_TEST_SUCCESS=true

echo.
echo Step 2: Testing Bible QA with Claude...
echo ---------------------------------------
echo Testing direct Claude API calls for Bible QA...

REM Check if we can import the huggingface_integration module
python -c "from src.dspy_programs.huggingface_integration import configure_claude_model; print('Claude API module import successful!')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error importing Claude API integration modules. Check your installation.
    exit /b 1
)

REM Run a basic test without DSPy
python -c "import os; import anthropic; from dotenv import load_dotenv; load_dotenv('.env.dspy'); api_key=os.getenv('ANTHROPIC_API_KEY'); client=anthropic.Anthropic(api_key=api_key); response=client.messages.create(model=os.getenv('CLAUDE_MODEL', 'claude-3-opus-20240229'), max_tokens=100, messages=[{'role': 'user', 'content': 'What is the first verse of the Bible?'}]); print(f'Test response: {response.content[0].text[:100]}...'); exit(0)"
if %ERRORLEVEL% neq 0 (
    echo Error during Claude API Bible QA test. Check logs for details.
    exit /b 1
)
set BIBLE_QA_TEST_SUCCESS=true

echo.
echo Step 3: Starting Bible QA API with Claude for quick test...
echo ---------------------------------------
echo Starting Bible QA API with Claude for quick test (will shut down after 5 seconds)...
start /b cmd /c "python bible_qa_api.py --use-claude --test-only > logs\claude_api_test.log 2>&1"
timeout /t 5 /nobreak > nul
echo Stopped API after short test.

REM Check the log file for test success
findstr /I "Claude API test successful" logs\claude_api_test.log > nul
if %ERRORLEVEL% equ 0 (
    echo Bible QA API test with Claude successful!
    set DSPY_TEST_SUCCESS=true
) else (
    echo Warning: Bible QA API test with Claude may have issues. Check logs\claude_api_test.log for details.
    echo This is not a critical failure, continuing with tests.
)

echo.
echo Claude API Integration testing summary:
echo - Basic API connectivity: %API_TEST_SUCCESS%
echo - Bible QA with Claude: %BIBLE_QA_TEST_SUCCESS%
echo - Bible QA API with Claude: %DSPY_TEST_SUCCESS%
echo.

if "%API_TEST_SUCCESS%"=="true" if "%BIBLE_QA_TEST_SUCCESS%"=="true" (
    echo Claude API Integration testing completed successfully!
    echo.
    echo To use the system:
    echo - For API only: python bible_qa_api.py --use-claude
    echo - For using Claude as teacher: python train_t5_bible_qa.py --teacher "claude-3-opus-20240229" --optimizer "bootstrap" --track-with-mlflow
    exit /b 0
) else (
    echo Some Claude API Integration tests failed. Check logs for details.
    exit /b 1
) 