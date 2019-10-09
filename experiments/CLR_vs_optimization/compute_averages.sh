#! /bin/bash

printf "#B\tCLR\n"

B=1000
N=100
STEP=10
while [ $B -ge 1 ]; do
    echo B=$B >&2
    average=`python3 ../../tools/average.py < peers_${N}__buffer_size_${B}_DBS.txt | grep "average" | cut -d "=" -f 2`
    printf $B
    printf "\t"
    printf $average
    printf "\n"
    let B=B-$STEP
done
