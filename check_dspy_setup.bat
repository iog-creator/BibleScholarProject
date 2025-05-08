@echo off
echo DSPy and MLflow Setup Check
echo ==========================
echo.

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python not found. Please install Python 3.9+
    exit /b 1
)

REM Install required packages if needed
pip install -q requests python-dotenv

REM Run the setup check script
python check_dspy_setup.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Some issues were found with the DSPy setup.
    echo Please address them before proceeding with training.
) else (
    echo.
    echo DSPy setup validated successfully.
)

pause 