#!/usr/bin/env python3
# Interleaved A/B: alternate baseline and revised cold runs, B-A-B-A..., N per arm.
# Usage: ab.py <baseline_dir> <revised_dir> <runs_per_arm>
# Gates: kill all non-essential processes first (caller's responsibility).
import json, subprocess, statistics, sys, os

base, rev, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
KEYS = ["perf_p50_us", "score", "push_p50_ms", "clone_p50_ms", "read_p50_ms", "write_p50_ms"]

def run(appdir, arm, i):
    tag = f"ab_{arm}_{i}"
    r = subprocess.run(["bash", "/workspace/ghclone/scripts/rig.sh", appdir, str(8200 + i), tag],
                       capture_output=True, text=True)
    try:
        d = json.load(open(f"{appdir}/rig_{tag}.json"))
    except Exception as e:
        print(f"{arm}{i}: PARSE FAIL {e}"); return None
    c, p = d.get("columns", {}), d.get("perf") or {}
    row = {"feature": c.get("feature"), "working": c.get("working"),
           "perf_p50_us": p.get("perf_p50_us"), "score": c.get("score")}
    for w in (p.get("workloads") or []):
        row[w["name"] + "_p50_ms"] = w.get("p50_ms")
    print(f"{arm}{i}: {row}", flush=True)
    return row

def summarize(rows, label):
    print(f"\n== {label} ({len(rows)} runs) ==")
    for k in KEYS:
        v = [r[k] for r in rows if isinstance(r.get(k), (int, float))]
        if not v: continue
        print(f"  {k}: median={statistics.median(v)} min={min(v)} max={max(v)} spread={max(v)-min(v)}")
    f = set(r["feature"] for r in rows); w = set(r["working"] for r in rows)
    print(f"  feature={f} working={w}")
    return {k: statistics.median([r[k] for r in rows if isinstance(r.get(k),(int,float))]) for k in KEYS}

B, A = [], []
for i in range(1, n + 1):
    rb = run(base, "B", i);  B.append(rb) if rb else None
    ra = run(rev, "A", i);   A.append(ra) if ra else None

mb, ma = summarize(B, "BASELINE B"), summarize(A, "REVISED A")
print("\n== decision ==")
for k in KEYS:
    if k in ("score", "perf_p50_us") or k.endswith("_p50_ms"):
        lo_b, hi_b = min(r.get(k, 1e18) for r in B), max(r.get(k, 1e18) for r in B)
        lo_a, hi_a = min(r.get(k, 1e18) for r in A), max(r.get(k, 1e18) for r in A)
        overlap = not (hi_a < lo_b or hi_b < lo_a)
        print(f"  {k}: B_med={mb.get(k)} A_med={ma.get(k)} overlap={overlap}")
json.dump({"B": B, "A": A}, open("/workspace/ghclone/ab_results.json", "w"), indent=1)
