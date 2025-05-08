@echo off
echo Bible QA DSPy Setup and Training
echo ===============================
echo.

REM Create required directories
if not exist logs mkdir logs
if not exist models mkdir models
if not exist models\dspy mkdir models\dspy
if not exist models\dspy\bible_qa_t5 mkdir models\dspy\bible_qa_t5
if not exist mlruns mkdir mlruns

REM Install requirements
echo [1/5] Installing required packages...
pip install -r requirements-dspy.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install requirements.
    pause
    exit /b 1
)

REM Check environment setup
echo [2/5] Checking environment setup...
python check_dspy_setup.py
if %ERRORLEVEL% NEQ 0 (
    echo Environment setup check failed.
    echo Please resolve the issues before continuing.
    echo You may still proceed at your own risk.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        exit /b 1
    )
)

REM Generate training data
echo [3/5] Generating/expanding training data...
python expand_dspy_training_data.py --examples 5000 --deduplicate --stratify
if %ERRORLEVEL% NEQ 0 (
    echo Failed to generate training data.
    pause
    exit /b 1
)

REM Check LM Studio
echo [4/5] Checking LM Studio...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:1234/v1/models' -UseBasicParsing -TimeoutSec 2 } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo LM Studio is not running or not accessible.
    echo Please start LM Studio and ensure:
    echo - The API server is enabled in Settings
    echo - A suitable model is loaded (Llama-3-8b-instruct or similar)
    echo - The server is running on http://localhost:1234
    echo.
    set /p START_TRAINING="Continue without LM Studio? (y/n): "
    if /i not "%START_TRAINING%"=="y" (
        exit /b 1
    )
    set LM_STUDIO_ENABLED=0
) else (
    echo LM Studio is running and accessible.
    set LM_STUDIO_ENABLED=1
)

REM Configure training parameters
echo [5/5] Configuring training parameters...

REM Select model size
echo Select model size:
echo 1. T5-small (80M parameters - fastest)
echo 2. T5-base (250M parameters - balanced)
echo 3. T5-large (800M parameters - best quality, slower)
set /p MODEL_CHOICE="Enter choice [1]: "
if "%MODEL_CHOICE%"=="" set MODEL_CHOICE=1

if %MODEL_CHOICE%==1 (
    set MODEL=google/flan-t5-small
    set MODEL_NAME=t5-small
) else if %MODEL_CHOICE%==2 (
    set MODEL=google/flan-t5-base
    set MODEL_NAME=t5-base
) else if %MODEL_CHOICE%==3 (
    set MODEL=google/flan-t5-large
    set MODEL_NAME=t5-large
) else (
    set MODEL=google/flan-t5-small
    set MODEL_NAME=t5-small
)

REM Select optimizer
echo.
echo Select optimizer:
echo 1. Bootstrap Few-Shot (fastest)
echo 2. GRPO (best quality, balanced speed)
echo 3. SIMBA (best for creative responses)
echo 4. MIPROv2 (thorough optimization, slowest)
set /p OPTIMIZER_CHOICE="Enter choice [2]: "
if "%OPTIMIZER_CHOICE%"=="" set OPTIMIZER_CHOICE=2

if %OPTIMIZER_CHOICE%==1 (
    set OPTIMIZER=bootstrap
) else if %OPTIMIZER_CHOICE%==2 (
    set OPTIMIZER=grpo
) else if %OPTIMIZER_CHOICE%==3 (
    set OPTIMIZER=simba
) else if %OPTIMIZER_CHOICE%==4 (
    set OPTIMIZER=miprov2
) else (
    set OPTIMIZER=grpo
)

REM Select number of demos
echo.
echo Select number of demos:
echo 1. Few demos (4) - fastest
echo 2. Medium demos (8) - balanced
echo 3. Many demos (16) - highest quality, slowest
set /p DEMOS_CHOICE="Enter choice [2]: "
if "%DEMOS_CHOICE%"=="" set DEMOS_CHOICE=2

if %DEMOS_CHOICE%==1 (
    set MAX_DEMOS=4
) else if %DEMOS_CHOICE%==2 (
    set MAX_DEMOS=8
) else if %DEMOS_CHOICE%==3 (
    set MAX_DEMOS=16
) else (
    set MAX_DEMOS=8
)

REM Set LM Studio flag if enabled
if %LM_STUDIO_ENABLED%==1 (
    set LM_STUDIO_FLAG=--lm-studio
) else (
    set LM_STUDIO_FLAG=
)

REM Show configuration summary
echo.
echo Training configuration:
echo - Model: %MODEL% (%MODEL_NAME%)
echo - Optimizer: %OPTIMIZER%
echo - Max demos: %MAX_DEMOS%
if %LM_STUDIO_ENABLED%==1 (
    echo - Using LM Studio for inference
) else (
    echo - Using direct model loading (slower)
)
echo.

REM Confirm and start training
set /p START_TRAINING="Start training with these settings? (y/n): "
if /i not "%START_TRAINING%"=="y" (
    echo Training cancelled.
    exit /b 0
)

echo.
echo Starting training...
python train_dspy_bible_qa.py --model %MODEL% --optimizer %OPTIMIZER% --max-demos %MAX_DEMOS% %LM_STUDIO_FLAG%

if %ERRORLEVEL% NEQ 0 (
    echo Training failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Training complete!
echo.
echo To view the results in MLflow UI:
echo 1. Run: mlflow ui
echo 2. Open: http://localhost:5000 in your browser
echo.
echo To use the trained model in your application:
echo - The model was saved to: models/dspy/bible_qa_t5
echo.

set /p VIEW_RESULTS="Would you like to start the MLflow UI now? (y/n): "
if /i "%VIEW_RESULTS%"=="y" (
    start "" mlflow ui
    echo Started MLflow UI. Open http://localhost:5000 in your browser.
)

pause 