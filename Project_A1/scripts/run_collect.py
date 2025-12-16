#!/usr/bin/env python3
import argparse
import csv
import os
import re
import shutil
import statistics
import subprocess
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
os.chdir(ROOT_DIR)

def has_perf():
    return shutil.which("perf") is not None

KV_RE = re.compile(r'(\w+)=(".*?"|[^\s]+)')

def parse_kv(stdout: str):
    """
    Parse single-line output with fields like: key=value key2=value2 ...
    Returns dict[str,str]
    """
    kv = {}
    for k, v in KV_RE.findall(stdout.strip()):
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        kv[k] = v
    return kv

def run_once(cmd):
    """
    Run cmd exactly once.
    If perf exists, wrap it and parse:
      - cycles:u
      - seconds time elapsed
    Returns (stdout_kv, cycles_or_None, perf_elapsed_or_None, stderr_snip)
    """
    cycles = None
    pelapsed = None
    stderr_note = ""

    if has_perf():
        perf_cmd = ["perf", "stat", "-e", "cycles:u", "--"] + cmd
        p = subprocess.run(perf_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()

        if p.returncode != 0:
            raise RuntimeError(f"Command failed: {cmd}\nstdout={out}\nstderr={err}")

        m = re.search(r'\s([0-9,]+)\s+cycles:u', err)
        if m:
            cycles = int(m.group(1).replace(",", ""))

        m2 = re.search(r'\s([0-9.]+)\s+seconds time elapsed', err)
        if m2:
            pelapsed = float(m2.group(1))

        stderr_note = err[:300]
        return parse_kv(out), cycles, pelapsed, stderr_note

    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()

    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nstdout={out}\nstderr={err}")

    return parse_kv(out), None, None, err[:300]

def mean_sd(vals):
    if not vals:
        return None, None
    if len(vals) == 1:
        return vals[0], 0.0
    return statistics.mean(vals), statistics.pstdev(vals)

def collect(cmd, repeats, warmup_s, extra_cols):
    """
    Repeats running cmd and aggregates metrics.
    """
    if warmup_s > 0:
        t_end = time.time() + warmup_s
        while time.time() < t_end:
            try:
                run_once(cmd)
            except Exception:
                pass
            time.sleep(0.05)

    kvs = []
    cycles_list = []
    pelapsed_list = []
    stderr_notes = []

    for _ in range(repeats):
        kv, cycles, pelapsed, note = run_once(cmd)
        kvs.append(kv)
        if cycles is not None:
            cycles_list.append(cycles)
        if pelapsed is not None:
            pelapsed_list.append(pelapsed)
        if note:
            stderr_notes.append(note)
        time.sleep(0.05)

    row = dict(extra_cols)

    first = kvs[0] if kvs else {}
    for k, v in first.items():
        row[k] = v

    for base in ["seconds", "touches_per_s", "accesses_per_s", "pair_tsc"]:
        vals = []
        for kv in kvs:
            if base in kv:
                try:
                    vals.append(float(kv[base]))
                except Exception:
                    pass
        m, sd = mean_sd(vals)
        if m is not None:
            row[f"{base}_mean"] = m
            row[f"{base}_sd"] = sd

    if cycles_list:
        row["cycles_mean"] = statistics.mean(cycles_list)
        row["cycles_sd"] = statistics.pstdev(cycles_list) if len(cycles_list) > 1 else 0.0
    else:
        row["cycles_mean"] = "NA"
        row["cycles_sd"] = "NA"

    if pelapsed_list:
        row["perf_elapsed_mean"] = statistics.mean(pelapsed_list)
        row["perf_elapsed_sd"] = statistics.pstdev(pelapsed_list) if len(pelapsed_list) > 1 else 0.0
    else:
        row["perf_elapsed_mean"] = "NA"
        row["perf_elapsed_sd"] = "NA"

    row["stderr_note"] = (" | ".join(stderr_notes))[:300] if stderr_notes else ""
    return row

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=7)
    ap.add_argument("--warmup", type=float, default=1.0)
    ap.add_argument("--out", default="results.csv")
    args = ap.parse_args()

    rows = []

    for pinned in [0, 1]:
        cmd = ["./affinity", "--threads", "2", "--iters", "300000000", "--pinned", str(pinned)]
        rows.append(collect(cmd, args.repeats, args.warmup, {
            "experiment": "affinity",
            "pinned": pinned
        }))

    for case in ["same", "spread"]:
        cmd = ["./smt", case, "30000000"]
        rows.append(collect(cmd, args.repeats, args.warmup, {
            "experiment": "smt",
            "case": case
        }))

    for stride in [16, 64, 256, 1024]:
        cmd = ["./mmu", "--mb", "256", "--stride", str(stride), "--reps", "5"]
        rows.append(collect(cmd, args.repeats, args.warmup, {
            "experiment": "mmu",
            "stride_elems": stride
        }))


    for mode in ["seq", "rand_idx", "ptr_chase"]:
        cmd = ["./prefetch", mode, "268435456", "200000000"]
        rows.append(collect(cmd, args.repeats, args.warmup, {
            "experiment": "prefetch",
            "mode": mode
        }))

    fieldnames = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Wrote {args.out} with {len(rows)} rows.")

if __name__ == "__main__":
    main()
