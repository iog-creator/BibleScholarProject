@echo off
echo ===================================================
echo Bible T5 Model Training and Testing Pipeline
echo ===================================================

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Create required directories
if not exist logs mkdir logs
if not exist models\dspy\bible_qa_t5 mkdir models\dspy\bible_qa_t5

REM Check if the environment file exists
if not exist .env.dspy (
    echo Warning: .env.dspy file not found. Please update the database connection details.
    echo Creating a template .env.dspy file...
    copy .env.example.dspy .env.dspy
    echo Please edit the .env.dspy file with your credentials before continuing.
    pause
    exit /b 1
)

echo.
echo Step 1: Training the T5 Bible QA model...
echo ---------------------------------------
python train_t5_bible_qa.py --lm "google/flan-t5-small" --teacher "gpt-3.5-turbo" --optimizer "dsp" --track-with-mlflow

if %ERRORLEVEL% neq 0 (
    echo Error during training. Check logs/t5_train.log for details.
    pause
    exit /b 1
)

echo.
echo Step 2: Finding the latest trained model...
echo ---------------------------------------
for /f "tokens=*" %%a in ('dir /b /od models\dspy\bible_qa_t5\bible_qa_t5_*') do set LATEST_MODEL=%%a
echo Latest model: %LATEST_MODEL%

echo.
echo Step 3: Testing the model...
echo ---------------------------------------
python test_bible_t5_model.py --model-path "models/dspy/bible_qa_t5/%LATEST_MODEL%" --interactive

echo.
echo Pipeline completed successfully!
echo.
echo For non-interactive testing, use:
echo python test_bible_t5_model.py --model-path "models/dspy/bible_qa_t5/%LATEST_MODEL%" --question "Your question here" --verse-ref "John 3:16"
echo.

pause 