#!/bin/bash
cd /var/tmp/collatz-scratch/leftscan
run_config () {
  BITS=$1; T=$2; CALN=$3; SCANN=$4; TAG=$5
  for i in $(seq 0 15); do
    ./bigtape calib $BITS $T $CALN $((100 + i)) > cal_${TAG}_$i.txt &
  done
  wait
  read F Tt C V <<< $(cat cal_${TAG}_*.txt | awk '{for(i=1;i<=4;i++) if($i>m[i]) m[i]=$i} END{print m[1], m[2], m[3], m[4]}')
  echo "[$TAG] thresholds: $F $Tt $C $V" >> bigprogress.txt
  for i in $(seq 0 15); do
    ./bigtape scan $BITS $T $SCANN $((7700 + i)) $F $Tt $C $V big_${TAG}_$i.txt &
  done
  wait
  echo "[$TAG] done: $(cat big_${TAG}_*.txt | wc -l) hits from $((SCANN * 16)) seeds" >> bigprogress.txt
}
: > bigprogress.txt
run_config 1024   900 200000 8500000 b1k
run_config 4096  1800  60000 1600000 b4k
run_config 16384 3600  15000  400000 b16k
echo "ALL DONE" >> bigprogress.txt
