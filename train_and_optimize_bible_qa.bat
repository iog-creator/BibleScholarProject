@echo off
REM Bible QA T5 Training and Optimization
REM Uses improved parameters to achieve much higher accuracy

echo.
echo ===================================================
echo Bible QA Advanced T5 Training and Optimization
echo ===================================================
echo.

REM Ensure required directories exist
mkdir "logs" 2>nul
mkdir "models\dspy\bible_qa_t5" 2>nul

REM Set environment variables
set PYTHONPATH=.
set PYTHONIOENCODING=utf-8

REM We're using Hugging Face regardless of LM Studio status
set USE_HUGGINGFACE=--use-huggingface

echo.
echo Starting advanced training with improved parameters...
echo Using Hugging Face API for more reliable results
echo.

REM Run the optimized training
python train_t5_bible_qa.py ^
  --lm "google/flan-t5-base" ^
  --optimizer "bootstrap" ^
  --augment-factor 2 ^
  --max-demos 5 ^
  --stratify-split ^
  --temperature 0.1 ^
  --track-with-mlflow ^
  %USE_HUGGINGFACE%

if %ERRORLEVEL% NEQ 0 (
  echo.
  echo WARNING: Training encountered errors. Trying with reduced parameters...
  echo.
  
  python train_t5_bible_qa.py ^
    --lm "google/flan-t5-small" ^
    --optimizer "none" ^
    --max-demos 3 ^
    --temperature 0.0 ^
    --track-with-mlflow ^
    --use-huggingface
)

echo.
echo Training complete! Evaluating model on test set...
echo.

REM Test the newly trained model with direct loading (more reliable test)
echo Running direct model test (to verify loading)...
python bible_qa_api.py --test-only --num-examples 5 --use-huggingface

echo.
echo ===================================================
echo Bible QA Training and Optimization Complete
echo ===================================================
echo. 