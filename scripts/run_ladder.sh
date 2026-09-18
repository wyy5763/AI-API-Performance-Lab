#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
LOOPS="\${LOOPS:-10}"
RAMP_UP="\${RAMP_UP:-5}"
HOST="\${HOST:-127.0.0.1}"
PORT="\${PORT:-8088}"
JMETER_CMD="\${JMETER_CMD:-jmeter}"
mkdir -p results/ladder
if [ "$#" -gt 0 ]; then LEVELS=("$@"); else LEVELS=(5 10 20 50 100); fi
for concurrency in "\${LEVELS[@]}"; do
  echo "[START] Concurrency=$concurrency"
  "$JMETER_CMD" -n -t "jmeter/ai_sse_performance_test.jmx" -q "jmeter/user.properties" -Jthreads="$concurrency" -Jloops="$LOOPS" -JrampUp="$RAMP_UP" -Jhost="$HOST" -Jport="$PORT" -l "results/ladder/result_\${concurrency}.jtl"
done
python3 tools/aggregate_ladder.py results/ladder --html results/ladder/performance-summary.html --csv results/ladder/performance-summary.csv
echo "Summary: results/ladder/performance-summary.html"
