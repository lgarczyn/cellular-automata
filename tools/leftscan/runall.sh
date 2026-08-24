#!/bin/bash
cd /var/tmp/collatz-scratch/leftscan
# exhaustive 32-bit: [2^31, 2^32), 16 shards
LO=2147483648; HI=4294967296; N=16
STEP=$(( (HI-LO)/N ))
for i in $(seq 0 $((N-1))); do
  A=$((LO + i*STEP)); B=$((A + STEP))
  ./leftscan exh $A $B 40 20.85 19.97 22.57 5.69 exh32_$i.txt &
done
wait
echo "exh32 done: $(cat exh32_*.txt | wc -l) hits" > progress.txt
# random 64-bit: 2e9 total, 16 shards
for i in $(seq 0 $((N-1))); do
  ./leftscan rand 60 125000000 $((999 + i)) 22.04 19.97 24.40 5.77 r64_$i.txt &
done
wait
echo "all done: exh32 $(cat exh32_*.txt | wc -l) hits, r64 $(cat r64_*.txt | wc -l) hits" > progress.txt
