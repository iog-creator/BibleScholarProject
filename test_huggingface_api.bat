@echo off
echo ===================================================
echo HuggingFace API Integration Test for BibleScholarProject
echo ===================================================

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
    echo Please edit the .env.dspy file with your HUGGINGFACE_API_KEY before continuing.
    exit /b 1
)

echo.
echo Step 1: Checking basic HuggingFace API connectivity...
echo ---------------------------------------
python scripts/test_huggingface_api.py

if %ERRORLEVEL% neq 0 (
    echo Error during HuggingFace API testing. Check logs for details.
    exit /b 1
)

echo.
echo HuggingFace API Integration testing completed!
echo.
echo To use HuggingFace models for training:
echo - For API only: python bible_qa_api.py --use-huggingface
echo - For using HuggingFace as teacher: python train_t5_bible_qa.py --teacher "meta-llama/Llama-3-70b-instruct" --optimizer "bootstrap" --track-with-mlflow 