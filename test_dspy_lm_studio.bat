@echo off
echo ===== DSPy 2.6 with LM Studio Integration Test =====
echo.
echo This script will test whether DSPy 2.6 is correctly integrated
echo with LM Studio following project standards.
echo.
echo Make sure LM Studio is running with a model loaded!
echo.

REM Create directories
mkdir logs 2>nul
mkdir models\dspy\test 2>nul

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Make sure Python is installed and in your PATH.
    exit /b 1
)

REM Check if DSPy is installed
python -c "import dspy" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: DSPy not found. Install it with: pip install dspy-ai
    exit /b 1
)

REM Check if required packages are installed
python -c "import requests, dotenv" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages...
    pip install python-dotenv requests
)

REM Check if .env.dspy exists
if not exist .env.dspy (
    echo Creating .env.dspy file with default settings...
    (
        echo LM_STUDIO_API_URL=http://localhost:1234/v1
        echo LM_STUDIO_CHAT_MODEL=mistral-nemo-instruct-2407
        echo LM_STUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0
    ) > .env.dspy
    echo Created .env.dspy with default settings.
    echo IMPORTANT: Edit .env.dspy to match your LM Studio configuration if needed.
    echo.
)

echo Starting test...
echo.

python test_dspy_lm_studio.py
set TEST_RESULT=%ERRORLEVEL%

echo.
if %TEST_RESULT% EQU 0 (
    echo ===== TEST PASSED =====
    echo DSPy 2.6 is correctly integrated with LM Studio!
    echo.
    echo To test model, run:
    echo   python test_optimized_bible_qa.py --conversation
) else (
    echo ===== TEST FAILED =====
    echo There were issues with the DSPy 2.6 integration.
    echo Check logs/test_dspy_lm_studio.log for details.
)

echo.
echo For more information, see docs/rules/dspy_lm_studio_integration.md 