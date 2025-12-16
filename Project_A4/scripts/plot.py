#!/usr/bin/env python3
import os
import csv
from collections import defaultdict

import matplotlib.pyplot as plt


CSV_PATH = os.path.join("results", "results.csv")
OUT_DIR = "results"
FIXED_THREADS_FOR_KEYS_PLOT = 8 

THREAD_TICKS = [1, 2, 4, 8, 16]
WORKLOAD_ORDER = ["lookup", "insert", "mixed"]
MODE_ORDER = ["coarse", "striped"]


def read_csv(path):
    rows = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["keys"] = int(r["keys"])
            r["threads"] = int(r["threads"])
            r["read_pct"] = int(r["read_pct"])
            r["ops_per_thread"] = int(r["ops_per_thread"])
            r["throughput_ops_per_s"] = float(r["throughput_ops_per_s"])

            def parse_optional_float(x):
                if x is None:
                    return None
                x = str(x).strip()
                if x == "" or x.upper() == "NA":
                    return None
                try:
                    return float(x)
                except ValueError:
                    return None

            r["cycles"] = parse_optional_float(r.get("cycles"))
            r["instructions"] = parse_optional_float(r.get("instructions"))
            r["cache_references"] = parse_optional_float(r.get("cache_references"))
            r["cache_misses"] = parse_optional_float(r.get("cache_misses"))

            rows.append(r)
    return rows


def ensure_outdir():
    os.makedirs(OUT_DIR, exist_ok=True)


def nice_order(items, preferred_order):
    s = set(items)
    ordered = [x for x in preferred_order if x in s]
    ordered += [x for x in sorted(items) if x not in set(ordered)]
    return ordered


def group_rows(rows):
    """
    Index rows by (keys, workload, mode) -> {threads: row}
    Keep the full row per thread so we can also plot derived metrics.
    """
    data = defaultdict(dict)
    keys_set = set()
    workloads_set = set()
    modes_set = set()

    for r in rows:
        k = r["keys"]
        w = r["workload"]
        m = r["mode"]
        t = r["threads"]
        keys_set.add(k)
        workloads_set.add(w)
        modes_set.add(m)
        data[(k, w, m)][t] = r  # store full row

    keys_list = sorted(keys_set)
    workloads = nice_order(workloads_set, WORKLOAD_ORDER)
    modes = nice_order(modes_set, MODE_ORDER)
    return data, keys_list, workloads, modes


def plot_throughput_vs_threads(data, keys_list, workloads, modes):
    for k in keys_list:
        for w in workloads:
            plt.figure()
            for m in modes:
                series = data.get((k, w, m), {})
                if not series:
                    continue
                ts = sorted(series.keys())
                ys = [series[t]["throughput_ops_per_s"] for t in ts]
                plt.plot(ts, ys, marker="o", label=m)

            plt.xlabel("Threads")
            plt.ylabel("Throughput (ops/s)")
            plt.title(f"Throughput vs Threads — workload={w}, keys={k}")
            plt.xticks(THREAD_TICKS)
            plt.legend()
            out = os.path.join(OUT_DIR, f"throughput_threads_workload-{w}_keys-{k}.png")
            plt.savefig(out, dpi=200, bbox_inches="tight")
            plt.close()


def plot_speedup_vs_threads(data, keys_list, workloads, modes):
    for k in keys_list:
        for w in workloads:
            plt.figure()
            for m in modes:
                series = data.get((k, w, m), {})
                if not series or 1 not in series:
                    continue
                base = series[1]["throughput_ops_per_s"]
                ts = sorted(series.keys())
                ys = [series[t]["throughput_ops_per_s"] / base for t in ts]
                plt.plot(ts, ys, marker="o", label=m)

            plt.xlabel("Threads")
            plt.ylabel("Speedup vs 1 thread")
            plt.title(f"Speedup vs Threads — workload={w}, keys={k}")
            plt.xticks(THREAD_TICKS)
            plt.legend()
            out = os.path.join(OUT_DIR, f"speedup_threads_workload-{w}_keys-{k}.png")
            plt.savefig(out, dpi=200, bbox_inches="tight")
            plt.close()


