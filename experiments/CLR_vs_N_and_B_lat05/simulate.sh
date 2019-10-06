#! /bin/bash

# This generates a single sample for all the peers of the team

STEP=1

N=100 # Max team size
while [ $N -gt 10 ]; do
    #echo N=$N
    B=400 # Buffer size
    while [ $B -gt 20 ]; do
	#echo B=$B
	min_buff_size=`echo $N*2 | bc`
	max_buff_size=`echo $N*4 | bc`
	if [ $B -ge $min_buff_size ] && [ $B -le $max_buff_size ]; then
	    echo $N $B
	    time python3 ../../src/simulator.py run --loglevel INFO --number_of_peers $N --buffer_size $B --number_of_rounds 10 | grep "CLR" | awk '{match($0,/CLR=[0-9.]+/);A=substr($0,RSTART,RLENGTH);sub(/.*=/,X,A);print A}' >>  peers_${N}__buffer_size_${B}.txt
	    #python3 ../../src/simulator.py run --loglevel DEBUG --number_of_peers $N --buffer_size $B --number_of_rounds 100 | grep "CLR" 
	fi
	let B=B-$STEP
    done
    let N=N-$STEP
done
