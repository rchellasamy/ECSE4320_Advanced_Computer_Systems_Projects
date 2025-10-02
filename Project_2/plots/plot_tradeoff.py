#!/usr/bin/env python3
import pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
R = Path(__file__).resolve().parents[1]
df = pd.read_csv(R/"data"/"mlc_intensity.csv")
plt.figure(); plt.plot(df["avg_latency_ns"], df["bandwidth_MBps"], marker="o")
for x,y,t in zip(df["avg_latency_ns"], df["bandwidth_MBps"], df["threads"]): 
    plt.annotate(str(int(t)), (x,y), textcoords="offset points", xytext=(4,4))
plt.xlabel("Latency (ns)"); plt.ylabel("Throughput (MB/s)"); plt.title("Throughput–Latency Trade-off — ")
plt.tight_layout(); plt.savefig(R/"figures"/"intensity_tradeoff.png")