#!/usr/bin/env python3
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict


def pct(values, p):
    if not values:
        return 0
    values = sorted(values)
    k = (len(values) - 1) * p / 100
    f, c = math.floor(k), math.ceil(k)
    return values[f] if f == c else values[f] + (values[c] - values[f]) * (k - f)


def num(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def message_metric(message, key, default=None):
    match = re.search(r"(?:^|,)" + re.escape(key) + r"=([^,]+)", message or "")
    if not match:
        return default
    return match.group(1)


def analyze_label(rows):
    times = [num(r.get("elapsed"), 0) for r in rows]
    errors = sum(str(r.get("success", "")).lower() != "true" for r in rows)
    return {
        "samples": len(rows),
        "errors": errors,
        "error_rate_pct": round(errors / len(rows) * 100, 2) if rows else 0,
        "avg_ms": round(sum(times) / len(times), 2) if times else 0,
        "min_ms": round(min(times), 2) if times else 0,
        "max_ms": round(max(times), 2) if times else 0,
        "p50_ms": round(pct(times, 50), 2),
        "p90_ms": round(pct(times, 90), 2),
        "p95_ms": round(pct(times, 95), 2),
        "p99_ms": round(pct(times, 99), 2),
    }


def main(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print(json.dumps({"samples": 0}, ensure_ascii=False, indent=2))
        return

    times = [num(r.get("elapsed"), 0) for r in rows]
    errors = sum(1 for r in rows if str(r.get("success", "")).lower() != "true")

    def stamp(r):
        return num(r.get("timeStamp", r.get("timestamp", "0")), 0)

    start = min(stamp(r) for r in rows)
    end = max(stamp(r) + num(r.get("elapsed"), 0) for r in rows)
    duration = max((end - start) / 1000, 0.001)

    by_label = defaultdict(list)
    sse_ttft = []
    sse_chunks = []
    sse_chars = []
    sse_done = 0

    for row in rows:
        label = row.get("label", "")
        by_label[label].append(row)

        if "SSE" in label.upper():
            message = row.get("responseMessage", row.get("responseMessage", ""))
            ttft = num(message_metric(message, "ttft_ms"))
            chunks = num(message_metric(message, "chunks"))
            chars = num(message_metric(message, "chars"))
            done = message_metric(message, "done")
            if ttft is not None and ttft >= 0:
                sse_ttft.append(ttft)
            if chunks is not None:
                sse_chunks.append(chunks)
            if chars is not None:
                sse_chars.append(chars)
            if done == "true":
                sse_done += 1

    result = {
        "samples": len(rows),
        "errors": errors,
        "error_rate_pct": round(errors / len(rows) * 100, 2),
        "tps": round(len(rows) / duration, 2),
        "avg_ms": round(sum(times) / len(times), 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
        "p50_ms": round(pct(times, 50), 2),
        "p90_ms": round(pct(times, 90), 2),
        "p95_ms": round(pct(times, 95), 2),
        "p99_ms": round(pct(times, 99), 2),
        "labels": {label: analyze_label(items) for label, items in by_label.items()},
    }

    if sse_ttft:
        result["sse"] = {
            "samples": len(sse_ttft),
            "ttft_avg_ms": round(sum(sse_ttft) / len(sse_ttft), 2),
            "ttft_p50_ms": round(pct(sse_ttft, 50), 2),
            "ttft_p95_ms": round(pct(sse_ttft, 95), 2),
            "ttft_p99_ms": round(pct(sse_ttft, 99), 2),
            "chunk_avg": round(sum(sse_chunks) / len(sse_chunks), 2) if sse_chunks else 0,
            "output_chars_avg": round(sum(sse_chars) / len(sse_chars), 2) if sse_chars else 0,
            "done_rate_pct": round(sse_done / len(sse_ttft) * 100, 2),
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python analyze_result.py result.jtl")
        sys.exit(2)
    main(sys.argv[1])
