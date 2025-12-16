#!/usr/bin/env bash
set -euo pipefail

IN=results_a3
OUT=plots_a3
mkdir -p "$OUT"

python3 - <<'PY'
import os, pandas as pd, matplotlib.pyplot as plt

IN="results_a3"
OUT="plots_a3"
os.makedirs(OUT, exist_ok=True)

def load_csv(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return pd.read_csv(path)

def avg_by(df, keys):
    # average across runs for each setting
    num_cols = [c for c in df.columns if df[c].dtype.kind in "if"]
    return df.groupby(keys, as_index=False)[num_cols].mean()

# --- 1) BPE vs achieved FPR curves ---
curves = [
    ("bloom_fpr.csv",  "bloom",  "target_fpr", "bpe", "achieved_fpr"),
    ("xor_fpbits.csv", "xor",    "fp_bits",    "bpe", "achieved_fpr"),
    ("cuckoo_fpbits.csv","cuckoo","fp_bits",   "bpe", "achieved_fpr"),
    ("qf_rbits.csv",   "qf",     "r_bits",     "bpe", "achieved_fpr"),
]
plt.figure()
for fname, label, knob, bpe, fpr in curves:
    df = avg_by(load_csv(os.path.join(IN, fname)), [knob])
    plt.plot(df[fpr], df[bpe], marker="o", label=label)
plt.xscale("log")
plt.xlabel("achieved_fpr (log)")
plt.ylabel("bits per entry (bpe)")
plt.title("BPE vs FPR")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT, "bpe_vs_fpr.png"), dpi=200)
plt.close()

# --- 2) Throughput vs negative share (all filters) ---
df = avg_by(load_csv(os.path.join(IN, "thr_vs_neg.csv")), ["filter","neg_share"])
plt.figure()
for flt in df["filter"].unique():
    s = df[df["filter"]==flt].sort_values("neg_share")
    plt.plot(s["neg_share"], s["throughput_ops_s"], marker="o", label=flt)
plt.xlabel("neg_share")
plt.ylabel("throughput (ops/s)")
plt.title("Throughput vs Negative Share")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT, "throughput_vs_neg_share.png"), dpi=200)
plt.close()

# --- 3) Load sweep throughput + failures (cuckoo + qf) ---
for fname, title in [("cuckoo_load.csv","Cuckoo"), ("qf_load.csv","Quotient Filter")]:
    df = avg_by(load_csv(os.path.join(IN, fname)), ["load"])
    df = df.sort_values("load")

    plt.figure()
    plt.plot(df["load"], df["throughput_ops_s"], marker="o")
    plt.xlabel("load")
    plt.ylabel("throughput (ops/s)")
    plt.title(f"{title}: Throughput vs Load")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, f"{fname[:-4]}_throughput_vs_load.png"), dpi=200)
    plt.close()

    # insert_fail if present (cuckoo)
    if "insert_fail" in df.columns:
        plt.figure()
        plt.plot(df["load"], df["insert_fail"], marker="o")
        plt.xlabel("load")
        plt.ylabel("insert_fail")
        plt.title(f"{title}: Insert Fail vs Load")
        plt.tight_layout()
        plt.savefig(os.path.join(OUT, f"{fname[:-4]}_insert_fail_vs_load.png"), dpi=200)
        plt.close()

# --- 4) Mixed workload (throughput vs qfrac) ---
for fname, title in [("cuckoo_mixed.csv","Cuckoo"), ("qf_mixed.csv","Quotient Filter")]:
    df = avg_by(load_csv(os.path.join(IN, fname)), ["qfrac"])
    df = df.sort_values("qfrac")
    plt.figure()
    plt.plot(df["qfrac"], df["throughput_ops_s"], marker="o")
    plt.xlabel("qfrac")
    plt.ylabel("throughput (ops/s)")
    plt.title(f"{title}: Throughput vs Query Fraction")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, f"{fname[:-4]}_throughput_vs_qfrac.png"), dpi=200)
    plt.close()

print(f"Wrote plots to {OUT}/")
PY
