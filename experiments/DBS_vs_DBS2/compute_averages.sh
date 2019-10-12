#! /bin/bash

SOR=$1 # Set Of Rules
B2=$2  # Max buffer size 
B1=$3  # Min buffer size
N=$4   # Num peers
STEP=1

printf "#B\tCLR\n"
while [ $B2 -ge $B1 ]; do
    echo B2=$B2 >&2
    average=`python3 ../average.py < peers_${N}__buffer_size_${B2}__${SOR}.txt | grep "average" | cut -d "=" -f 2`
    printf $B2
    printf "\t"
    printf $average
    printf "\n"
    let B2=B2-$STEP
done
