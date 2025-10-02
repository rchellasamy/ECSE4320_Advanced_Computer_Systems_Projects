#!/usr/bin/env python3
import pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
R = Path(__file__).resolve().parents[1]
df = pd.read_csv(R/"data"/"mlc_cache_miss.csv")
plt.figure(); plt.plot(df["miss_rate"], df["throughput_MBps"], marker="o")
plt.xlabel("Miss rate"); plt.ylabel("Throughput (MB/s)")
plt.title("Cache-Miss Impact — ")
plt.tight_layout(); plt.savefig(R/"figures"/"cache_miss.png")