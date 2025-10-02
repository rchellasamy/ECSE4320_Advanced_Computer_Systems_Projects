#!/usr/bin/env python3
import pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
R = Path(__file__).resolve().parents[1]
df = pd.read_csv(R/"data"/"mlc_workingset.csv")
plt.figure(); plt.plot(df["working_set_KiB"], df["bandwidth_MBps"], marker="o")
for x in [48,128,30720]: plt.axvline(x, linestyle="--")
plt.xscale("log"); plt.xlabel("Working set (KiB)"); plt.ylabel("Bandwidth (MB/s)")
plt.title("Working-Set Size Sweep — ")
plt.tight_layout(); plt.savefig(R/"figures"/"working_set_bandwidth.png")
plt.figure(); plt.plot(df["working_set_KiB"], df["latency_ns"], marker="o")
for x in [48,128,30720]: plt.axvline(x, linestyle="--")
plt.xscale("log"); plt.xlabel("Working set (KiB)"); plt.ylabel("Latency (ns)")
plt.title("Working-Set Latency — ")
plt.tight_layout(); plt.savefig(R/"figures"/"working_set_latency.png")