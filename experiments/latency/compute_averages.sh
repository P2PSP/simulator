#! /bin/bash

SOR=$1

printf "#B\tCLR\n"

B=200
N=100
STEP=10
while [ $B -ge 1 ]; do
    echo B=$B >&2
    average=`python3 ../average.py < peers_${N}__buffer_size_${B}__${SOR}.txt | grep "average" | cut -d "=" -f 2`
    printf $B
    printf "\t"
    printf $average
    printf "\n"
    let B=B-$STEP
done
