#!/usr/bin/env python3
import os, csv, subprocess, datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

OUT_DIR = "results"
CSV_PATH = os.path.join(OUT_DIR, "results.csv")
PDF_PATH = os.path.join(OUT_DIR, "report.pdf")

PLOTS = [
    ("CPU Affinity", "affinity_runtime.png"),
    ("SMT Interference Proxy", "smt_proxy_runtime.png"),
    ("MMU / Stride Sensitivity", "mmu_stride_touches.png"),
    ("Prefetcher Effect", "prefetch_accesses.png"),
]

def sh(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as e:
        return f"NA ({e})"

def read_csv_text(limit=12):
    if not os.path.exists(CSV_PATH):
        return "results.csv not found (run scripts/run_collect.py first)"
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        lines = []
        for i, line in enumerate(f):
            lines.append(line.rstrip("\n"))
            if i >= limit:
                break
    return "\n".join(lines)

def add_wrapped(c, text, x, y, width, leading=12):
    import textwrap
    for line in text.split("\n"):
        wrapped = textwrap.wrap(line, width=int(width/6.2)) or [""]
        for wline in wrapped:
            c.drawString(x, y, wline)
            y -= leading
    return y

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    c = canvas.Canvas(PDF_PATH, pagesize=letter)
    W, H = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, H-1*inch, "ECSE 4320/6320 Project A1: Advanced OS and CPU Feature Exploration")
    c.setFont("Helvetica", 11)
    c.drawString(1*inch, H-1.25*inch, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(1*inch, H-1.45*inch, "Environment summary (auto-collected; edit README for full details):")

    env = {
        "uname": sh(["uname","-a"]),
        "lscpu": sh(["bash","-lc","lscpu | sed -n '1,25p'"]),
        "wsl": sh(["bash","-lc","grep -i microsoft /proc/version || true"]),
        "perf": sh(["bash","-lc","perf --version 2>/dev/null || echo NA"]),
        "compiler": sh(["bash","-lc","g++ --version | head -n 1"]),
    }

    y = H-1.7*inch
    c.setFont("Helvetica", 9.5)
    y = add_wrapped(c, "uname:\n"+env["uname"], 1*inch, y, W-2*inch, leading=11)
    y -= 6
    y = add_wrapped(c, "lscpu (top):\n"+env["lscpu"], 1*inch, y, W-2*inch, leading=11)
    y -= 6
    y = add_wrapped(c, "WSL indicator:\n"+(env["wsl"] or "NA"), 1*inch, y, W-2*inch, leading=11)
    y -= 6
    y = add_wrapped(c, "perf:\n"+env["perf"], 1*inch, y, W-2*inch, leading=11)
    y -= 6
    y = add_wrapped(c, "compiler:\n"+env["compiler"], 1*inch, y, W-2*inch, leading=11)

    c.showPage()

    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, H-1*inch, "Methodology")
    c.setFont("Helvetica", 10.5)
    method = (
        "We implemented microbenchmarks targeting four OS/CPU features and executed each configuration "
        "multiple times to reduce noise. We report mean and standard deviation for runtime or throughput.\n\n"
        "WSL Notes: Under WSL2, some perf hardware events (e.g., LLC-load-misses) may be unavailable. "
        "This report records cycles when supported and documents unsupported events as NA. "
        "Where CPU affinity is not honored, the benchmark prints a warning."
    )
    y = H-1.3*inch
    y = add_wrapped(c, method, 1*inch, y, W-2*inch, leading=13)

    c.setFont("Helvetica-Bold", 12)
    y -= 10
    c.drawString(1*inch, y, "Raw results CSV (preview)")
    y -= 14
    c.setFont("Courier", 8.5)
    y = add_wrapped(c, read_csv_text(), 1*inch, y, W-2*inch, leading=10)

    c.showPage()

    for title, fname in PLOTS:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1*inch, H-1*inch, f"Results: {title}")
        img_path = os.path.join(OUT_DIR, fname)
        c.setFont("Helvetica", 10)
        if not os.path.exists(img_path):
            c.drawString(1*inch, H-1.3*inch, f"Missing figure {fname}. Run scripts/plot.py first.")
            c.showPage()
            continue

        img = ImageReader(img_path)
        iw, ih = img.getSize()
        max_w = W - 2*inch
        max_h = H - 2.2*inch
        scale = min(max_w/iw, max_h/ih)
        draw_w = iw*scale
        draw_h = ih*scale
        x = (W - draw_w)/2
        y = (H - 1.4*inch) - draw_h
        c.drawImage(img, x, y, width=draw_w, height=draw_h, preserveAspectRatio=True, mask='auto')

        c.setFont("Helvetica", 10.5)
        cap_y = y - 0.4*inch
        caption = (
            "Caption guidance: state the independent variable(s), dependent metric, and the key effect. "
            "Tie the trend to OS/CPU mechanisms (contention, scheduling, TLB pressure, prefetch efficiency)."
        )
        add_wrapped(c, caption, 1*inch, cap_y, W-2*inch, leading=12)

        c.showPage()

    c.save()
    print(f"Wrote {PDF_PATH}")

if __name__ == "__main__":
    main()
