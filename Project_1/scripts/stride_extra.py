import os, pandas as pd, numpy as np, matplotlib.pyplot as plt
os.makedirs("docs", exist_ok=True)
df = pd.read_csv("data/results.csv")
for c in ["kernel","dtype","align","build"]:
    df[c] = df[c].astype(str).str.strip().str.lower()
for c in ["stride","N","time_ms","median_ms"]:
    if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
def pick_best_N(kernel="dot", dtype="f32", align="aligned"):
    sub = df[(df.kernel==kernel)&(df.dtype==dtype)&(df.align==align)&(df.stride==1)]
    if sub.empty: return None
    have = sub.groupby("N")["build"].nunique()
    ok = [int(n) for n in have[have>=2].index]
    return max(ok) if ok else None
def plot_stride(kernel="dot", dtype="f32", align="aligned"):
    N = pick_best_N(kernel,dtype,align)
    if N is None: print(f"[stride] no suitable N for {kernel}/{dtype}/{align}"); return
    sub = df[(df.kernel==kernel)&(df.dtype==dtype)&(df.align==align)&(df.N==N)&(df.stride.isin([1,2,4,8]))]
    if sub.empty: print(f"[stride] no rows for {kernel}/{dtype}/{align} at N={N:,}"); return
    v = "median_ms" if "median_ms" in sub.columns else "time_ms"
    agg = sub.groupby(["stride","build"])[v].median().unstack()
    fig = plt.figure(figsize=(6,4), dpi=140); ax = plt.gca()
    x = np.arange(len(agg.index)); w = 0.35
    ax.bar(x - w/2, agg["scalar"], w, label="scalar")
    ax.bar(x + w/2, agg["auto"],   w, label="auto")
    ax.set_xticks(x); ax.set_xticklabels([str(s) for s in agg.index])
    ax.set_xlabel("stride"); ax.set_ylabel("Median time (ms)")
    ax.set_title(f"{kernel.upper()} stride ({dtype}, {align}, N={N:,})")
    ax.legend()
    out = f"docs/stride_{kernel}_{dtype}_{align}_N{N}.png"
    plt.tight_layout(); plt.savefig(out); plt.close(); print("Wrote", out)
if __name__ == "__main__":
    plot_stride("dot","f32","aligned")
