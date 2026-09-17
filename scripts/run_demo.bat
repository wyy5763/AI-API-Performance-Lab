@echo off
setlocal
start "AI API Mock" cmd /k "python mock-server\app.py"
timeout /t 2 >nul
jmeter -n -t jmeter\ai_sse_performance_test.jmx -q jmeter\user.properties -l result.jtl
python tools\analyze_result.py result.jtl
python tools\generate_report.py result.jtl report.html
echo Done. Open report.html
