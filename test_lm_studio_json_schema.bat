@echo off
echo ===== Testing LM Studio JSON Schema Integration =====
echo.
echo This script will test whether LM Studio's JSON Schema capability
echo is correctly integrated with DSPy for structured output.
echo.
echo Make sure LM Studio is running with a model loaded!
echo.

REM Create directories
mkdir logs 2>nul

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

echo Starting JSON Schema integration test...
echo.

python test_lm_studio_json_schema.py
set TEST_RESULT=%ERRORLEVEL%

echo.
if %TEST_RESULT% EQU 0 (
    echo ===== TEST PASSED =====
    echo LM Studio JSON Schema integration is working correctly!
    echo.
    echo You can now use structured output in your DSPy applications by:
    echo 1. Importing dspy_json_patch after dspy
    echo 2. Using normal DSPy Signatures with multiple output fields
    echo 3. LM Studio will automatically enforce JSON structure
) else (
    echo ===== TEST FAILED =====
    echo There were issues with the JSON Schema integration.
    echo Check logs/test_lm_studio_json_schema.log for details.
)

echo.
echo For more information, see the following resources:
echo - docs/rules/dspy_lm_studio_integration.md
echo - https://lmstudio.ai/blog/lmstudio-v0.3.0 