#!/usr/bin/env bash
set -euo pipefail
mkdir -p results
for qd in 1 2 4 8 16 32 64 128; do
  fio --name=qd_randread_4k_qd${qd} --rw=randread --bs=4k --iodepth=${qd} --time_based=1 --runtime=30s --numjobs=1 --direct=1 --ioengine=psync --output-format=json --output=results/qd_randread_4k_qd${qd}.json
done
