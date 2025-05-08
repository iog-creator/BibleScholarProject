@echo off
echo ===================================
echo DSPy 2.6 Bible QA Training Script
echo ===================================
echo.

:: Check if the required directories exist
if not exist logs mkdir logs
if not exist models\dspy mkdir models\dspy
if not exist data\processed\dspy_training_data\bible_corpus\dspy mkdir data\processed\dspy_training_data\bible_corpus\dspy

:: Check DSPy version
echo Checking DSPy version...
python -c "import dspy; print(f'DSPy version: {dspy.__version__}')"
echo.

:: Set up environment options
set TEACHER_MODEL=high
set STUDENT_MODEL=google/flan-t5-small
set OPTIMIZER=grpo

:: Parse command line arguments
if "%1"=="--teacher" set TEACHER_MODEL=%2
if "%1"=="--student" set STUDENT_MODEL=%2
if "%1"=="--optimizer" set OPTIMIZER=%2

echo Starting DSPy 2.6 Bible QA training...
echo Teacher model category: %TEACHER_MODEL%
echo Student model: %STUDENT_MODEL%
echo Optimizer: %OPTIMIZER%
echo.

:: Start MLflow UI (if not already running)
echo Starting MLflow UI (if not already running)
start "MLflow UI" /min cmd /c "mlflow ui --port 5000"
echo MLflow UI available at http://localhost:5000
echo.

:: Train the model
echo Training model...
python -m src.dspy_programs.bible_qa_dspy26 --teacher-category %TEACHER_MODEL% --student-model %STUDENT_MODEL% --optimizer %OPTIMIZER%

if %ERRORLEVEL% neq 0 (
    echo Error: Training failed
    exit /b %ERRORLEVEL%
)

echo.
echo Training completed successfully!
echo.

:: Run tests on the trained model
echo Running tests...
python test_bible_qa_dspy26.py --model-path models/dspy/bible_qa_t5_latest

echo.
echo ==============================================
echo To start interactive conversation mode, run:
echo python test_bible_qa_dspy26.py --conversation
echo ============================================== 