@echo off
echo DSPy Bible QA Training Script
echo ===========================

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Install requirements
echo Checking and installing required packages...
pip install -r requirements-dspy.txt

REM Check if DSPy module is available
python -c "import dspy" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo DSPy module not found. Please install it:
    echo pip install dspy
    exit /b 1
)

REM Check if MLflow module is available
python -c "import mlflow" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo MLflow module not found. Please install it:
    echo pip install mlflow
    exit /b 1
)

REM Expand training data
echo Expanding training data...
python expand_dspy_training_data.py --examples 5000 --deduplicate --stratify

REM Start LM Studio if configured to use it
set LM_STUDIO_ENABLED=1
if %LM_STUDIO_ENABLED%==1 (
    echo Checking LM Studio...
    
    REM Check if LM Studio is running
    powershell -Command "Invoke-WebRequest -Uri 'http://localhost:1234/v1/models' -UseBasicParsing -TimeoutSec 2" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo LM Studio is not running. Please start it and ensure the server is enabled.
        echo - LM Studio should be running at: http://localhost:1234
        echo - Load the required models in LM Studio before continuing
        pause
    ) else (
        echo LM Studio is running and available.
    )
)

REM Get model choice
set /p MODEL_CHOICE="Choose model size (1=small, 2=base, 3=large) [1]: "
if "%MODEL_CHOICE%"=="" set MODEL_CHOICE=1

if %MODEL_CHOICE%==1 (
    set MODEL=google/flan-t5-small
) else if %MODEL_CHOICE%==2 (
    set MODEL=google/flan-t5-base
) else if %MODEL_CHOICE%==3 (
    set MODEL=google/flan-t5-large
) else (
    set MODEL=google/flan-t5-small
)

REM Get optimizer choice
set /p OPTIMIZER_CHOICE="Choose optimizer (1=bootstrap, 2=grpo, 3=simba) [1]: "
if "%OPTIMIZER_CHOICE%"=="" set OPTIMIZER_CHOICE=1

if %OPTIMIZER_CHOICE%==1 (
    set OPTIMIZER=bootstrap
) else if %OPTIMIZER_CHOICE%==2 (
    set OPTIMIZER=grpo
) else if %OPTIMIZER_CHOICE%==3 (
    set OPTIMIZER=simba
) else (
    set OPTIMIZER=bootstrap
)

echo.
echo Starting training with the following configuration:
echo - Model: %MODEL%
echo - Optimizer: %OPTIMIZER%
if %LM_STUDIO_ENABLED%==1 (
    echo - Using LM Studio for inference
    set LM_STUDIO_FLAG=--lm-studio
)
echo.

REM Run the training script
python train_dspy_bible_qa.py --model %MODEL% --optimizer %OPTIMIZER% --train-pct 0.8 --max-demos 8 %LM_STUDIO_FLAG%

if %ERRORLEVEL% NEQ 0 (
    echo Training failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Training complete! To view results in MLflow:
echo 1. Run: mlflow ui
echo 2. Open: http://localhost:5000
echo.

pause 