#!/usr/bin/env python3
import pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
R = Path(__file__).resolve().parents[1]
df = pd.read_csv(R/"data"/"zero_queue.csv")
plt.figure(); plt.bar(df["level"].astype(str), df["latency_ns"].fillna(0.0))
plt.ylabel("Latency (ns)"); plt.title("Zero-Queue Latency — ")
plt.tight_layout(); plt.savefig(R/"figures"/"zero_queue.png")