def plot_throughput_vs_keys_at_threads(data, keys_list, workloads, modes, fixed_threads):
    """
    For each workload, plot throughput vs keys at a fixed thread count.
    """
    for w in workloads:
        plt.figure()
        for m in modes:
            xs = []
            ys = []
            for k in keys_list:
                series = data.get((k, w, m), {})
                if fixed_threads in series:
                    xs.append(k)
                    ys.append(series[fixed_threads]["throughput_ops_per_s"])
            if xs:
                plt.plot(xs, ys, marker="o", label=m)

        plt.xlabel("Keys (initial dataset size)")
        plt.ylabel(f"Throughput (ops/s) @ {fixed_threads} threads")
        plt.title(f"Throughput vs Keys @ {fixed_threads} threads — workload={w}")
        plt.xscale("log")
        plt.legend()
        out = os.path.join(OUT_DIR, f"throughput_keys_workload-{w}_threads-{fixed_threads}.png")
        plt.savefig(out, dpi=200, bbox_inches="tight")
        plt.close()


def plot_cycles_per_op_vs_threads(data, keys_list, workloads, modes):
    """
    Extra evidence plot: cycles/op vs threads (lower is better).
    cycles/op = cycles / total_ops, where total_ops = threads * ops_per_thread.
    """
    for k in keys_list:
        for w in workloads:
            plt.figure()
            plotted_any = False
            for m in modes:
                series = data.get((k, w, m), {})
                if not series:
                    continue

                xs, ys = [], []
                for t in sorted(series.keys()):
                    row = series[t]
                    cycles = row.get("cycles")
                    if cycles is None:
                        continue
                    total_ops = float(row["threads"]) * float(row["ops_per_thread"])
                    if total_ops <= 0:
                        continue
                    xs.append(t)
                    ys.append(cycles / total_ops)

                if xs:
                    plotted_any = True
                    plt.plot(xs, ys, marker="o", label=m)

            if not plotted_any:
                plt.close()
                continue

            plt.xlabel("Threads")
            plt.ylabel("Cycles per operation")
            plt.title(f"Cycles/op vs Threads — workload={w}, keys={k}")
            plt.xticks(THREAD_TICKS)
            plt.legend()
            out = os.path.join(OUT_DIR, f"cycles_per_op_threads_workload-{w}_keys-{k}.png")
            plt.savefig(out, dpi=200, bbox_inches="tight")
            plt.close()


def plot_cache_misses_per_op_vs_threads(data, keys_list, workloads, modes):
    """
    Extra evidence plot: cache-misses/op vs threads (proxy for cache/coherence effects on WSL).
    cache_misses/op = cache_misses / total_ops.
    """
    for k in keys_list:
        for w in workloads:
            plt.figure()
            plotted_any = False
            for m in modes:
                series = data.get((k, w, m), {})
                if not series:
                    continue

                xs, ys = [], []
                for t in sorted(series.keys()):
                    row = series[t]
                    cm = row.get("cache_misses")
                    if cm is None:
                        continue
                    total_ops = float(row["threads"]) * float(row["ops_per_thread"])
                    if total_ops <= 0:
                        continue
                    xs.append(t)
                    ys.append(cm / total_ops)

                if xs:
                    plotted_any = True
                    plt.plot(xs, ys, marker="o", label=m)

            if not plotted_any:
                plt.close()
                continue

            plt.xlabel("Threads")
            plt.ylabel("Cache-misses per operation")
            plt.title(f"Cache-misses/op vs Threads — workload={w}, keys={k}")
            plt.xticks(THREAD_TICKS)
            plt.legend()
            out = os.path.join(OUT_DIR, f"cache_misses_per_op_threads_workload-{w}_keys-{k}.png")
            plt.savefig(out, dpi=200, bbox_inches="tight")
            plt.close()


def main():
    ensure_outdir()

    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Could not find {CSV_PATH}. Run scripts/sweep.sh first.")

    rows = read_csv(CSV_PATH)
    data, keys_list, workloads, modes = group_rows(rows)

    plot_throughput_vs_threads(data, keys_list, workloads, modes)
    plot_speedup_vs_threads(data, keys_list, workloads, modes)
    plot_throughput_vs_keys_at_threads(data, keys_list, workloads, modes, FIXED_THREADS_FOR_KEYS_PLOT)

    plot_cycles_per_op_vs_threads(data, keys_list, workloads, modes)
    plot_cache_misses_per_op_vs_threads(data, keys_list, workloads, modes)

    print("Done. Plots written to results/*.png")
    print(f"- Used CSV: {CSV_PATH}")
    print(f"- Keys: {keys_list}")
    print(f"- Workloads: {workloads}")
    print(f"- Modes: {modes}")
    print(f"- Throughput vs Keys thread count: {FIXED_THREADS_FOR_KEYS_PLOT}")
    print("- Also wrote: cycles_per_op_* and cache_misses_per_op_* plots (if counters available).")


if __name__ == "__main__":
    main()
