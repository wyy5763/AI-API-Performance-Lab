#!/usr/bin/env python3
import csv, html, math, sys

def percentile(values, p):
    if not values: return 0
    values = sorted(values)
    k = (len(values) - 1) * p / 100
    f, c = math.floor(k), math.ceil(k)
    return values[f] if f == c else values[f] + (values[c] - values[f]) * (k - f)

def main(jtl, out):
    with open(jtl, newline='', encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    total=len(rows)
    errors=sum(str(r.get('success','')).lower()!='true' for r in rows)
    times=[float(r.get('elapsed','0') or 0) for r in rows]
    start=min((float(r.get('timeStamp', r.get('timestamp','0')) or 0) for r in rows), default=0)
    end=max((float(r.get('timeStamp', r.get('timestamp','0')) or 0)+float(r.get('elapsed','0') or 0) for r in rows), default=start)
    duration=max((end-start)/1000,0.001)
    avg=sum(times)/total if total else 0
    tps=total/duration
    metrics=[('Samples',str(total)),('Errors',str(errors)),('Error Rate',f'{errors/total*100:.2f}%' if total else '0.00%'),('TPS',f'{tps:.2f}'),('Average',f'{avg:.2f} ms'),('P50',f'{percentile(times,50):.2f} ms'),('P90',f'{percentile(times,90):.2f} ms'),('P95',f'{percentile(times,95):.2f} ms'),('P99',f'{percentile(times,99):.2f} ms')]
    cards=''.join(f'<div class="card">{html.escape(k)}<br><b>{html.escape(v)}</b></div>' for k,v in metrics)
    body=''.join('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(html.escape(r.get('label','')),r.get('elapsed',''),r.get('responseCode',''),r.get('success','')) for r in rows[-100:])
    page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI API Performance Report</title><style>body{{font-family:Arial,"Microsoft YaHei",sans-serif;max-width:1100px;margin:30px auto;padding:0 20px;background:#f6f8fa}}section{{background:#fff;border:1px solid #ddd;border-radius:10px;padding:20px;margin:18px 0}}.cards{{display:flex;gap:12px;flex-wrap:wrap}}.card{{border:1px solid #ddd;border-radius:8px;padding:14px;min-width:130px;background:#fff}}table{{width:100%;border-collapse:collapse;background:#fff}}th,td{{border:1px solid #ddd;padding:8px}}h1{{margin-bottom:4px}}.muted{{color:#666}}</style><h1>AI API Performance Lab</h1><p class="muted">Generated from JMeter JTL: {html.escape(jtl)}</p><section><h2>Summary</h2><div class="cards">{cards}</div></section><section><h2>Recent Samples</h2><table><tr><th>Label</th><th>Elapsed</th><th>Code</th><th>Success</th></tr>{body}</table></section></html>'''
    with open(out,'w',encoding='utf-8') as f: f.write(page)
    print(f'Report written to {out}')

if __name__=='__main__':
    if len(sys.argv)!=3: print('usage: python generate_report.py result.jtl report.html'); sys.exit(2)
    main(sys.argv[1],sys.argv[2])
