#!/usr/bin/env bash
set -euo pipefail
mkdir -p results
for qd in 16 64; do
  fio --name=tails_randread_4k_qd${qd} --rw=randread --bs=4k --iodepth=${qd} --time_based=1 --runtime=30s --numjobs=1 --direct=1 --ioengine=psync --percentile_list=50,95,99,99.9 --output-format=json --output=results/tails_randread_4k_qd${qd}.json
done
