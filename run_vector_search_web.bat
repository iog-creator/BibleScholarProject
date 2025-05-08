@echo off
echo Starting Simplified Vector Search Web Application
echo =========================================
echo.

:: Check if pgvector is available in the database
echo Checking vector search functionality...
python -m src.utils.test_vector_search > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Vector search test had issues.
    echo The application will continue, but some functionality might not work.
    echo.
)

echo.
echo Starting simplified web application...
echo Access vector search at: http://localhost:5001/vector-search
echo Access similar verses at: http://localhost:5001/similar-verses
echo.
echo Press Ctrl+C to stop the application
echo.

:: Start the web application
python vector_search_web.py 