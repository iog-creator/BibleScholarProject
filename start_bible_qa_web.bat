@echo off
REM Bible QA Web Interface Starter
REM Starts a web server to interact with the Bible Q&A model

echo.
echo ===================================================
echo Bible QA Web Interface
echo ===================================================
echo.

REM Set environment variables
set PYTHONPATH=.
set PYTHONIOENCODING=utf-8

REM Check if model exists
if not exist "models\dspy\bible_qa_t5\bible_qa_t5_latest" (
  echo ERROR: Bible QA model not found.
  echo Please run train_and_optimize_bible_qa.bat first to train a model.
  exit /b 1
)

echo Starting Bible QA Web Interface at http://localhost:5005
echo Press Ctrl+C to stop the server

REM Start the web server
uvicorn bible_qa_api:app --reload --host 0.0.0.0 --port 5005 