#!/usr/bin/env python3
import pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
R = Path(__file__).resolve().parents[1]
df = pd.read_csv(R/"data"/"mlc_gran_mix.csv")
seq = df[df["pattern"]=="seq"].sort_values("stride_B")
rand = df[df["pattern"]=="rand"].sort_values("stride_B")
plt.figure(); plt.plot(seq["stride_B"], seq["bandwidth_MBps"], marker="o", label="Seq"); plt.plot(rand["stride_B"], rand["bandwidth_MBps"], marker="o", label="Rand")
plt.xlabel("Stride (bytes)"); plt.ylabel("Bandwidth (MB/s)"); plt.title("Bandwidth vs Stride — "); plt.legend(); plt.tight_layout(); plt.savefig(R/"figures"/"granularity_bandwidth.png")
plt.figure(); plt.plot(seq["stride_B"], seq["latency_ns"], marker="o", label="Seq"); plt.plot(rand["stride_B"], rand["latency_ns"], marker="o", label="Rand")
plt.xlabel("Stride (bytes)"); plt.ylabel("Avg Latency (ns)"); plt.title("Latency vs Stride — "); plt.legend(); plt.tight_layout(); plt.savefig(R/"figures"/"granularity_latency.png")