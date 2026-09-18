@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0.."
set "LOOPS=%LOOPS%"
if "%LOOPS%"=="" set "LOOPS=10"
set "RAMP_UP=%RAMP_UP%"
if "%RAMP_UP%"=="" set "RAMP_UP=5"
set "HOST=%HOST%"
if "%HOST%"=="" set "HOST=127.0.0.1"
set "PORT=%PORT%"
if "%PORT%"=="" set "PORT=8088"
set "JMETER_CMD=%JMETER_CMD%"
if "%JMETER_CMD%"=="" set "JMETER_CMD=jmeter"
if not exist "results\ladder" mkdir "results\ladder"
echo AI API Performance Lab - Concurrency Ladder
if not "%~1"=="" goto CUSTOM_LEVELS
set "LEVELS=5 10 20 50 100"
goto RUN_LEVELS
:CUSTOM_LEVELS
set "LEVELS=%*"
:RUN_LEVELS
for %%C in (%LEVELS%) do (
    echo [START] Concurrency=%%C
    "%JMETER_CMD%" -n -t "jmeter\ai_sse_performance_test.jmx" -q "jmeter\user.properties" -Jthreads=%%C -Jloops=%LOOPS% -JrampUp=%RAMP_UP% -Jhost=%HOST% -Jport=%PORT% -l "results\ladder\result_%%C.jtl"
    if errorlevel 1 (echo [ERROR] Concurrency=%%C failed.) else (echo [DONE] Concurrency=%%C)
)
python tools\aggregate_ladder.py results\ladder --html results\ladder\performance-summary.html --csv results\ladder\performance-summary.csv
echo Summary: results\ladder\performance-summary.html
endlocal
