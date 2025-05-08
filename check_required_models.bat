@echo off
echo Bible Scholar Project - Required Models Check
echo ============================================
echo.
echo This script will check if all required models are loaded in LM Studio.
echo.
echo Make sure LM Studio is running before continuing!
echo.
pause

echo Running model check...
echo.
python bible_qa_api.py --test-models

echo.
echo If any models failed to load automatically, please:
echo 1. Make sure LM Studio is running
echo 2. In LM Studio, go to Models tab
echo 3. Search for the missing model(s) and load them
echo 4. Restart your Bible QA application
echo.
echo Required models:
echo - Chat model: darkidol-llama-3.1-8b-instruct-1.2-uncensored (or similar LLaMa model)
echo - Embedding model: text-embedding-nomic-embed-text-v1.5@q8_0
echo - T5 model: gguf-flan-t5-small
echo.
pause 