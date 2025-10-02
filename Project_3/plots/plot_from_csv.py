
#!/usr/bin/env python3
import os, csv, argparse
import matplotlib.pyplot as plt

def R(p): 
    with open(p, newline="") as f: 
        return list(csv.DictReader(f))

def F(x): 
    try: return float(x)
    except: return None

def S(p): 
    os.makedirs(os.path.dirname(p), exist_ok=True); 
    plt.tight_layout(); plt.savefig(p, dpi=150); plt.close()

def zeroq(inp, outp):
    RWS=[("random","read","4k"),("random","write","4k"),("sequential","read","128k"),("sequential","write","128k")]
    rows=R(inp); L=[]; V=[]; E=[]
    for pat,op,bs in RWS:
        for r in rows:
            if r["pattern"]==pat and r["op"]==op and r["bs"].lower()==bs:
                L.append(f"{pat[:3]} {op} {bs}")
                V.append(F(r["bw_mib_s_mean"])); E.append(F(r["bw_mib_s_std"])); break
    if V:
        plt.figure(); plt.bar(range(len(V)), V, yerr=E); plt.xticks(range(len(L)), L, rotation=15, ha="right")
        plt.ylabel("Bandwidth (MiB/s)"); plt.title("Zero-Queue (mean ± 5%)"); S(outp)

def gran(inp, out_bw, out_lat):
    rows=R(inp); seq=[r for r in rows if r["pattern"]=="seq"]; rnd=[r for r in rows if r["pattern"]=="rand"]
    seq.sort(key=lambda r:int(r["stride_B"])); rnd.sort(key=lambda r:int(r["stride_B"]))
    x1=[int(r["stride_B"]) for r in seq]; y1=[F(r["bandwidth_mib_s"]) for r in seq]; e1=[F(r["bandwidth_mib_s_std"]) for r in seq]
    x2=[int(r["stride_B"]) for r in rnd]; y2=[F(r["bandwidth_mib_s"]) for r in rnd]; e2=[F(r["bandwidth_mib_s_std"]) for r in rnd]
    plt.figure(); plt.errorbar(x1,y1,yerr=e1,marker="o"); plt.errorbar(x2,y2,yerr=e2,marker="o")
    plt.xlabel("Stride (bytes)"); plt.ylabel("Bandwidth (MiB/s)"); plt.title("Pattern×Granularity — BW"); S(out_bw)
    y1=[F(r["latency_us"]) for r in seq]; e1=[F(r["latency_us_std"]) for r in seq]
    y2=[F(r["latency_us"]) for r in rnd]; e2=[F(r["latency_us_std"]) for r in rnd]
    plt.figure(); plt.errorbar(x1,y1,yerr=e1,marker="o"); plt.errorbar(x2,y2,yerr=e2,marker="o")
    plt.xlabel("Stride (bytes)"); plt.ylabel("Latency (µs)"); plt.title("Pattern×Granularity — Lat"); S(out_lat)

def mix(inp, out_bw, out_lat):
    rows=R(inp); order=["R100","R70W30","R50W50","W100"]; rows=[r for r in rows if r["mix"] in order]; rows.sort(key=lambda r:order.index(r["mix"]))
    x=list(range(len(rows))); y=[F(r["bandwidth_mib_s"]) for r in rows]; e=[F(r["bandwidth_mib_s_std"]) for r in rows]
    plt.figure(); plt.bar(x,y,yerr=e); plt.xticks(x,[r["mix"] for r in rows]); plt.ylabel("Bandwidth (MiB/s)"); plt.title("Mix Sweep — BW"); S(out_bw)
    y=[F(r["latency_us"]) for r in rows]; e=[F(r["latency_us_std"]) for r in rows]
    plt.figure(); plt.bar(x,y,yerr=e); plt.xticks(x,[r["mix"] for r in rows]); plt.ylabel("Latency (µs)"); plt.title("Mix Sweep — Lat"); S(out_lat)

