#!/bin/bash
cd /var/tmp/collatz-scratch/leftscan
rerun () {
  BITS=$1; T=$2; SCANN=$3; TAG=$4
  read F Tt C V <<< $(cat cal_${TAG}_*.txt | awk '{for(i=1;i<=4;i++) if($i>m[i]) m[i]=$i} END{printf "%.4f %.4f %.4f %.6f", m[1], m[2], m[3], m[4]+0.05}')
  echo "[$TAG] rerun thresholds: $F $Tt $C $V" >> bigprogress.txt
  for i in $(seq 0 15); do
    ./bigtape scan $BITS $T $SCANN $((7700 + i)) $F $Tt $C $V big_${TAG}_$i.txt &
  done
  wait
  echo "[$TAG] rerun done: $(cat big_${TAG}_*.txt | wc -l) hits from $((SCANN * 16)) seeds" >> bigprogress.txt
}
rerun 1024  900 8500000 b1k
rerun 4096 1800 1600000 b4k
echo "RERUN DONE" >> bigprogress.txt
