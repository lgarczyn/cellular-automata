#!/bin/bash
cd /var/tmp/collatz-scratch/monster
# 12 rounds; per round: 48/16 x5 procs, 64/32 x5, 80/48 x6
for R in $(seq 1 12); do
  for i in 0 1 2 3 4; do
    ./monster2 48 16 2000000000 $((48160000 + R*1000 + i)) "48_16_$i" &
  done
  for i in 0 1 2 3 4; do
    ./monster2 64 32 1500000000 $((64320000 + R*1000 + i)) "64_32_$i" &
  done
  for i in 0 1 2 3 4 5; do
    ./monster2 80 48 1100000000 $((80480000 + R*1000 + i)) "80_48_$i" &
  done
  wait
  echo "round $R done $(date)" >> rounds.log
done
echo ALLDONE >> rounds.log
