@echo off
echo ===== Complete DSPy 2.6 Training and Testing Workflow =====
echo.
echo This script runs the complete workflow for training and testing
echo a Bible QA model using DSPy 2.6 with LM Studio integration.
echo.
echo Steps:
echo 1. Prepare training data
echo 2. Train and optimize the model
echo 3. Test the optimized model
echo.

REM Create logs directory
mkdir logs 2>nul
mkdir models\dspy\bible_qa_optimized 2>nul

REM Parse command line arguments
set MAX_TRAIN=%1
set MAX_VAL=%2

REM Set defaults if not provided
if "%MAX_TRAIN%"=="" set MAX_TRAIN=20
if "%MAX_VAL%"=="" set MAX_VAL=5

echo Using:
echo   Max Training Examples: %MAX_TRAIN%
echo   Max Validation Examples: %MAX_VAL%
echo.

REM Step 1: Prepare training data
echo Step 1: Preparing training data...
python prepare_training_data.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to prepare training data
    echo Check logs/prepare_training_data.log for details
    exit /b %ERRORLEVEL%
)

REM Step 2: Train and optimize model
echo.
echo Step 2: Training and optimizing model...
call run_fixed_optimization.bat %MAX_TRAIN% %MAX_VAL%
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to train model
    echo Check logs/train_and_optimize_bible_qa.log for details
    exit /b %ERRORLEVEL%
)

REM Step 3: Run interactive test
echo.
echo Step 3: Testing model interactively...
echo Starting interactive test - you can ask Bible questions
echo.
python test_optimized_bible_qa.py --conversation

echo.
echo ===== Complete DSPy 2.6 Workflow Finished =====
echo.
echo All steps completed successfully!
echo The optimized model is saved at:
echo   models/dspy/bible_qa_optimized/bible_qa_bootstrap_few_shot.py
echo.
echo To run the model again:
echo   python test_optimized_bible_qa.py --conversation
echo.
echo For MLflow results analysis:
echo   python analyze_mlflow_results.py --visualize
echo. 