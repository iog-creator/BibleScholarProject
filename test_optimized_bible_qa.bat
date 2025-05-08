@echo off
echo ===== Testing Optimized Bible QA with DSPy 2.6 =====

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

REM Check if MLflow is already running on port 5000
echo Checking for MLflow server...
powershell -Command "$portInUse = $false; try { $connections = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue; if ($connections) { $portInUse = $true; Write-Host 'Found existing MLflow server on port 5000' } } catch { $portInUse = $false }; if (-not $portInUse) { Write-Host 'Starting new MLflow server...'; Start-Process -FilePath 'mlflow' -ArgumentList 'ui', '--host', '127.0.0.1', '--port', '5000' -WindowStyle Minimized }"

REM Wait for MLflow server to be ready
echo Waiting for MLflow server to be ready...
timeout /t 2 /nobreak > nul

REM Verify JSON patch is available
echo Checking for JSON patch implementation...
if not exist dspy_json_patch.py (
    echo ERROR: dspy_json_patch.py not found. This file is required to fix JSON responses from LM Studio.
    exit /b 1
)

REM Run the optimized Bible QA test
echo Running optimization test...
python test_optimized_bible_qa.py
if %ERRORLEVEL% neq 0 (
    echo ERROR: Optimization test failed with exit code %ERRORLEVEL%.
    echo Please check the logs for details.
    exit /b 1
)

echo.
echo ===== Test Completed Successfully! =====
echo.
echo MLflow UI is available at: http://127.0.0.1:5000
echo Note: The MLflow server is still running on port 5000. 