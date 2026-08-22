#!/bin/bash
cd /var/tmp/collatz-scratch/monster
LO=1073741824; HI=2147483648; N=16
STEP=$(( (HI-LO)/N ))
for CFG in "48 16" "64 32" "80 48"; do
  set -- $CFG; B=$1; J=$2
  for i in $(seq 0 $((N-1))); do
    a=$(( LO + i*STEP )); b=$(( i==N-1 ? HI : LO + (i+1)*STEP ))
    ./exh $B $J $a $b > exh_${B}_${J}_$i.txt &
  done
  wait
  echo "exhaustive $B/$J done $(date)" >> exh.log
done
echo EXHDONE >> exh.log
