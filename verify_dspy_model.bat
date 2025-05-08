@echo off
echo ===== Verifying DSPy Model with LM Studio =====

REM Create logs directory
mkdir logs 2>nul

REM Check if LM Studio is running
echo Checking if LM Studio API is running...
powershell -Command "try { $null = Invoke-WebRequest -Uri 'http://127.0.0.1:1234/v1/models' -UseBasicParsing -TimeoutSec 2; Write-Host 'LM Studio API is running.' } catch { Write-Host 'ERROR: LM Studio API is not running or not enabled.'; exit 1 }"
if %ERRORLEVEL% neq 0 (
    echo ERROR: LM Studio is not running or the API server is not enabled.
    echo Please start LM Studio, load a model, and enable the API server.
    exit /b 1
)

REM Verify JSON patch is available
echo Checking for JSON patch implementation...
if not exist dspy_json_patch.py (
    echo ERROR: dspy_json_patch.py not found. This file is required to fix JSON responses from LM Studio.
    exit /b 1
)

REM Run the test script
echo Running DSPy model verification...
python verify_dspy_model.py
if %ERRORLEVEL% neq 0 (
    echo ERROR: DSPy model verification failed.
    echo Check logs/verify_dspy_model.log for details.
    exit /b 1
)

exit /b 0 