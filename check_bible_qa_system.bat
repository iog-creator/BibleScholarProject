@echo off
REM Bible QA System Check
REM Performs a comprehensive check of all Bible QA system components

echo.
echo ===================================================
echo Bible QA System Check
echo ===================================================
echo.

REM Set environment variables
set PYTHONPATH=.
set PYTHONIOENCODING=utf-8

echo Checking system components...
echo.

REM Check Python installation
echo 1. Checking Python installation...
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [FAIL] Python not found. Please install Python 3.8+.
) else (
  echo [PASS] Python is installed.
)

REM Check required packages
echo 2. Checking required packages...
python -c "import dspy, fastapi, uvicorn" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo [FAIL] Some required packages are missing.
  echo       Please run: pip install -r requirements.txt
) else (
  echo [PASS] Required packages are installed.
)

REM Check environment files
echo 3. Checking environment files...
if exist ".env.dspy" (
  echo [PASS] .env.dspy file found.
) else (
  echo [WARN] .env.dspy file not found. Copy .env.example.dspy to .env.dspy.
)

REM Check training data
echo 4. Checking training data...
if exist "data\processed\dspy_training_data\bible_corpus\dspy\combined_bible_corpus_dataset.json" (
  echo [PASS] Training data found.
) else (
  echo [WARN] Training data not found. Run data preparation scripts first.
)

REM Check model directories
echo 5. Checking model directories...
if exist "models\dspy\bible_qa_t5" (
  echo [PASS] Model directory structure exists.
) else (
  echo [WARN] Model directory not found. It will be created during training.
)

REM Check trained model
echo 6. Checking trained model...
if exist "models\dspy\bible_qa_t5\bible_qa_t5_latest" (
  echo [PASS] Trained model found.
) else (
  echo [WARN] Trained model not found. Run train_and_optimize_bible_qa.bat first.
)

REM Check web server (mock test)
echo 7. Testing web server startup...
>nul timeout /t 1 /nobreak
start "Bible QA Test" /b python bible_qa_api.py --test-web --port 5099 > nul 2>&1
>nul timeout /t 3 /nobreak
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:5099/health' -UseBasicParsing -TimeoutSec 2; exit 0 } catch { exit 1 }" > nul 2>&1
if %ERRORLEVEL% EQU 0 (
  echo [PASS] Web server starts successfully.
) else (
  echo [WARN] Web server test failed. Check for port conflicts or errors.
)
taskkill /FI "WINDOWTITLE eq Bible QA Test" /T /F > nul 2>&1

REM Check direct model testing
echo 8. Testing model operation...
python test_bible_qa.py --mock --num-examples 1 > test_output.txt 2>&1
findstr /C:"Testing complete" test_output.txt > nul
if %ERRORLEVEL% EQU 0 (
  echo [PASS] Model testing works correctly.
) else (
  echo [WARN] Model testing encountered issues. Check test_bible_qa.py.
)
del test_output.txt > nul 2>&1

echo.
echo ===================================================
echo System Check Complete
echo ===================================================
echo.
echo To start using the Bible QA system:
echo 1. Run train_and_optimize_bible_qa.bat (if model not found)
echo 2. Run start_bible_qa_web.bat
echo 3. Visit http://localhost:5005 in your browser
echo. 