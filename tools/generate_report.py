#!/usr/bin/env python3
import csv, html, sys

def main(jtl, out):
    with open(jtl, newline='', encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    total=len(rows); errors=sum(str(r.get('success','')).lower()!='true' for r in rows)
    avg=sum(float(r.get('elapsed','0') or 0) for r in rows)/total if total else 0
    body=''.join('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(html.escape(r.get('label','')),r.get('elapsed',''),r.get('responseCode',''),r.get('success','')) for r in rows[-100:])
    page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>AI API Performance Report</title><style>body{{font-family:Arial,sans-serif;max-width:1100px;margin:30px auto;padding:0 20px}}.cards{{display:flex;gap:12px;flex-wrap:wrap}}.card{{border:1px solid #ddd;border-radius:8px;padding:18px;min-width:150px}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #ddd;padding:8px}}</style><h1>AI API Performance Lab</h1><div class="cards"><div class="card">Samples<br><b>{total}</b></div><div class="card">Errors<br><b>{errors}</b></div><div class="card">Avg(ms)<br><b>{avg:.2f}</b></div></div><h2>Recent Samples</h2><table><tr><th>Label</th><th>Elapsed</th><th>Code</th><th>Success</th></tr>{body}</table></html>'''
    open(out,'w',encoding='utf-8').write(page)

if __name__=='__main__':
    if len(sys.argv)!=3: print('usage: python generate_report.py result.jtl report.html'); sys.exit(2)
    main(sys.argv[1],sys.argv[2])
