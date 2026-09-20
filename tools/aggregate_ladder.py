#!/usr/bin/env python3
"""Aggregate JMeter JTL files produced by the AI API concurrency ladder."""

import argparse
import csv
import glob
import html
import math
import os
import re
from pathlib import Path


def percentile(values, p):
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * p / 100.0
    f, c = math.floor(k), math.ceil(k)
    return values[f] if f == c else values[f] + (values[c] - values[f]) * (k - f)


def number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def message_metric(message, key, default=None):
    match = re.search(r"(?:^|,)" + re.escape(key) + r"=([^,]+)", message or "")
    if not match:
        return default
    return match.group(1)


def stats(rows):
    times = [number(r.get("elapsed")) for r in rows]
    errors = sum(str(r.get("success", "")).lower() != "true" for r in rows)
    return {
        "samples": len(rows),
        "errors": errors,
        "error_rate_pct": round(errors / len(rows) * 100.0, 2) if rows else 0,
        "avg_ms": round(sum(times) / len(times), 2) if times else 0,
        "p50_ms": round(percentile(times, 50), 2),
        "p95_ms": round(percentile(times, 95), 2),
        "p99_ms": round(percentile(times, 99), 2),
        "min_ms": round(min(times), 2) if times else 0,
        "max_ms": round(max(times), 2) if times else 0,
    }


