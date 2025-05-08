@echo off
echo Bible Scholar Project - T5 Model Loader
echo =======================================
echo.
echo This script will check if the required T5 model is loaded in LM Studio
echo and attempt to load it if needed.
echo.
echo Make sure LM Studio is running before continuing!
echo.
pause

python bible_qa_api.py --load-t5

echo.
echo If the model failed to load automatically, please:
echo 1. Make sure LM Studio is running
echo 2. In LM Studio, go to Models tab
echo 3. Search for "gguf-flan-t5-small" and load it
echo 4. Restart your Bible QA application
echo.
pause 