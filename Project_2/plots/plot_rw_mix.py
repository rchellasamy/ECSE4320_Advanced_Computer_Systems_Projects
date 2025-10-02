#!/usr/bin/env python3
import pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
R = Path(__file__).resolve().parents[1]
df = pd.read_csv(R/"data"/"mlc_rw_mix.csv")
plt.figure(); plt.plot(df["ratio"], df["bandwidth_MBps"], marker="o")
plt.ylabel("Bandwidth (MB/s)"); plt.title("Read/Write Mix — ")
plt.tight_layout(); plt.savefig(R/"figures"/"rw_mix_bandwidth.png")
plt.figure(); plt.plot(df["ratio"], df["latency_ns"], marker="o")
plt.ylabel("Latency (ns)"); plt.title("Read/Write Mix Latency — ")
plt.tight_layout(); plt.savefig(R/"figures"/"rw_mix_latency.png")