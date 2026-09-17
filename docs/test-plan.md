# Test Plan

## Objectives

1. Verify AI API functional availability.
2. Measure ordinary JSON API latency and throughput.
3. Measure SSE stream completion time and chunk characteristics.
4. Produce reproducible JMeter result files for later analysis.

## Workload

- Threads: configurable with `-Jthreads`
- Ramp-up: configurable with `-JrampUp`
- Loops: configurable with `-Jloops`
- Host/port: configurable with `-Jhost` and `-Jport`

## Metrics

Average, P50, P90, P95, P99, TPS, error rate, bytes, SSE chunks and characters.
