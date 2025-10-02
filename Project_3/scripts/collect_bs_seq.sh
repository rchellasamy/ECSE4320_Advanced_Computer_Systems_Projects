#!/usr/bin/env bash
set -euo pipefail
mkdir -p results
for bs in 4k 16k 64k 128k 256k; do
  fio --name=bs_seq_${bs} --rw=read --bs=${bs} --iodepth=1 --time_based=1 --runtime=30s --numjobs=1 --direct=1 --ioengine=psync --output-format=json --output=results/bs_seq_${bs}.json
done
