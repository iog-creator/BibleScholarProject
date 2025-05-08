@echo off
echo Starting Bible Vector Search Web Application
echo =========================================
echo.

:: Check if environment variables are set
if not exist .env (
    echo ERROR: .env file not found.
    echo Please create a .env file with the required configuration.
    echo See README_VECTOR_SEARCH.md for details.
    exit /b 1
)

:: Check if secure connection is available
echo Checking secure database connection...
if not exist "%~dp0src\database\secure_connection.py" (
    echo WARNING: Secure database connection module not found.
    echo The application will use standard database connection.
    echo Run setup_db_security.bat to set up secure database access.
    echo.
)

:: Check if pgvector is available in the database
echo Checking vector search functionality...
python -m src.utils.test_vector_search > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Vector search test failed.
    echo Please ensure pgvector extension is installed and verse embeddings are available.
    echo See README_VECTOR_SEARCH.md for setup instructions.
    exit /b 1
)

echo.
echo Starting web application...
echo Access vector search at: http://localhost:5001/vector-search
echo Access similar verses at: http://localhost:5001/similar-verses
echo.
echo Press Ctrl+C to stop the application
echo.

:: Start the web application
python -m src.web_app 