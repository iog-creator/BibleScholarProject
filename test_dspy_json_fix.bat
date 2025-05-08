@echo off
echo ===== Testing DSPy JSON Patch with LM Studio =====

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
echo Checking for JSON patch file...
if not exist dspy_json_patch.py (
    echo ERROR: dspy_json_patch.py not found. This file is required to fix JSON responses from LM Studio.
    exit /b 1
)

REM Run the JSON patch test
echo Running JSON patch test...
python test_dspy_json_fix.py
if %ERRORLEVEL% neq 0 (
    echo ERROR: DSPy JSON patch test failed.
    echo Please check logs/test_dspy_json_fix.log for details.
    exit /b 1
)

echo.
echo ===== DSPy JSON Patch Test Successful! =====
echo.
echo The DSPy JSON patch is working correctly with LM Studio.
echo You can proceed with the optimization process. 