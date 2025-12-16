#!/usr/bin/env python3
import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt

def make_label(row: pd.Series) -> str:
    for col in ["benchmark", "experiment", "name", "feature"]:
        if col in row and pd.notna(row[col]) and str(row[col]).strip() != "":
            base = str(row[col])
            break
    else:
        base = "row"

    parts = []
    for col in ["case", "mode", "pattern", "stride_elems", "threads", "pinned", "thp"]:
        if col in row and pd.notna(row[col]) and str(row[col]).strip() != "":
            parts.append(f"{col}={row[col]}")
    if parts:
        return base + " (" + ", ".join(parts) + ")"
    return base

def plot_with_errorbars(df: pd.DataFrame, ycol: str, sdcol: str, ylabel: str, title: str, outpath: str):
    fig = plt.figure()

    y = pd.to_numeric(df[ycol], errors="coerce")
    yerr = pd.to_numeric(df[sdcol], errors="coerce").fillna(0)

    x = list(range(len(df)))
    labels = [make_label(df.iloc[i]) for i in range(len(df))]

    plt.xticks(x, labels, rotation=30, ha="right")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.errorbar(x, y, yerr=yerr, fmt="o")
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close(fig)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results.csv")
    ap.add_argument("--outdir", default="plots")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    os.makedirs(args.outdir, exist_ok=True)

    if "seconds_mean" not in df.columns or "seconds_sd" not in df.columns:
        raise SystemExit("CSV must contain seconds_mean and seconds_sd columns")

    plot_with_errorbars(
        df,
        ycol="seconds_mean",
        sdcol="seconds_sd",
        ylabel="Seconds (mean ± sd)",
        title="Benchmark runtime",
        outpath=os.path.join(args.outdir, "runtime_seconds.png"),
    )

    if "cycles_mean" in df.columns and df["cycles_mean"].notna().any():
        if "cycles_sd" not in df.columns:
            df["cycles_sd"] = 0

        plot_with_errorbars(
            df,
            ycol="cycles_mean",
            sdcol="cycles_sd",
            ylabel="Cycles (mean ± sd)",
            title="Perf cycles",
            outpath=os.path.join(args.outdir, "perf_cycles.png"),
        )

    print(f"Wrote plots into: {args.outdir}/")

if __name__ == "__main__":
    main()
