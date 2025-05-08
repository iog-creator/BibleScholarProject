@echo off
echo ===================================================
echo Vector Search Test for BibleScholarProject
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

echo.
echo Checking LM Studio API availability...
python -c "import os; import requests; from dotenv import load_dotenv; load_dotenv(); url=os.getenv('LM_STUDIO_API_URL', 'http://127.0.0.1:1234/v1'); print(f'Using API URL: {url}'); try: r=requests.get(f'{url}/models'); print(f'LM Studio API is running - Status: {r.status_code}'); except Exception as e: print(f'Error checking LM Studio API: {e}')"

echo.
echo Checking PostgreSQL pgvector extension...
python -c "import psycopg2; import os; from dotenv import load_dotenv; load_dotenv(); host=os.getenv('POSTGRES_HOST', 'localhost'); port=os.getenv('POSTGRES_PORT', '5432'); db=os.getenv('POSTGRES_DB', 'bible_db'); user=os.getenv('POSTGRES_USER', 'postgres'); pwd=os.getenv('POSTGRES_PASSWORD', 'postgres'); try: conn=psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pwd); cur=conn.cursor(); cur.execute('SELECT 1 FROM pg_extension WHERE extname = %s', ('vector',)); result=cur.fetchone(); print(f'pgvector extension is {\"installed\" if result else \"NOT installed\"}'); conn.close(); except Exception as e: print(f'Error connecting to PostgreSQL: {e}')"

echo.
echo Running vector search tests...
echo ---------------------------------------
python -m src.utils.test_vector_search > logs\vector_search_test.log 2>&1
type logs\vector_search_test.log

if %ERRORLEVEL% neq 0 (
    echo Error during vector search testing. Check logs for details.
    echo See logs\vector_search_test.log for detailed output.
    exit /b 1
)

echo.
echo Vector search testing completed!
echo See logs\vector_search_test.log for detailed output.
echo.
echo To use vector search APIs, the following endpoints are available:
echo - /api/vector-search - Semantic search for verses
echo - /api/similar-verses - Find verses similar to a reference verse
echo - /api/compare-translations - Compare different translations of a verse
echo - /api/available-translations - List available translations with embeddings

exit /b 0 