def qd(inp, out_iops, out_lat, out_trade):
    rows=R(inp); rows.sort(key=lambda r:int(r["qd"])); q=[int(r["qd"]) for r in rows]
    I=[F(r["iops"]) for r in rows]; Ie=[F(r["iops_std"]) for r in rows]
    L=[F(r["latency_us"]) for r in rows]; Le=[F(r["latency_us_std"]) for r in rows]
    plt.figure(); plt.errorbar(q,I,yerr=Ie,marker="o"); plt.xlabel("Queue Depth"); plt.ylabel("IOPS"); plt.title("IOPS vs QD"); S(out_iops)
    plt.figure(); plt.errorbar(q,L,yerr=Le,marker="o"); plt.xlabel("Queue Depth"); plt.ylabel("Latency (µs)"); plt.title("Latency vs QD"); S(out_lat)
    plt.figure(); plt.scatter(L,I); plt.xlabel("Latency (µs)"); plt.ylabel("IOPS"); plt.title("Throughput–Latency"); S(out_trade)

def wss(inp, out_bw, out_lat):
    rows=R(inp); rows.sort(key=lambda r:float(r["working_set_gib"])); x=[float(r["working_set_gib"]) for r in rows]
    y=[F(r["bandwidth_mib_s"]) for r in rows]; e=[F(r["bandwidth_mib_s_std"]) for r in rows]
    plt.figure(); plt.errorbar(x,y,yerr=e,marker="o"); plt.xlabel("Working Set (GiB)"); plt.ylabel("Bandwidth (MiB/s)"); plt.title("WSS — BW"); S(out_bw)
    y=[F(r["latency_us"]) for r in rows]; e=[F(r["latency_us_std"]) for r in rows]
    plt.figure(); plt.errorbar(x,y,yerr=e,marker="o"); plt.xlabel("Working Set (GiB)"); plt.ylabel("Latency (µs)"); plt.title("WSS — Lat"); S(out_lat)

def cache(inp, out_bw, out_lat):
    rows=R(inp); rows.sort(key=lambda r:float(r["miss_rate_pct"])); x=[float(r["miss_rate_pct"]) for r in rows]
    y=[F(r["bandwidth_mib_s"]) for r in rows]; e=[F(r["bandwidth_mib_s_std"]) for r in rows]
    plt.figure(); plt.errorbar(x,y,yerr=e,marker="o"); plt.xlabel("Miss Rate (%)"); plt.ylabel("Bandwidth (MiB/s)"); plt.title("Cache-Miss — BW"); S(out_bw)
    y=[F(r["latency_us"]) for r in rows]; e=[F(r["latency_us_std"]) for r in rows]
    plt.figure(); plt.errorbar(x,y,yerr=e,marker="o"); plt.xlabel("Miss Rate (%)"); plt.ylabel("Latency (µs)"); plt.title("Cache-Miss — Lat"); S(out_lat)

def tlb(inp, out_bw, out_lat):
    rows=R(inp); rows.sort(key=lambda r:float(r["stride_kib"])); x=[float(r["stride_kib"]) for r in rows]
    y=[F(r["bandwidth_mib_s"]) for r in rows]; e=[F(r["bandwidth_mib_s_std"]) for r in rows]
    plt.figure(); plt.errorbar(x,y,yerr=e,marker="o"); plt.xlabel("Stride (KiB)"); plt.ylabel("Bandwidth (MiB/s)"); plt.title("TLB — BW"); S(out_bw)
    y=[F(r["latency_us"]) for r in rows]; e=[F(r["latency_us_std"]) for r in rows]
    plt.figure(); plt.errorbar(x,y,yerr=e,marker="o"); plt.xlabel("Stride (KiB)"); plt.ylabel("Latency (µs)"); plt.title("TLB — Lat"); S(out_lat)

if __name__ == "__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--data", default="data"); a.add_argument("--out", default="figures"); A=a.parse_args()
    zeroq(os.path.join(A.data,"zero_queue.csv"), os.path.join(A.out,"zeroqueue_bars.png"))
    gran(os.path.join(A.data,"granularity_matrix.csv"), os.path.join(A.out,"granularity_bw.png"), os.path.join(A.out,"granularity_lat.png"))
    mix(os.path.join(A.data,"mix_sweep.csv"), os.path.join(A.out,"mix_bw.png"), os.path.join(A.out,"mix_lat.png"))
    qd(os.path.join(A.data,"qd_tradeoff.csv"), os.path.join(A.out,"qd_iops.png"), os.path.join(A.out,"qd_lat.png"), os.path.join(A.out,"qd_tradeoff.png"))
    wss(os.path.join(A.data,"working_set_sizes.csv"), os.path.join(A.out,"wss_bw.png"), os.path.join(A.out,"wss_lat.png"))
    cache(os.path.join(A.data,"impact_cache.csv"), os.path.join(A.out,"cache_bw.png"), os.path.join(A.out,"cache_lat.png"))
    tlb(os.path.join(A.data,"impact_tlb.csv"), os.path.join(A.out,"tlb_bw.png"), os.path.join(A.out,"tlb_lat.png"))

