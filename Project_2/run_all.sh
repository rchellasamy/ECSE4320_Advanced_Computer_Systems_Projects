#!/usr/bin/env bash
set -euo pipefail
python3 scripts/populate_from_sparse.py
python3 plots/plot_zero_queue.py
python3 plots/plot_granularity.py
python3 plots/plot_tradeoff.py
python3 plots/plot_rw_mix.py
python3 plots/plot_workingset.py
python3 plots/plot_cache_miss.py
python3 plots/plot_tlb.py
echo "All figures written to figures/, CSVs to data/"
