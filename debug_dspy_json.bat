@echo off
echo ===== DSPy JSON Format Debug Tool =====

echo Checking if LM Studio is running...
powershell -Command "try { $null = Invoke-WebRequest -Uri 'http://127.0.0.1:1234/v1/models' -UseBasicParsing; Write-Host 'LM Studio API is running' } catch { Write-Host 'ERROR: LM Studio API is not running. Please start LM Studio and enable the API server.'; exit 1 }"
if %ERRORLEVEL% neq 0 (
    echo ERROR: LM Studio is not running or the API server is not enabled.
    echo Please start LM Studio, load a model, and enable the API server.
    exit /b 1
)

echo Creating logs directory...
mkdir logs 2>nul

echo Running JSON format debug tests...
python debug_json_format.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Debug tests failed!
    echo Please check the logs/debug_json_format.log file for details.
    exit /b 1
)

echo.
echo ===== Debug Tests Completed! =====
echo.
echo Check logs/debug_json_format.log for detailed results.
echo.
echo Common DSPy 2.6 JSON issues:
echo  - Using response_format parameter with LM Studio
echo  - Missing dspy.settings.experimental = True
echo  - Using modules parameter in BetterTogether constructor
echo.
echo Fix your code and re-run verify_dspy_model.bat to test again.
echo.
pause 