#!/usr/bin/env python3
# Usage: calibrate.py <appdir> <prefix> <runs> — N cold rig runs, print medians + spread.
import json, subprocess, sys, statistics, glob, os

appdir, prefix, runs = sys.argv[1], sys.argv[2], int(sys.argv[3])
rows = []
for i in range(1, runs + 1):
    tag = f"{prefix}_{i}"
    snap = subprocess.run(["bash", "-c", "ps -eo pid,pcpu,comm,args | grep -E 'node|codex' | grep -v grep | head -5"],
                          capture_output=True, text=True).stdout.strip()
    r = subprocess.run(["bash", "/workspace/ghclone/scripts/rig.sh", appdir, str(8100 + i), tag],
                       capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip().splitlines()
    cpuline = [l for l in out if "cpu=" in l]
    cpu_s = None
    if cpuline and "cpu=" in cpuline[0]:
        try: cpu_s = float(cpuline[0].split("cpu=")[1])
        except ValueError: cpu_s = None
    try:
        d = json.load(open(f"{appdir}/rig_{tag}.json"))
    except Exception as e:
        print(f"run {i}: PARSE FAIL {e} | {out[-3:]}"); continue
    c = d.get("columns", {})
    p = d.get("perf") or {}
    row = {"run": i, "feature": c.get("feature"), "working": c.get("working"),
           "perf_p50_us": p.get("perf_p50_us"),
           "score": c.get("score"), "server_cpu_s": cpu_s}
    # per-workload p50s from nested workloads list
    for w in (p.get("workloads") or []):
        row[w["name"] + "_p50_ms"] = w.get("p50_ms")
    rows.append(row)
    print("run", i, row, flush=True)
    if snap: print("  ps:", snap.replace("\n", " | "), flush=True)

print("\n=== summary over", len(rows), "runs ===")
for key in rows[0]:
    if key in ("run", "feature", "working"): continue
    vals = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
    if not vals: continue
    med = statistics.median(vals)
    print(f"{key}: median={med} min={min(vals)} max={max(vals)} spread={max(vals)-min(vals)} all={vals}")
feats = set(r.get("feature") for r in rows); works = set(r.get("working") for r in rows)
print("feature:", feats, "working:", works)
with open(f"{appdir}/calib_{prefix}.json", "w") as f: json.dump(rows, f, indent=1)
