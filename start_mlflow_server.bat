@echo off
echo ===== Starting MLflow Server =====
echo.
echo This will start MLflow server on port 5000.
echo Access the UI at http://localhost:5000
echo Press Ctrl+C to stop the server.
echo.

REM Parse command line arguments
set PORT=5000
set BACKEND=file

:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="--port" (
    set PORT=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--backend-store-uri" (
    set BACKEND=%~2
    shift
    shift
    goto parse_args
)
shift
goto parse_args
:end_parse

echo Starting MLflow server on port %PORT%...
echo.

REM Check if backend is a database connection string
echo %BACKEND% | findstr /C:"postgresql://" > nul
if %ERRORLEVEL% EQU 0 (
    echo Using PostgreSQL database backend: %BACKEND%
    mlflow server --port %PORT% --backend-store-uri %BACKEND% --default-artifact-root ./mlruns
) else (
    echo Using local file storage backend
    mlflow server --port %PORT% --backend-store-uri ./mlruns
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error starting MLflow server. Make sure MLflow is installed:
    echo   pip install mlflow
    exit /b 1
)

echo.
echo MLflow server stopped. 