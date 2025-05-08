@echo off
echo ------------------------------------------------------
echo    Training DSPy Models for Semantic Search
echo ------------------------------------------------------

REM Check if .env.dspy exists, create if not
if not exist .env.dspy (
    echo Creating .env.dspy file...
    echo # Database connection > .env.dspy
    echo POSTGRES_HOST=localhost >> .env.dspy
    echo POSTGRES_PORT=5432 >> .env.dspy
    echo POSTGRES_DB=bible_db >> .env.dspy
    echo POSTGRES_USER=postgres >> .env.dspy
    echo POSTGRES_PASSWORD=postgres >> .env.dspy
    echo. >> .env.dspy
    echo # LM Studio API >> .env.dspy
    echo LM_STUDIO_API_URL=http://127.0.0.1:1234/v1 >> .env.dspy
    echo LM_STUDIO_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5@q8_0 >> .env.dspy
    echo LM_STUDIO_CHAT_MODEL=gguf-flan-t5-small >> .env.dspy
)

REM Check if LM Studio is running
echo Checking if LM Studio is running...
powershell -Command "Invoke-WebRequest -Uri 'http://127.0.0.1:1234/v1/models' -UseBasicParsing -Method GET -ErrorAction SilentlyContinue" > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: LM Studio API is not available at http://127.0.0.1:1234/v1
    echo Please start LM Studio and load a model before continuing.
    echo.
    echo Recommended models:
    echo - gguf-flan-t5-small
    echo - gguf-t5-small
    echo - other T5 models
    echo.
    echo After loading the model, press any key to continue...
    pause > nul
)

REM Ensure model directory exists
if not exist models\dspy\semantic_search (
    mkdir models\dspy\semantic_search
)

REM Train the models
echo.
echo Starting training process...
echo This may take several minutes depending on your hardware.
echo.

python -m src.dspy_programs.train_semantic_search --use-local-teacher --teacher-model gguf-flan-t5-small

echo.
if %ERRORLEVEL% neq 0 (
    echo Training failed with error code %ERRORLEVEL%.
    echo Please check the logs for more information.
) else (
    echo Training completed successfully!
    echo.
    echo Testing the models...
    python -m src.dspy_programs.load_semantic_search_models
    echo.
    echo You can now use the trained models with the semantic search API.
    echo Try running: python -m src.utils.dspy_search_demo
) 