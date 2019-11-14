#! /bin/bash

N=$1 # 7   # Number of peers (monitor apart)
B=$2 # 32  # Buffer size
R=$3 # 100 # Number of rounds
S=$4 # DBS # Set of rules

set -x
time python3 ../../src/simulator.py run --set_of_rules $S --number_of_peers $N --buffer_size $B --number_of_rounds $R | grep "average_latency" | awk '{match($0,/average_latency=[0-9.]+/);A=substr($0,RSTART,RLENGTH);sub(/.*=/,X,A);print A}' >> $N_$B_$S.txt
set +x
