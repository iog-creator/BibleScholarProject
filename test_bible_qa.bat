@echo off
REM Bible QA Model Tester
REM Tests the Bible QA model with sample questions

echo.
echo ===================================================
echo Bible QA Model Tester
echo ===================================================
echo.

REM Set environment variables
set PYTHONPATH=.
set PYTHONIOENCODING=utf-8

REM Check if model exists
if not exist "models\dspy\bible_qa_t5\bible_qa_t5_latest" (
  echo WARNING: Bible QA model directory not found.
  echo Will run in mock mode for demonstration.
)

echo Testing Bible QA model with sample questions...
echo.

REM Run the test script - Use mock mode for demonstration
python test_bible_qa.py --mock

echo.
echo Testing complete! 