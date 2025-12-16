import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse

def ci95(x):
    x = np.asarray(x, dtype=float)
    if len(x) < 2:
        return 0.0
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results.csv")
    ap.add_argument("--out_prefix", default="plot")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    grp_cols = ["filter","n","target_fpr","load","fp_bits","r_bits","threads","qfrac","neg_share","ops"]
    g = df.groupby(grp_cols).agg(
        achieved_fpr_mean=("achieved_fpr","mean"),
        achieved_fpr_ci=("achieved_fpr", ci95),
        bpe_mean=("bpe","mean"),
        bpe_ci=("bpe", ci95),
        thr_mean=("throughput_ops_s","mean"),
        thr_ci=("throughput_ops_s", ci95),
        p95_mean=("p95_ns","mean"),
        p99_mean=("p99_ns","mean"),
        insert_fail_mean=("insert_fail","mean"),
        kicks_mean=("kicks","mean"),
        stash_hits_mean=("stash_hits","mean"),
        fp_checks_mean=("fp_checks","mean"),
        scan_steps_mean=("scan_steps","mean"),
    ).reset_index()

    plt.figure()
    for flt in sorted(g["filter"].unique()):
        sub = g[(g["filter"]==flt) & (g["threads"]==1) & (g["qfrac"]==1.0)]
        if sub.empty:
            continue
        plt.errorbar(
            sub["bpe_mean"],
            sub["achieved_fpr_mean"],
            xerr=sub["bpe_ci"],
            yerr=sub["achieved_fpr_ci"],
            fmt='o',
            label=flt
        )
    plt.yscale("log")
    plt.xlabel("Bits per entry (mean)")
    plt.ylabel("Achieved FPR (mean)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{args.out_prefix}_space_vs_fpr.png", dpi=160)

    plt.figure()
    n0 = g["n"].min()
    for flt in sorted(g["filter"].unique()):
        sub = g[(g["filter"]==flt) & (g["n"]==n0) & (g["threads"]==1) & (g["qfrac"]==1.0)]
        if sub.empty:
            continue
        sub = sub.sort_values("neg_share")
        plt.errorbar(sub["neg_share"], sub["thr_mean"], yerr=sub["thr_ci"], fmt='o-', label=flt)
    plt.xlabel("Negative lookup share")
    plt.ylabel("Ops/s (mean)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{args.out_prefix}_throughput_vs_negshare.png", dpi=160)

    plt.figure()
    for flt in ["cuckoo","qf"]:
        sub = g[(g["filter"]==flt) & (g["threads"]==1) & (g["qfrac"]<1.0)]
        if sub.empty:
            continue
        sub = sub.sort_values("load")
        plt.plot(sub["load"], sub["thr_mean"], marker='o', label=flt)
    plt.xlabel("Load factor")
    plt.ylabel("Ops/s (mixed)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{args.out_prefix}_ops_vs_load.png", dpi=160)

if __name__ == "__main__":
    main()
