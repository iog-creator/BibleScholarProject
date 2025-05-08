@echo off
echo ===================================================
echo Verse Embeddings Generator for BibleScholarProject
echo ===================================================

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Create required directories
if not exist logs mkdir logs

REM Check if the environment file exists
if not exist .env (
    echo Warning: .env file not found. Please create an environment file.
    echo Creating a template .env file...
    copy .env.example .env
    echo Please edit the .env file before continuing.
    exit /b 1
)

REM Check if LM Studio is running (simplified check)
echo.
echo Checking LM Studio API availability...
python -c "import os; import requests; from dotenv import load_dotenv; load_dotenv(); url=os.getenv('LM_STUDIO_API_URL', 'http://127.0.0.1:1234/v1'); print(f'Using API URL: {url}'); try: r=requests.get(f'{url}/models'); print(f'LM Studio API is running - Status: {r.status_code}'); print('Available models:'); for m in r.json()['data']: print(f' - {m[\"id\"]}' if isinstance(m, dict) and 'id' in m else f' - {m}'); except Exception as e: print(f'Error checking LM Studio API: {e}')"

echo.
echo Checking PostgreSQL pgvector extension...
python -c "import psycopg2; import os; from dotenv import load_dotenv; load_dotenv(); host=os.getenv('POSTGRES_HOST', 'localhost'); port=os.getenv('POSTGRES_PORT', '5432'); db=os.getenv('POSTGRES_DB', 'bible_db'); user=os.getenv('POSTGRES_USER', 'postgres'); pwd=os.getenv('POSTGRES_PASSWORD', 'postgres'); try: conn=psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pwd); cur=conn.cursor(); cur.execute('SELECT 1 FROM pg_extension WHERE extname = %s', ('vector',)); result=cur.fetchone(); print(f'pgvector extension is {\"installed\" if result else \"NOT installed\"}'); conn.close(); except Exception as e: print(f'Error connecting to PostgreSQL: {e}')"

echo.
echo Starting verse embeddings generation...
echo ---------------------------------------

REM Parse command line arguments
set TRANSLATION=
set LIMIT=
set BATCH_SIZE=50

:parse_args
if "%~1"=="" goto run_script
if /i "%~1"=="--translation" (
    set TRANSLATION=%~2
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--limit" (
    set LIMIT=%~2
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--batch-size" (
    set BATCH_SIZE=%~2
    shift
    shift
    goto parse_args
)
shift
goto parse_args

:run_script
set CMD=python -m src.utils.generate_verse_embeddings
if not "%TRANSLATION%"=="" set CMD=%CMD% --translation %TRANSLATION%
if not "%LIMIT%"=="" set CMD=%CMD% --limit %LIMIT%
if not "%BATCH_SIZE%"=="" set CMD=%CMD% --batch_size %BATCH_SIZE%

echo Command: %CMD%
echo.
echo Running embedding generation, this may take a while...
%CMD% > logs\verse_embeddings.log 2>&1

if %ERRORLEVEL% neq 0 (
    echo Error during embedding generation. Check logs for details.
    echo See logs\verse_embeddings.log for detailed output.
    type logs\verse_embeddings.log
    exit /b 1
)

echo.
echo Embeddings generation completed successfully!
echo See logs\verse_embeddings.log for detailed output.
echo.
echo To test the vector search capabilities:
echo - Run: python -m src.utils.test_vector_search
echo - API endpoints are available at: /api/vector-search, /api/similar-verses, /api/compare-translations

exit /b 0 