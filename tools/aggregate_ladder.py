#!/usr/bin/env python3
"""Aggregate JMeter JTL files produced by a concurrency ladder."""

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


def number(row, *keys):
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            try:
                return float(value)
            except ValueError:
                pass
    return 0.0


def analyze_jtl(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None

    times = [number(r, "elapsed") for r in rows]
    errors = sum(str(r.get("success", "")).lower() != "true" for r in rows)

    stamps = [number(r, "timeStamp", "timestamp") for r in rows]
    end_times = [
        number(r, "timeStamp", "timestamp") + number(r, "elapsed")
        for r in rows
    ]
    if stamps and any(stamps):
        duration_s = max((max(end_times) - min(stamps)) / 1000.0, 0.001)
    else:
        duration_s = max(sum(times) / 1000.0, 0.001)

    match = re.search(r"result_(\d+)\.jtl$", os.path.basename(path), re.I)
    concurrency = int(match.group(1)) if match else 0

    return {
        "concurrency": concurrency,
        "samples": len(rows),
        "errors": errors,
        "error_rate_pct": round(errors / len(rows) * 100.0, 2),
        "tps": round(len(rows) / duration_s, 2),
        "avg_ms": round(sum(times) / len(times), 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
        "p50_ms": round(percentile(times, 50), 2),
        "p90_ms": round(percentile(times, 90), 2),
        "p95_ms": round(percentile(times, 95), 2),
        "p99_ms": round(percentile(times, 99), 2),
        "duration_s": round(duration_s, 2),
    }


def load_results(directory):
    paths = glob.glob(os.path.join(directory, "result_*.jtl"))
    results = []
    for path in paths:
        item = analyze_jtl(path)
        if item:
            results.append(item)
    return sorted(results, key=lambda x: x["concurrency"])


def write_csv(results, output):
    fields = [
        "concurrency", "samples", "errors", "error_rate_pct", "tps",
        "avg_ms", "min_ms", "max_ms", "p50_ms", "p90_ms", "p95_ms",
        "p99_ms", "duration_s",
    ]
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)


def write_html(results, output):
    def esc(v):
        return html.escape(str(v))

    body = "".join(
        "<tr>"
        f"<td>{esc(r['concurrency'])}</td>"
        f"<td>{esc(r['samples'])}</td>"
        f"<td>{esc(r['tps'])}</td>"
        f"<td>{esc(r['avg_ms'])}</td>"
        f"<td>{esc(r['p50_ms'])}</td>"
        f"<td>{esc(r['p90_ms'])}</td>"
        f"<td>{esc(r['p95_ms'])}</td>"
        f"<td>{esc(r['p99_ms'])}</td>"
        f"<td>{esc(r['min_ms'])}</td>"
        f"<td>{esc(r['max_ms'])}</td>"
        f"<td>{esc(r['error_rate_pct'])}%</td>"
        "</tr>"
        for r in results
    )

    if results:
        peak_tps = max(results, key=lambda x: x["tps"])
        latest = results[-1]
        cards = [
            ("测试等级", len(results)),
            ("最高并发", latest["concurrency"]),
            ("峰值 TPS", peak_tps["tps"]),
            ("峰值 TPS 并发", peak_tps["concurrency"]),
            ("最高并发 P95", f"{latest['p95_ms']} ms"),
            ("最高并发错误率", f"{latest['error_rate_pct']}%"),
        ]
        tps_points = ", ".join(
            f"[{r['concurrency']}, {r['tps']}]" for r in results
        )
        p95_points = ", ".join(
            f"[{r['concurrency']}, {r['p95_ms']}]" for r in results
        )
    else:
        cards = [("测试等级", 0)]
        tps_points = ""
        p95_points = ""

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
body{{font-family:Arial,"Microsoft YaHei",sans-serif;max-width:1250px;margin:30px auto;padding:0 20px;background:#f5f7fa;color:#222}}
h1{{margin-bottom:4px}} .muted{{color:#666}}
section{{background:#fff;border:1px solid #ddd;border-radius:10px;padding:20px;margin:18px 0}}
.cards{{display:flex;gap:12px;flex-wrap:wrap}}
.card{{border:1px solid #ddd;border-radius:8px;padding:14px;min-width:150px;background:#fff}}
.card span{{display:block;color:#666;font-size:13px;margin-bottom:6px}}
.card strong{{font-size:22px}}
table{{width:100%;border-collapse:collapse;background:#fff}}
th,td{{border:1px solid #ddd;padding:8px;text-align:right}}
th:first-child,td:first-child{{text-align:center}}
th{{background:#f0f2f5}}
canvas{{width:100%;height:320px;border:1px solid #eee;border-radius:8px}}
.note{{padding:12px;background:#f8f8f8;border-left:4px solid #999}}
</style>
</head>
<body>
<h1>AI API Performance Lab</h1>
<p class="muted">JMeter 并发阶梯测试汇总报告</p>

<section>
<h2>Summary</h2>
<div class="cards">{cards_html}</div>
</section>

<section>
<h2>Performance Matrix</h2>
<table>
<thead><tr>
<th>Concurrency</th><th>Samples</th><th>TPS</th><th>Avg</th>
<th>P50</th><th>P90</th><th>P95</th><th>P99</th>
<th>Min</th><th>Max</th><th>Error Rate</th>
</tr></thead>
<tbody>{body}</tbody>
</table>
</section>

<section>
<h2>TPS / P95 Trend</h2>
<canvas id="chart"></canvas>
<p class="muted">用于观察并发增加后的吞吐量与尾延迟变化。</p>
</section>

<section>
<h2>说明</h2>
<div class="note">
本报告负责客观汇总 JMeter 数据，不自动判断是否达标。
容量结论应结合实际业务 SLA、目标 TPS、P95/P99 延迟上限和允许错误率。
</div>
</section>

<script>
const tps = [{tps_points}];
const p95 = [{p95_points}];
const canvas = document.getElementById("chart");
const ctx = canvas.getContext("2d");

function resize() {{
  const ratio = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * ratio;
  canvas.height = rect.height * ratio;
  ctx.setTransform(ratio,0,0,ratio,0,0);
  draw(rect.width, rect.height);
}}

function draw(w,h) {{
  ctx.clearRect(0,0,w,h);
  if (!tps.length) return;
  const left=55, right=25, top=25, bottom=45;
  const pw=w-left-right, ph=h-top-bottom;
  const maxX=Math.max(...tps.map(p=>p[0]));
  const minX=Math.min(...tps.map(p=>p[0]));
  const maxY=Math.max(...tps.map(p=>Math.max(p[1], p95.find(q=>q[0]===p[0])[1])));
  const x=v=>left+(v-minX)/Math.max(maxX-minX,1)*pw;
  const y=v=>top+ph-v/Math.max(maxY,1)*ph;

  ctx.beginPath();
  ctx.moveTo(left,top);
  ctx.lineTo(left,top+ph);
  ctx.lineTo(left+pw,top+ph);
  ctx.stroke();

  ctx.font="12px Arial";
  tps.forEach(p=>ctx.fillText(String(p[0]),x(p[0])-8,top+ph+22));

  function line(data) {{
    ctx.beginPath();
    data.forEach((p,i)=>i===0?ctx.moveTo(x(p[0]),y(p[1])):ctx.lineTo(x(p[0]),y(p[1])));
    ctx.stroke();
    data.forEach(p=>{{ctx.beginPath();ctx.arc(x(p[0]),y(p[1]),4,0,Math.PI*2);ctx.fill();}});
  }}
  line(tps);
  line(p95);
  ctx.fillText("TPS",left+10,top+15);
  ctx.fillText("P95 ms",left+55,top+15);
}}
window.addEventListener("resize",resize);
resize();
</script>
</body>
</html>
"""
    with open(output, "w", encoding="utf-8") as f:
        f.write(page)


def main():
    parser = argparse.ArgumentParser(description="Aggregate JMeter concurrency ladder results.")
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

    print(f"Levels: {len(results)}")
    for r in results:
        print(
            f"C={r['concurrency']:>3} "
            f"TPS={r['tps']:>7} "
            f"Avg={r['avg_ms']:>8}ms "
            f"P95={r['p95_ms']:>8}ms "
            f"Err={r['error_rate_pct']:>5}%"
        )
    print(f"CSV written to {csv_path}")
    print(f"HTML written to {html_path}")


if __name__ == "__main__":
    main()
