#!/bin/bash
set -e
mkdir -p results

KEYS=${KEYS:-100000}
OPS=${OPS:-500000}

for t in 1 2 4 8 16; do
  echo "=== coarse t=$t ==="
  perf stat -e cycles,LLC-load-misses,LLC-store-misses \
    ./bench --mode coarse --workload lookup --keys $KEYS --threads $t --ops $OPS \
    2> results/perf_coarse_t${t}.txt | tee results/out_coarse_t${t}.txt

  echo "=== striped t=$t ==="
  perf stat -e cycles,LLC-load-misses,LLC-store-misses \
    ./bench --mode striped --workload lookup --keys $KEYS --threads $t --ops $OPS \
    2> results/perf_striped_t${t}.txt | tee results/out_striped_t${t}.txt
done
