#!/bin/bash
set -e
make clean && make
python3 scripts/run_collect.py
python3 scripts/plot.py
python3 scripts/generate_report.py
echo "Done. See results/ for CSV, plots, and report.pdf"
