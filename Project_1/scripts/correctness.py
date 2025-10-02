#!/usr/bin/env python3
import os, subprocess, pandas as pd, numpy as np

CSV = "data/correctness_tmp.csv"
OUT = "docs/correctness.txt"
os.makedirs("docs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Seed the CSV with a header so pandas knows column names even if utils.cpp
# doesn't write a header when the file exists-but-empty.
HEADER = "kernel,dtype,align,stride,N,build,median_ms,stdev_ms,gflops,cpe,reduce\n"
with open(CSV, "w") as f:
    f.write(HEADER)

cases = [
  ("saxpy","f32",16), ("saxpy","f32",32),
  ("saxpy","f64",16), ("saxpy","f64",32),
  ("ewmul","f32",16), ("ewmul","f32",32),
  ("ewmul","f64",16), ("ewmul","f64",32),
  ("dot","f32",16),   ("dot","f32",32),
  ("dot","f64",16),   ("dot","f64",32),
]

def run(build_dir, K, DT, N):
    cmd = [
      f"./{build_dir}/simd_profile",
      "--kernel", K, "--dtype", DT, "--align", "aligned",
      "--stride", "1", "--N", str(N),
      "--trials", "5", "--warmups", "1",
      "--min-ms", "5.0",  # IMPORTANT: repeat inside one trial to get finite time
      "--build-label", ("auto" if build_dir=="build" else "scalar"),
      "--csv", CSV, "--cpu-ghz", "3.6"
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


rows = []
for K,DT,N in cases:
    run("build",        K,DT,N)  # auto
    run("build-scalar", K,DT,N)  # scalar

    df = pd.read_csv(CSV)

    # Normalize just in case
    for c in ["kernel","dtype","align","build"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.lower()
    if "N" in df.columns:      df["N"] = df["N"].astype(int, errors="ignore")
    if "stride" in df.columns: df["stride"] = df["stride"].astype(int, errors="ignore")

    sub = df[
        (df["kernel"]==K) & (df["dtype"]==DT) &
        (df["N"]==N) & (df["align"]=="aligned") & (df["stride"]==1)
    ]
    # Take the most recent rows per build
    p = sub.groupby("build").tail(1).set_index("build")
    have_both = {"auto","scalar"}.issubset(set(p.index))

    rel_err = np.nan
    g_auto = np.nan
    g_scalar = np.nan

    if have_both:
        g_auto   = float(p.loc["auto","gflops"])
        g_scalar = float(p.loc["scalar","gflops"])
        # Compare the scalar 'reduce' checksum values
        a = float(p.loc["auto","reduce"])
        s = float(p.loc["scalar","reduce"])
        denom  = max(1e-30, abs(s))
        rel_err = abs(a - s) / denom

    tol = 1e-6 if DT=="f32" else 1e-12
    result = "PASS" if (have_both and rel_err <= tol) else "FAIL"

    rows.append([K,DT,N, g_auto, g_scalar, rel_err, tol, result])

with open(OUT,"w") as f:
    f.write("kernel  dtype   N   GF/s(auto)   GF/s(scalar)   rel_err    tol      result\n")
    for r in rows:
        f.write(f"{r[0]:6s}  {r[1]:4s}  {r[2]:6d}  {r[3]:10.4f}   {r[4]:11.4f}   {r[5]:.3e}  {r[6]:.0e}   {r[7]}\n")

print("Wrote", OUT)
