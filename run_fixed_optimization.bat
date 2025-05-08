@echo off
echo ===== Bible QA Optimization Workflow with BootstrapFewShot =====
echo.
echo This script runs the DSPy optimization workflow using BootstrapFewShot,
echo which is compatible with LM Studio (doesn't require fine-tuning).
echo.
echo For more information, see README_DSPY_LM_STUDIO.md
echo.

REM Parse command line arguments
set MAX_TRAIN=%1
set MAX_VAL=%2
set TARGET_ACCURACY=%3

REM Set defaults if not provided
if "%MAX_TRAIN%"=="" set MAX_TRAIN=20
if "%MAX_VAL%"=="" set MAX_VAL=5
if "%TARGET_ACCURACY%"=="" set TARGET_ACCURACY=0.95

echo Using:
echo   Optimization Method: bootstrap_few_shot (compatible with LM Studio)
echo   Max Training Examples: %MAX_TRAIN%
echo   Max Validation Examples: %MAX_VAL%
echo   Target Accuracy: %TARGET_ACCURACY%
echo.

REM Ensure the data directories exist
if not exist "data\processed\bible_training_data" (
    echo Creating data directory...
    mkdir "data\processed\bible_training_data"
)

REM Check if datasets exist, if not, copy from alternative location
if not exist "data\processed\bible_training_data\qa_dataset_train.jsonl" (
    echo Training dataset not found in primary location. Checking alternatives...
    
    if exist "data\processed\dspy_training_data\bible_corpus\integrated\qa_dataset_train.jsonl" (
        echo Found training dataset in alternative location. Copying...
        copy "data\processed\dspy_training_data\bible_corpus\integrated\qa_dataset_train.jsonl" "data\processed\bible_training_data\"
    ) else (
        echo ERROR: Could not find training dataset. Please generate it first.
        echo Use: python src\utils\generate_bible_training_data.py
        exit /b 1
    )
)

REM Run the optimization script
echo Starting optimization process...
python train_and_optimize_bible_qa.py --data-path "data\processed\bible_training_data" --max-train %MAX_TRAIN% --max-val %MAX_VAL% --target-accuracy %TARGET_ACCURACY% --use-bootstrap

REM Check if training was successful
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Training failed with error code %ERRORLEVEL%
    echo Check logs/train_and_optimize_bible_qa.log for details
    exit /b %ERRORLEVEL%
)

REM Test the optimized model
echo.
echo Testing optimized model...
python test_optimized_bible_qa.py --sample-only

REM Analyze the results
echo.
echo Analyzing optimization results...
python analyze_mlflow_results.py --limit 10 --visualize

echo.
echo Training and optimization complete! 
echo Results saved to models/dspy/bible_qa_optimized/bible_qa_bootstrap_few_shot.py
echo.
echo To test the model interactively, run:
echo   python test_optimized_bible_qa.py --conversation
echo. 