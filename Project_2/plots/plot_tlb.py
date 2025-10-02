#!/usr/bin/env python3
import pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
R = Path(__file__).resolve().parents[1]
df = pd.read_csv(R/"data"/"mlc_tlb.csv")
for col, ylab, fn in [("bandwidth_MBps","Bandwidth (MB/s)","tlb_bandwidth.png"),
                      ("latency_ns","Latency (ns)","tlb_latency.png")]:
    plt.figure()
    for mode, sub in df.groupby("page_mode"):
        plt.plot(sub["locality_pages"], sub[col], marker="o", label=mode)
    plt.xscale("log"); plt.xlabel("Page-locality (unique pages)"); plt.ylabel(ylab)
    plt.title("TLB Impact — "); plt.legend()
    plt.tight_layout(); plt.savefig(R/"figures"/f"{fn}")