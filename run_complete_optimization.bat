@echo off
echo ===== Complete Bible QA Optimization Workflow =====

REM Parse command line arguments
set OPTIMIZATION_METHOD=%1
set MAX_ITERATIONS=%2
set TARGET_ACCURACY=%3

REM Set defaults if not provided
if "%OPTIMIZATION_METHOD%"=="" set OPTIMIZATION_METHOD=better_together
if "%MAX_ITERATIONS%"=="" set MAX_ITERATIONS=5
if "%TARGET_ACCURACY%"=="" set TARGET_ACCURACY=0.95

echo Using:
echo   Optimization Method: %OPTIMIZATION_METHOD%
echo   Max Iterations: %MAX_ITERATIONS%
echo   Target Accuracy: %TARGET_ACCURACY%
echo.

REM Create directories
mkdir logs 2>nul
mkdir analysis_results 2>nul
mkdir models\dspy\bible_qa_optimized 2>nul

REM Step 1: Verify JSON patch works
echo Step 1: Verifying DSPy JSON patch...
call test_dspy_json_fix.bat
if %ERRORLEVEL% neq 0 (
    echo Error: DSPy JSON patch verification failed
    exit /b 1
)

REM Step 2: Verify DSPy Model
echo Step 2: Verifying DSPy model...
call verify_dspy_model.bat
if %ERRORLEVEL% neq 0 (
    echo Error: DSPy model verification failed
    exit /b 1
)

REM Step 3: Expand Validation Dataset
echo Step 3: Expanding validation dataset...
python expand_validation_dataset.py --sample-theological
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to expand validation dataset
    exit /b 1
)

REM Step 4: Start MLflow server - Fixed for PowerShell compatibility
echo Step 4: Starting MLflow tracking server...
powershell -Command "$portInUse = $false; try { $connections = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue; if ($connections) { $portInUse = $true; Write-Host 'Found existing MLflow server on port 5000' } } catch { $portInUse = $false }; if (-not $portInUse) { Write-Host 'Starting new MLflow server...'; Start-Process -FilePath 'mlflow' -ArgumentList 'ui', '--host', '127.0.0.1', '--port', '5000' -WindowStyle Minimized }"

REM Wait a moment for MLflow to be ready
echo Waiting for MLflow server to be ready...
timeout /t 3 /nobreak > nul

REM Step 5: Run Optimization
echo Step 5: Running optimization...
python train_and_optimize_bible_qa.py --optimization-method %OPTIMIZATION_METHOD% --max-iterations %MAX_ITERATIONS% --target-accuracy %TARGET_ACCURACY%
if %ERRORLEVEL% neq 0 (
    echo Warning: Optimization script returned non-zero exit code: %ERRORLEVEL%
    echo This may be due to failing to reach target accuracy, but results could still be useful.
)

REM Step 6: Test the optimized model
echo Step 6: Testing optimized model...
python test_optimized_bible_qa.py
if %ERRORLEVEL% neq 0 (
    echo Warning: Optimized model test returned non-zero exit code: %ERRORLEVEL%
)

REM Step 7: Analyze Results
echo Step 7: Analyzing optimization results...
python -m scripts.analyze_mlflow_results --experiment-name bible_qa_optimization
if %ERRORLEVEL% neq 0 (
    echo Warning: Analysis script returned non-zero exit code: %ERRORLEVEL%
)

echo.
echo ===== Complete Optimization Workflow Finished =====
echo Results saved to analysis_results directory
echo MLflow UI is available at http://127.0.0.1:5000 