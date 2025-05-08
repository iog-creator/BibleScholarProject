@echo off
echo ===== Bible QA Optimization with MLflow and DSPy 2.6 =====
echo.
echo This script runs the DSPy optimization workflow with MLflow tracking.
echo It will check if MLflow server is running and fallback to local tracking if needed.
echo.

REM Parse command line arguments
set VISUALIZE=false
set MAX_TRAIN=10
set MAX_VAL=5
set USE_BOOTSTRAP=true
set NO_MLFLOW_SERVER=false

:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="--visualize" (
    set VISUALIZE=true
    shift
    goto parse_args
)
if "%~1"=="--max-train" (
    set MAX_TRAIN=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--max-val" (
    set MAX_VAL=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--use-better-together" (
    set USE_BOOTSTRAP=false
    shift
    goto parse_args
)
if "%~1"=="--no-mlflow-server" (
    set NO_MLFLOW_SERVER=true
    shift
    goto parse_args
)
shift
goto parse_args
:end_parse

echo Settings:
echo   Max Training Examples: %MAX_TRAIN%
echo   Max Validation Examples: %MAX_VAL%
echo   Optimizer: %USE_BOOTSTRAP% 
echo   Visualize: %VISUALIZE%
echo   No MLflow Server: %NO_MLFLOW_SERVER%
echo.

REM Check if MLflow server is running if not explicitly disabled
if "%NO_MLFLOW_SERVER%"=="false" (
    echo Checking if MLflow server is running...
    powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5000' -UseBasicParsing -TimeoutSec 2; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
    
    if %ERRORLEVEL% EQU 0 (
        echo MLflow server is running at http://localhost:5000
    ) else (
        echo MLflow server is not running. You can:
        echo   1. Start MLflow server with 'mlflow ui --port 5000' in another terminal
        echo   2. Continue with local tracking (results will be saved in ./mlruns)
        echo   3. Run with --no-mlflow-server to skip this check in the future
        
        choice /C YN /M "Continue with local tracking"
        if %ERRORLEVEL% EQU 2 (
            echo Exiting. Please start MLflow server first and try again.
            exit /b 1
        )
        set NO_MLFLOW_SERVER=true
    )
)

REM Ensure required directories exist
if not exist "logs" mkdir logs

REM Prepare arguments for optimization script
set ARGS=--max-train %MAX_TRAIN% --max-val %MAX_VAL%

if "%USE_BOOTSTRAP%"=="true" (
    set ARGS=%ARGS% --use-bootstrap
)
if "%NO_MLFLOW_SERVER%"=="true" (
    set ARGS=%ARGS% --no-mlflow-server
)

REM Run optimization script
echo Starting optimization with MLflow tracking...
python train_and_optimize_bible_qa.py %ARGS%

REM Check if training was successful
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Training failed with error code %ERRORLEVEL%
    echo Check logs/train_and_optimize_bible_qa.log for details
    exit /b %ERRORLEVEL%
)

REM Run analysis if requested
if "%VISUALIZE%"=="true" (
    echo.
    echo Analyzing results with visualization...
    python analyze_mlflow_results.py --visualize --limit 10
) else (
    echo.
    echo Analyzing optimization results...
    python analyze_mlflow_results.py --limit 10
)

echo.
echo Optimization complete! 
echo.
echo To test the optimized model interactively, run:
echo   python test_optimized_bible_qa.py --conversation
echo.
echo To view optimization metrics in MLflow UI, run:
echo   mlflow ui --port 5000 