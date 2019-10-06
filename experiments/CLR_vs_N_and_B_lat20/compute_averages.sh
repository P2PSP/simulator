#! /bin/bash

printf "# N*\tB\tCLR\n"

N=10
STEP=1
while [  $N -le 100 ]; do
    echo N=$N >&2
    B=20 # Buffer size
    while [ $B -le 600 ]; do
	echo B=$B >&2
	if [ -f peers_${N}__buffer_size_${B}.txt ]; then
	    average=`python3 ../average.py < peers_${N}__buffer_size_${B}.txt | grep "average" | cut -d "=" -f 2`
	else
	    average=NaN
	fi
	printf $N
	printf "\t"
	printf $B
	printf "\t"
	#echo $average
	printf $average
	printf "\n"
	let B=B+$STEP
    done
    let N=N+$STEP
done
