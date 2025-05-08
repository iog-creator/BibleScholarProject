@echo off
echo ===================================================
echo DSPy Llama-3.3 Integration Test for BibleScholarProject
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
    echo Warning: .env.dspy file not found. Please update the environment file.
    echo Creating a template .env.dspy file...
    copy .env.example.dspy .env.dspy
    echo Please edit the .env.dspy file with your HUGGINGFACE_API_KEY before continuing.
    exit /b 1
)

echo.
echo Checking HuggingFace API key...
python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.dspy'); key=os.getenv('HUGGINGFACE_API_KEY'); print(f'API key {\"is set\" if key else \"is NOT set\"}'); has_valid_key = key and key.startswith('hf_') and len(key)>10; print(f'API key status: {\"Valid format\" if has_valid_key else \"Invalid format\"}');"

echo.
echo Testing DSPy integration with Llama-3.3-70B-Instruct...
echo ---------------------------------------
python scripts/test_dspy_llama.py > logs\dspy_llama_test.log 2>&1
type logs\dspy_llama_test.log

if %ERRORLEVEL% neq 0 (
    echo Error during DSPy Llama integration testing. Check logs for details.
    echo See logs\dspy_llama_test.log for detailed output.
    exit /b 1
)

echo.
echo DSPy Llama-3.3 integration testing completed successfully!
echo See logs\dspy_llama_test.log for detailed output.
echo.
echo To use Llama-3.3 models with DSPy:
echo - For Bible QA: python bible_qa_api.py --use-huggingface --model "meta-llama/Llama-3.3-70B-Instruct"
echo - For training: python train_t5_bible_qa.py --teacher "meta-llama/Llama-3.3-70B-Instruct" --optimizer "bootstrap"

exit /b 0 