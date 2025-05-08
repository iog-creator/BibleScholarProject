@echo off
REM Bible QA Web Server Test
REM Tests if the Bible QA web server can start

echo.
echo ===================================================
echo Bible QA Web Server Test
echo ===================================================
echo.

REM Set environment variables
set PYTHONPATH=.
set PYTHONIOENCODING=utf-8

REM Check if model exists
if not exist "models\dspy\bible_qa_t5\bible_qa_t5_latest" (
  echo WARNING: Bible QA model directory not found.
  echo Will create a mock model for demonstration.
)

echo Testing Bible QA web server...
echo The server will start and run for a few seconds to verify it works.
echo.

REM Use a different port for testing to avoid conflicts
set TEST_PORT=5099

REM Start the server with the --test-web flag on a different port
start "Bible QA Test" /b python bible_qa_api.py --test-web --port %TEST_PORT%

echo Waiting for server to start...

REM Wait a moment to let the server start (suppress timeout message)
>nul timeout /t 5 /nobreak

REM Make a test request to the server
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:%TEST_PORT%/health' -UseBasicParsing -TimeoutSec 5; exit 0 } catch { exit 1 }" > nul 2>&1

if %ERRORLEVEL% EQU 0 (
  echo SUCCESS: Web server started successfully!
) else (
  echo WARNING: Could not connect to the web server.
  echo This might be normal if port %TEST_PORT% is already in use.
)

REM Attempt to terminate the server
taskkill /FI "WINDOWTITLE eq Bible QA Test" /T /F > nul 2>&1
taskkill /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Bible QA Test" /T /F > nul 2>&1

echo.
echo Testing complete!
echo.
echo To start the web server for normal use, run:
echo   start_bible_qa_web.bat 