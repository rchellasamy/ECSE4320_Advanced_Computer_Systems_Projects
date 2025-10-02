#!/usr/bin/env python3
import os, pandas as pd
os.makedirs("docs", exist_ok=True)

df = pd.read_csv("data/results.csv")

# Ensure these columns exist/in order
cols = ["kernel","dtype","align","stride","N","build","median_ms","stdev_ms","gflops","cpe","reduce"]
for c in cols:
    if c not in df.columns:
        df[c] = float("nan")
df = df[cols]

# normalize for neat grouping
for c in ["kernel","dtype","align","build"]:
    df[c] = df[c].astype(str).str.strip().str.lower()

# sort for readability
df = df.sort_values(["kernel","dtype","align","stride","N","build"])

out = "data/results_clean.csv"
df.to_csv(out, index=False)
print("Wrote", out)

with open("docs/CSV_README.md","w") as f:
    f.write("""# results.csv schema

Columns: kernel, dtype, align, stride, N, build, median_ms, stdev_ms, gflops, cpe, reduce

- `build` is either `auto` (auto-vectorized) or `scalar` (vectorization disabled).
- `align` is `aligned` or `misaligned`.
- `stride` contains stride/gather experiments (1, 2, 4, 8...).
- `reduce` holds a correctness checksum:
  - DOT: the dot-product scalar result
  - SAXPY: sum of output y
  - EWMUL: sum of output z

This CSV contains scalar vs SIMD, aligned vs misaligned, float32 vs float64,
stride sweeps, and working-set size sweeps across L1→L2→LLC→DRAM.
""")
print("Wrote docs/CSV_README.md")
