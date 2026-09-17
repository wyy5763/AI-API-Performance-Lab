#!/usr/bin/env python3
import csv, json, math, sys
from collections import Counter

def pct(values, p):
    if not values: return 0
    values = sorted(values)
    k = (len(values)-1) * p / 100
    f, c = math.floor(k), math.ceil(k)
    return values[f] if f == c else values[f] + (values[c]-values[f])*(k-f)

def main(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    if not rows:
        print(json.dumps({'samples':0}, ensure_ascii=False, indent=2)); return
    times=[float(r.get('elapsed','0') or 0) for r in rows]
    errors=sum(1 for r in rows if str(r.get('success','')).lower()!='true')
    def stamp(r): return float(r.get('timeStamp', r.get('timestamp','0')) or 0)
    start=min(stamp(r) for r in rows)
    end=max(stamp(r)+float(r.get('elapsed','0') or 0) for r in rows)
    duration=max((end-start)/1000,0.001)
    result={
      'samples':len(rows), 'errors':errors, 'error_rate_pct':round(errors/len(rows)*100,2),
      'tps':round(len(rows)/duration,2), 'avg_ms':round(sum(times)/len(times),2),
      'min_ms':round(min(times),2), 'max_ms':round(max(times),2),
      'p50_ms':round(pct(times,50),2), 'p90_ms':round(pct(times,90),2),
      'p95_ms':round(pct(times,95),2), 'p99_ms':round(pct(times,99),2),
      'labels':dict(Counter(r.get('label','') for r in rows))
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__=='__main__':
    if len(sys.argv)!=2:
        print('usage: python analyze_result.py result.jtl'); sys.exit(2)
    main(sys.argv[1])
