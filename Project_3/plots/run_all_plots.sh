#!/usr/bin/env bash
set -euo pipefail
python3 plots/plot_zeroq.py data/zero_queue.csv figures/zeroqueue_bars.png
python3 plots/plot_bs_random.py data/bs_random.csv figures/bs_random.png figures/bs_random_lat.png
python3 plots/plot_bs_seq.py    data/bs_seq.csv    figures/bs_seq.png    figures/bs_seq_lat.png
python3 plots/plot_mix.py       data/mix_sweep.csv figures/mix_bw.png    figures/mix_lat.png
python3 plots/plot_qd.py        data/qd_tradeoff.csv figures/qd_iops.png figures/qd_lat.png figures/qd_tradeoff.png
python3 plots/plot_tails.py     data/tails.csv     figures/tails.png
python3 plots/plot_granularity.py data/granularity_matrix.csv figures/granularity_bw.png figures/granularity_lat.png
python3 plots/plot_wss.py       data/working_set_sizes.csv figures/wss_bw.png figures/wss_lat.png
python3 plots/plot_cache.py     data/impact_cache.csv figures/cache_bw.png figures/cache_lat.png
python3 plots/plot_tlb.py       data/impact_tlb.csv figures/tlb_bw.png figures/tlb_lat.png
