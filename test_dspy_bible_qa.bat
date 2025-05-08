@echo off
echo DSPy Bible QA Model Test
echo =======================

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Check if DSPy module is available
python -c "import dspy" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo DSPy module not found. Please install it:
    echo pip install dspy
    exit /b 1
)

REM Check if LM Studio is running
echo Checking LM Studio...
powershell -Command "Invoke-WebRequest -Uri 'http://localhost:1234/v1/models' -UseBasicParsing -TimeoutSec 2" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo LM Studio is not running. Please start it and ensure the server is enabled.
    echo - LM Studio should be running at: http://localhost:1234
    echo - Load the required models in LM Studio before continuing
    pause
    exit /b 1
) else (
    echo LM Studio is running and available.
)

REM Check model path input
echo.
echo Available models:
dir /b models\dspy\bible_qa_t5\
echo.

set /p MODEL_PATH="Enter model directory name (default: bible_qa_flan-t5-small_20250507_120648): "
if "%MODEL_PATH%"=="" set MODEL_PATH=bible_qa_flan-t5-small_20250507_120648

REM Run the test script
echo Running test with model %MODEL_PATH%...
python test_trained_bible_qa.py --model-path "models/dspy/bible_qa_t5/%MODEL_PATH%" --lm-studio

pause 