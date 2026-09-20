#!/usr/bin/env python3
import csv
import html
import math
import re
import sys
from collections import defaultdict


def percentile(values, p):
    if not values:
        return 0
    values = sorted(values)
    k = (len(values) - 1) * p / 100
    f, c = math.floor(k), math.ceil(k)
    return values[f] if f == c else values[f] + (values[c] - values[f]) * (k - f)


def num(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def metric(message, key, default=None):
    match = re.search(r"(?:^|,)" + re.escape(key) + r"=([^,]+)", message or "")
    return match.group(1) if match else default


def label_stats(rows):
    times = [num(r.get("elapsed")) for r in rows]
    errors = sum(str(r.get("success", "")).lower() != "true" for r in rows)
    return {
        "samples": len(rows),
        "errors": errors,
        "error_rate": errors / len(rows) * 100 if rows else 0,
        "avg": sum(times) / len(times) if times else 0,
        "p50": percentile(times, 50),
        "p95": percentile(times, 95),
        "p99": percentile(times, 99),
    }


def main(jtl, out):
    with open(jtl, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    errors = sum(str(r.get("success", "")).lower() != "true" for r in rows)
    times = [num(r.get("elapsed")) for r in rows]

    stamps = [num(r.get("timeStamp", r.get("timestamp"))) for r in rows]
    ends = [num(r.get("timeStamp", r.get("timestamp"))) + num(r.get("elapsed")) for r in rows]
    start = min(stamps, default=0)
    end = max(ends, default=start)
    duration = max((end - start) / 1000, 0.001)

    groups = defaultdict(list)
    ttft = []
    chunks = []
    error_types = defaultdict(int)
    chars = []
    done = 0

    for row in rows:
        label = row.get("label", "")
        groups[label].append(row)
        message = row.get("responseMessage", "")
        et = metric(message, "error_type", "NONE")
        if et and et != "NONE":
            error_types[et] += 1
        if "SSE" in label.upper():
            t = num(metric(message, "ttft_ms"), -1)
            if t >= 0:
                ttft.append(t)
            c = num(metric(message, "chunks"), -1)
            if c >= 0:
                chunks.append(c)
            ch = num(metric(message, "chars"), -1)
            if ch >= 0:
                chars.append(ch)
            if metric(message, "done") == "true":
                done += 1

    cards = [
        ("Samples", str(total)),
        ("Errors", str(errors)),
        ("Error Rate", f"{errors / total * 100:.2f}%" if total else "0.00%"),
        ("TPS", f"{total / duration:.2f}"),
        ("Average", f"{sum(times) / total:.2f} ms" if total else "0.00 ms"),
        ("P95", f"{percentile(times, 95):.2f} ms"),
        ("P99", f"{percentile(times, 99):.2f} ms"),
    ]

    cards_html = "".join(
        f'<div class="card"><span>{html.escape(k)}</span><b>{html.escape(v)}</b></div>'
        for k, v in cards
    )

    api_rows = []
    for label, items in groups.items():
        s = label_stats(items)
        api_rows.append(
            "<tr>"
            f"<td>{html.escape(label)}</td>"
            f"<td>{s['samples']}</td>"
            f"<td>{s['avg']:.2f} ms</td>"
            f"<td>{s['p50']:.2f} ms</td>"
            f"<td>{s['p95']:.2f} ms</td>"
            f"<td>{s['p99']:.2f} ms</td>"
            f"<td>{s['error_rate']:.2f}%</td>"
            "</tr>"
        )

    error_html = ""
    if error_types:
        error_rows = "".join(
            f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>"
            for k, v in sorted(error_types.items(), key=lambda item: (-item[1], item[0]))
        )
        error_html = f"""
<section>
<h2>异常分类</h2>
<table>
<tr><th>异常类型</th><th>次数</th></tr>
{error_rows}
</table>
<p class="muted">分类来自 JMeter sampler 的 error_type。598 表示 SSE 协议/流结束异常；599 表示客户端网络或超时异常；HTTP 4xx/5xx 保留服务端 HTTP 状态码。</p>
</section>
"""
    sse_html = ""
    if ttft:
        sse_html = f"""
<section>
<h2>SSE 专项指标</h2>
<div class="cards">
<div class="card"><span>TTFT Average</span><b>{sum(ttft)/len(ttft):.2f} ms</b></div>
<div class="card"><span>TTFT P50</span><b>{percentile(ttft,50):.2f} ms</b></div>
<div class="card"><span>TTFT P95</span><b>{percentile(ttft,95):.2f} ms</b></div>
<div class="card"><span>TTFT P99</span><b>{percentile(ttft,99):.2f} ms</b></div>
<div class="card"><span>Avg Chunks</span><b>{sum(chunks)/len(chunks):.2f}</b></div>
<div class="card"><span>Avg Output Chars</span><b>{sum(chars)/len(chars):.2f}</b></div>
<div class="card"><span>Done Rate</span><b>{done/len(ttft)*100:.2f}%</b></div>
</div>
<p class="muted">TTFT 为压测客户端从发起请求到读取第一个 SSE data 事件的观测时间，不等同于模型服务端内部生成首 token 时间。</p>
</section>
"""

    body = "".join(
        "<tr>"
        f"<td>{html.escape(r.get('label',''))}</td>"
        f"<td>{html.escape(r.get('elapsed',''))}</td>"
        f"<td>{html.escape(r.get('responseCode',''))}</td>"
        f"<td>{html.escape(r.get('success',''))}</td>"
        "</tr>"
        for r in rows[-100:]
    )

    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI API Performance Report</title>
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;max-width:1200px;margin:30px auto;padding:0 20px;background:#f6f8fa;color:#222}}
section{{background:#fff;border:1px solid #ddd;border-radius:10px;padding:20px;margin:18px 0}}
.cards{{display:flex;gap:12px;flex-wrap:wrap}}
.card{{border:1px solid #ddd;border-radius:8px;padding:14px;min-width:130px;background:#fff}}
.card span{{display:block;color:#666;font-size:13px;margin-bottom:7px}}
.card b{{font-size:20px}}
table{{width:100%;border-collapse:collapse;background:#fff}}
th,td{{border:1px solid #ddd;padding:8px;text-align:right}}
th:first-child,td:first-child{{text-align:left}}
th{{background:#f0f2f5}}
.muted{{color:#666}}
</style>
</head>
<body>
<h1>AI API Performance Lab</h1>
<p class="muted">Generated from JMeter JTL: {html.escape(jtl)}</p>

<section>
<h2>Overall Summary</h2>
<div class="cards">{cards_html}</div>
</section>

<section>
<h2>API Scenario Comparison</h2>
<table>
<tr><th>Label</th><th>Samples</th><th>Average</th><th>P50</th><th>P95</th><th>P99</th><th>Error Rate</th></tr>
{"".join(api_rows)}
</table>
</section>

{sse_html}

{error_html}

<section>
<h2>Recent Samples</h2>
<table>
<tr><th>Label</th><th>Elapsed</th><th>Code</th><th>Success</th></tr>
{body}
</table>
</section>

<section>
<h2>说明</h2>
<p class="muted">报告只汇总测试数据，不自动判断是否达标。容量结论应结合业务 SLA、目标 TPS、P95/P99 延迟上限和允许错误率。</p>
</section>
</body>
</html>"""

    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Report written to {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python generate_report.py result.jtl report.html")
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
