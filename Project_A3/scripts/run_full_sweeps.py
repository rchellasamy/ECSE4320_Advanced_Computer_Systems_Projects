#!/usr/bin/env python3

from __future__ import annotations

import argparse
import itertools
import os
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    print(" ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def physical_cores() -> int:
    try:
        out = subprocess.check_output(["bash", "-lc", "lscpu -p=CORE | grep -v '^#' | sort -u | wc -l"]).decode().strip()
        v = int(out)
        return max(1, v)
    except Exception:
        return max(1, os.cpu_count() or 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", default="./build/amq_bench")
    ap.add_argument("--out", default="results.csv")
    ap.add_argument("--ops", type=int, default=2_000_000)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--quick", action="store_true", help="smaller matrix for sanity")
    args = ap.parse_args()

    b = args.bin
    out = args.out
    Path(out).parent.mkdir(parents=True, exist_ok=True)

    Ns = [1_000_000, 5_000_000, 10_000_000]
    fprs = [0.05, 0.01, 0.001]
    negs = [0.0, 0.5, 0.9]
    mixes = [1.0, 0.95, 0.50]
    loads = [round(x, 2) for x in [0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95]]
    fpbits = [8, 12, 16]
    rbits = [8, 12, 16]

    if args.quick:
        Ns = [1_000_000]
        fprs = [0.01]
        negs = [0.5]
        mixes = [0.95]
        loads = [0.70, 0.90]
        fpbits = [12]
        rbits = [12]

    cores = physical_cores()
    thread_list = list(range(1, cores + 1))
    if args.quick:
        thread_list = [1, min(2, cores)]
        thread_list = sorted(set(thread_list))

    for n, fpr, neg, qfrac, t in itertools.product(Ns, fprs, negs, mixes, thread_list):
        run([
            b, "--filter", "bloom", "--n", str(n), "--fpr", str(fpr), "--neg", str(neg),
            "--qfrac", str(qfrac), "--threads", str(t), "--ops", str(args.ops), "--runs", str(args.runs),
            "--out", out
        ])

    for n, fp, neg, t in itertools.product(Ns, fpbits, negs, thread_list):
        run([
            b, "--filter", "xor", "--n", str(n), "--fpbits", str(fp), "--neg", str(neg),
            "--threads", str(t), "--ops", str(args.ops), "--runs", str(args.runs), "--out", out
        ])

    for n, load, fp, neg, qfrac, t in itertools.product(Ns, loads, fpbits, negs, mixes, thread_list):
        run([
            b, "--filter", "cuckoo", "--n", str(n), "--load", str(load), "--fpbits", str(fp),
            "--neg", str(neg), "--qfrac", str(qfrac), "--threads", str(t), "--ops", str(args.ops),
            "--runs", str(args.runs), "--out", out
        ])

    for n, load, rb, neg, qfrac, t in itertools.product(Ns, loads, rbits, negs, mixes, thread_list):
        run([
            b, "--filter", "qf", "--n", str(n), "--load", str(load), "--rbits", str(rb),
            "--neg", str(neg), "--qfrac", str(qfrac), "--threads", str(t), "--ops", str(args.ops),
            "--runs", str(args.runs), "--out", out
        ])

    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