def analyze_jtl(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None

    stamps = [number(r.get("timeStamp", r.get("timestamp"))) for r in rows]
    ends = [number(r.get("timeStamp", r.get("timestamp"))) + number(r.get("elapsed")) for r in rows]
    duration_s = max((max(ends) - min(stamps)) / 1000.0, 0.001) if stamps else 0.001

    json_rows = [r for r in rows if "JSON" in r.get("label", "").upper()]
    sse_rows = [r for r in rows if "SSE" in r.get("label", "").upper()]

    error_types = {}
    sse_ttft = []
    sse_chunks = []
    sse_chars = []
    sse_done = 0
    for row in sse_rows:
        message = row.get("responseMessage", "")
        error_type = message_metric(message, "error_type", "NONE")
        if error_type and error_type != "NONE":
            error_types[error_type] = error_types.get(error_type, 0) + 1
        ttft = number(message_metric(message, "ttft_ms"), -1)
        chunks = number(message_metric(message, "chunks"), -1)
        chars = number(message_metric(message, "chars"), -1)
        done = message_metric(message, "done")
        if ttft >= 0:
            sse_ttft.append(ttft)
        if chunks >= 0:
            sse_chunks.append(chunks)
        if chars >= 0:
            sse_chars.append(chars)
        if done == "true":
            sse_done += 1

    match = re.search(r"result_(\d+)\.jtl$", os.path.basename(path), re.I)
    concurrency = int(match.group(1)) if match else 0
    overall = stats(rows)
    return {
        "concurrency": concurrency,
        "samples": len(rows),
        "errors": overall["errors"],
        "error_rate_pct": overall["error_rate_pct"],
        "tps": round(len(rows) / duration_s, 2),
        "avg_ms": overall["avg_ms"],
        "p50_ms": overall["p50_ms"],
        "p95_ms": overall["p95_ms"],
        "p99_ms": overall["p99_ms"],
        "json": stats(json_rows),
        "sse": stats(sse_rows),
        "sse_ttft_avg_ms": round(sum(sse_ttft) / len(sse_ttft), 2) if sse_ttft else 0,
        "sse_ttft_p95_ms": round(percentile(sse_ttft, 95), 2),
        "sse_chunks_avg": round(sum(sse_chunks) / len(sse_chunks), 2) if sse_chunks else 0,
        "sse_chars_avg": round(sum(sse_chars) / len(sse_chars), 2) if sse_chars else 0,
        "sse_done_rate_pct": round(sse_done / len(sse_rows) * 100.0, 2) if sse_rows else 0,
        "error_types": error_types,
        "timeout_count": error_types.get("CONNECT_TIMEOUT", 0) + error_types.get("READ_TIMEOUT", 0),
        "duration_s": round(duration_s, 2),
    }


def load_results(directory):
    paths = glob.glob(os.path.join(directory, "result_*.jtl"))
    results = [analyze_jtl(path) for path in paths]
    return sorted([r for r in results if r], key=lambda x: x["concurrency"])


def write_csv(results, output):
    fields = [
        "concurrency", "samples", "errors", "error_rate_pct", "tps",
        "avg_ms", "p50_ms", "p95_ms", "p99_ms",
        "json_avg_ms", "json_p95_ms", "json_error_rate_pct",
        "sse_avg_ms", "sse_p95_ms", "sse_error_rate_pct",
        "sse_ttft_avg_ms", "sse_ttft_p95_ms",
        "sse_chunks_avg", "sse_chars_avg", "sse_done_rate_pct",
        "timeout_count", "http_4xx_count", "http_5xx_count", "sse_protocol_error_count",
        "duration_s",
    ]
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            row = {k: r.get(k, "") for k in fields}
            row.update({
                "json_avg_ms": r["json"]["avg_ms"],
                "json_p95_ms": r["json"]["p95_ms"],
                "json_error_rate_pct": r["json"]["error_rate_pct"],
                "sse_avg_ms": r["sse"]["avg_ms"],
                "sse_p95_ms": r["sse"]["p95_ms"],
                "sse_error_rate_pct": r["sse"]["error_rate_pct"],
                "timeout_count": r["timeout_count"],
                "http_4xx_count": r["error_types"].get("HTTP_4XX", 0),
                "http_5xx_count": r["error_types"].get("HTTP_5XX", 0),
                "sse_protocol_error_count": sum(r["error_types"].get(k, 0) for k in ("SSE_NO_FIRST_CHUNK", "SSE_INCOMPLETE", "SSE_INTERRUPTED")),
            })
            writer.writerow(row)


def write_html(results, output):
    esc = lambda v: html.escape(str(v))

    rows = "".join(
        "<tr>"
        f"<td>{esc(r['concurrency'])}</td>"
        f"<td>{esc(r['tps'])}</td>"
        f"<td>{esc(r['json']['avg_ms'])}</td>"
        f"<td>{esc(r['json']['p95_ms'])}</td>"
        f"<td>{esc(r['sse']['avg_ms'])}</td>"
        f"<td>{esc(r['sse']['p95_ms'])}</td>"
        f"<td>{esc(r['sse_ttft_avg_ms'])}</td>"
        f"<td>{esc(r['sse_ttft_p95_ms'])}</td>"
        f"<td>{esc(r['sse_chunks_avg'])}</td>"
        f"<td>{esc(r['sse_chars_avg'])}</td>"
        f"<td>{esc(r['sse_error_rate_pct'])}%</td>"
        f"<td>{esc(r['timeout_count'])}</td>"
        f"<td>{esc(r['error_types'].get('HTTP_4XX', 0))}</td>"
        f"<td>{esc(r['error_types'].get('HTTP_5XX', 0))}</td>"
        "</tr>"
        for r in results
    )

    if results:
        latest = results[-1]
        peak = max(results, key=lambda x: x["tps"])
        cards = [
            ("测试等级", len(results)),
            ("最高并发", latest["concurrency"]),
            ("峰值 TPS", peak["tps"]),
            ("最高并发 JSON P95", f"{latest['json']['p95_ms']} ms"),
            ("最高并发 SSE P95", f"{latest['sse']['p95_ms']} ms"),
            ("最高并发 TTFT P95", f"{latest['sse_ttft_p95_ms']} ms"),
        ]
        tps_points = ", ".join(f"[{r['concurrency']},{r['tps']}]" for r in results)
        sse_p95_points = ", ".join(f"[{r['concurrency']},{r['sse']['p95_ms']}]" for r in results)
        ttft_points = ", ".join(f"[{r['concurrency']},{r['sse_ttft_p95_ms']}]" for r in results)
    else:
        cards = [("测试等级", 0)]
        tps_points = sse_p95_points = ttft_points = ""

    cards_html = "".join(
        f'<div class="card"><span>{esc(k)}</span><strong>{esc(v)}</strong></div>'
        for k, v in cards
    )

    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI API Performance Lab - Concurrency Ladder</title>
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;max-width:1400px;margin:30px auto;padding:0 20px;background:#f5f7fa;color:#222}}
section{{background:#fff;border:1px solid #ddd;border-radius:10px;padding:20px;margin:18px 0}}
.cards{{display:flex;gap:12px;flex-wrap:wrap}}
.card{{border:1px solid #ddd;border-radius:8px;padding:14px;min-width:150px}}
.card span{{display:block;color:#666;font-size:13px;margin-bottom:6px}}
.card strong{{font-size:21px}}
table{{width:100%;border-collapse:collapse}}
th,td{{border:1px solid #ddd;padding:8px;text-align:right}}
th:first-child,td:first-child{{text-align:center}}
th{{background:#f0f2f5}}
canvas{{width:100%;height:340px;border:1px solid #eee;border-radius:8px}}
.note{{padding:12px;background:#f8f8f8;border-left:4px solid #999}}
.muted{{color:#666}}
</style>
</head>
<body>
<h1>AI API Performance Lab</h1>
<p class="muted">JMeter AI API JSON + SSE 并发阶梯测试报告</p>

<section>
<h2>Summary</h2>
<div class="cards">{cards_html}</div>
</section>

<section>
<h2>AI API Performance Matrix</h2>
<table>
<thead><tr>
<th>Concurrency</th><th>TPS</th>
<th>JSON Avg</th><th>JSON P95</th>
<th>SSE Avg</th><th>SSE P95</th>
<th>SSE TTFT Avg</th><th>SSE TTFT P95</th>
<th>Chunks Avg</th><th>Chars Avg</th><th>SSE Error</th><th>Timeouts</th><th>HTTP 4xx</th><th>HTTP 5xx</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
</section>

<section>
<h2>Trend</h2>
<canvas id="chart"></canvas>
<p class="muted">同时展示 TPS、SSE P95 和 SSE TTFT P95，观察并发增长后的吞吐与流式延迟变化。</p>
</section>

<section>
<h2>说明</h2>
<div class="note">
本报告只做客观数据汇总，不自动判断是否达标。容量结论应结合实际业务 SLA、目标 TPS、P95/P99 延迟上限和允许错误率。
TTFT 为压测客户端从发起请求到读取第一个 SSE data 事件的观测时间。
</div>
</section>

<script>
const tps=[{tps_points}];
const sseP95=[{sse_p95_points}];
const ttft=[{ttft_points}];
const canvas=document.getElementById("chart");
const ctx=canvas.getContext("2d");

function resize(){{
  const ratio=window.devicePixelRatio||1;
  const rect=canvas.getBoundingClientRect();
  canvas.width=rect.width*ratio;
  canvas.height=rect.height*ratio;
  ctx.setTransform(ratio,0,0,ratio,0,0);
  draw(rect.width,rect.height);
}}
function draw(w,h){{
  ctx.clearRect(0,0,w,h);
  if(!tps.length)return;
  const left=55,right=25,top=25,bottom=45;
  const pw=w-left-right,ph=h-top-bottom;
  const maxX=Math.max(...tps.map(p=>p[0]));
  const minX=Math.min(...tps.map(p=>p[0]));
  const maxY=Math.max(...tps.map(p=>Math.max(p[1],sseP95.find(q=>q[0]===p[0])[1],ttft.find(q=>q[0]===p[0])[1])));
  const x=v=>left+(v-minX)/Math.max(maxX-minX,1)*pw;
  const y=v=>top+ph-v/Math.max(maxY,1)*ph;

  ctx.beginPath();
  ctx.moveTo(left,top);ctx.lineTo(left,top+ph);ctx.lineTo(left+pw,top+ph);ctx.stroke();
  ctx.font="12px Arial";
  tps.forEach(p=>ctx.fillText(String(p[0]),x(p[0])-8,top+ph+22));

  function line(data){{
    ctx.beginPath();
    data.forEach((p,i)=>i===0?ctx.moveTo(x(p[0]),y(p[1])):ctx.lineTo(x(p[0]),y(p[1])));
    ctx.stroke();
    data.forEach(p=>{{ctx.beginPath();ctx.arc(x(p[0]),y(p[1]),4,0,Math.PI*2);ctx.fill();}});
  }}
  line(tps);line(sseP95);line(ttft);
  ctx.fillText("TPS",left+10,top+15);
  ctx.fillText("SSE P95",left+55,top+15);
  ctx.fillText("TTFT P95",left+120,top+15);
}}
window.addEventListener("resize",resize);resize();
</script>
</body>
</html>"""
    with open(output, "w", encoding="utf-8") as f:
        f.write(page)


def main():
    parser = argparse.ArgumentParser(description="Aggregate AI API JSON + SSE concurrency ladder results.")
    parser.add_argument("directory", help="Directory containing result_<concurrency>.jtl files")
    parser.add_argument("--html", default=None)
    parser.add_argument("--csv", default=None)
    args = parser.parse_args()

    results = load_results(args.directory)
    if not results:
        raise SystemExit(f"No result_*.jtl files found in: {args.directory}")

    html_path = args.html or os.path.join(args.directory, "performance-summary.html")
    csv_path = args.csv or os.path.join(args.directory, "performance-summary.csv")
    Path(html_path).parent.mkdir(parents=True, exist_ok=True)
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)

    write_csv(results, csv_path)
    write_html(results, html_path)

    for r in results:
        print(
            f"C={r['concurrency']:>3} TPS={r['tps']:>7} "
            f"JSON-P95={r['json']['p95_ms']:>8}ms "
            f"SSE-P95={r['sse']['p95_ms']:>8}ms "
            f"TTFT-P95={r['sse_ttft_p95_ms']:>8}ms "
            f"SSE-Err={r['sse']['error_rate_pct']:>5}%"
        )
    print(f"CSV written to {csv_path}")
    print(f"HTML written to {html_path}")


if __name__ == "__main__":
    main()
