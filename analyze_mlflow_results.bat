@echo off
echo ===== Bible QA DSPy MLflow Analysis =====

REM Check if MLflow server is running
powershell -Command "try { $null = Invoke-WebRequest -Uri 'http://127.0.0.1:5000' -UseBasicParsing; Write-Host 'MLflow server is running' } catch { Write-Host 'WARNING: MLflow server is not running. Starting it now...'; Start-Process -FilePath 'cmd' -ArgumentList '/c mlflow ui --host 127.0.0.1 --port 5000' -WindowStyle Minimized }"
echo.

REM Get experiment name
set experiment_name=bible_qa_optimization
set output_dir=analysis_results
set compare_methods=
set top_n=5

echo Running MLflow analysis...
python -m scripts.analyze_mlflow_results --experiment-name %experiment_name% --output-dir %output_dir% --top-n %top_n% --compare-methods

echo ===== Analysis Complete =====
echo Results saved to %output_dir% directory
echo.

REM Open the results folder
explorer %output_dir%

echo Press any key to exit...
pause > nul 