@echo off
echo Setting up Bible Database Security
echo ================================
echo.
echo This script will set up secure database access with read-only and write modes.
echo This helps prevent accidental data modification or deletion of the Bible database.
echo.
echo Requirements:
echo  - PostgreSQL admin credentials
echo  - Existing .env file in project root
echo.
echo Press Ctrl+C to cancel or any key to continue...
pause > nul

:: Run the setup script
python scripts/setup_db_security.py

:: Check if setup was successful
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Database security setup failed.
    echo Please check the error messages above.
    exit /b 1
)

echo.
echo Testing the secure database connection...
python scripts/test_db_security.py

echo.
echo Setup complete. Your Bible database is now protected!
echo.
echo To use in your code:
echo from src.database.secure_connection import get_secure_connection
echo.
echo # For read-only access (default, safe)
echo conn = get_secure_connection()
echo.
echo # For write access (requires password)
echo conn = get_secure_connection(mode='write')
echo.
pause 