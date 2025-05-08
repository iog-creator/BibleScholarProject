@echo off
echo ===== Bible QA DSPy Optimization Pipeline =====

REM Get optimization method
set optimization_method=better_together
if not "%1"=="" (
    set optimization_method=%1
)

echo Starting MLflow server for tracking...
start "MLflow Server" cmd /c "mlflow ui --host 127.0.0.1 --port 5000"
echo Waiting for MLflow server to start...
timeout /t 5

echo Running Bible QA optimization with method: %optimization_method%
python train_and_optimize_bible_qa.py --max-iterations 10 --target-accuracy 0.95 --optimization-method %optimization_method%

echo ===== Optimization Complete =====
echo View results at http://127.0.0.1:5000
echo.
echo Press any key to exit...
pause > nul 