#!/usr/bin/env bash
set -e
python3 mock-server/app.py &
PID=$!
trap 'kill $PID' EXIT
sleep 1
jmeter -n -t jmeter/ai_sse_performance_test.jmx -q jmeter/user.properties -l result.jtl
python3 tools/analyze_result.py result.jtl
python3 tools/generate_report.py result.jtl report.html