# === Added panels for block-size & tails ===

import os, csv
import matplotlib.pyplot as plt

def R(p): 
    with open(p, newline="") as f: 
        return list(csv.DictReader(f))

def F(x): 
    try: return float(x)
    except: return None

def S(p): 
    os.makedirs(os.path.dirname(p), exist_ok=True); 
    plt.tight_layout(); plt.savefig(p, dpi=150); plt.close()

def vlines_for_bs():
    # 64KiB and 128KiB markers
    for x in [65536, 131072]:
        plt.axvline(x, linestyle="--", linewidth=1)

def bs_panels(inp_csv, out_iops_mbps, out_lat):
    rows = R(inp_csv)
    rows.sort(key=lambda r:int(r["bs_bytes"]))
    x = [int(r["bs_bytes"]) for r in rows]
    iops = [F(r["iops"]) for r in rows]
    mbps = [F(r["mbps"]) for r in rows]
    lat = [F(r["lat_us"]) for r in rows]

    # IOPS/MBps panel (two separate y-axes would be dual-axis; we use two charts per rubric allowance)
    plt.figure()
    plt.plot(x, iops, marker="o")
    vlines_for_bs()
    plt.xlabel("Block Size (bytes)")
    plt.ylabel("IOPS")
    plt.title("Block Size Sweep — IOPS")
    plt.xscale("log")
    S(out_iops_mbps.replace(".png","_iops.png"))

    plt.figure()
    plt.plot(x, mbps, marker="o")
    vlines_for_bs()
    plt.xlabel("Block Size (bytes)")
    plt.ylabel("Throughput (MB/s)")
    plt.title("Block Size Sweep — MB/s")
    plt.xscale("log")
    S(out_iops_mbps.replace(".png","_mbps.png"))

    # Latency panel
    plt.figure()
    plt.plot(x, lat, marker="o")
    vlines_for_bs()
    plt.xlabel("Block Size (bytes)")
    plt.ylabel("Avg Latency (µs)")
    plt.title("Block Size Sweep — Latency")
    plt.xscale("log")
    S(out_lat)

def tails(inp_csv, outprefix):
    rows = R(inp_csv)
    rows.sort(key=lambda r:int(r["qd"]))
    qd = [int(r["qd"]) for r in rows]
    p50 = [F(r["p50_us"]) for r in rows]
    p95 = [F(r["p95_us"]) for r in rows]
    p99 = [F(r["p99_us"]) for r in rows]
    p999= [F(r["p999_us"]) for r in rows]

    # one chart per percentile set (bar grouped by QD)
    for name, series in [("p50",p50),("p95",p95),("p99",p99),("p999",p999)]:
        plt.figure()
        plt.bar(range(len(qd)), series)
        plt.xticks(range(len(qd)), [str(q) for q in qd])
        plt.xlabel("Queue Depth")
        plt.ylabel("Latency (µs)")
        plt.title(f"Tail Latency — {name.upper()}")
        S(f"{outprefix}_{name}.png")

# Generate the new panels immediately when called as a script
if __name__ == "__main__":
    try:
        bs_panels(os.path.join(A.data,"bs_random.csv"), os.path.join(A.out,"bs_random.png"), os.path.join(A.out,"bs_random_lat.png"))
        bs_panels(os.path.join(A.data,"bs_seq.csv"),    os.path.join(A.out,"bs_seq.png"),    os.path.join(A.out,"bs_seq_lat.png"))
        tails(os.path.join(A.data,"tails.csv"), os.path.join(A.out,"tails"))
    except Exception as e:
        pass
