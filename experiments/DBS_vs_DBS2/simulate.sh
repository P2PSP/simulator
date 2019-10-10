#! /bin/bash

N=99  # Monitor apart
let P=N+1
R=200
STEP=10

B=200
while [ $B -gt 1 ]; do
    echo peers_${P}__buffer_size_${B}__DBS.txt
    time python3 ../../src/simulator.py run --set_of_rules DBS --number_of_peers $N --buffer_size $B --number_of_rounds $R --max_chunk_loss_at_peers 10000 --max_chunk_loss_at_splitter 10000 | grep "CLR" | awk '{match($0,/CLR=[0-9.]+/);A=substr($0,RSTART,RLENGTH);sub(/.*=/,X,A);print A}' >> peers_${P}__buffer_size_${B}__DBS.txt
    let B=B-$STEP
done

B=200
while [ $B -gt 1 ]; do
    echo peers_${P}__buffer_size_${B}__DBS2.txt
    time python3 ../../src/simulator.py run --set_of_rules DBS2 --number_of_peers $N --buffer_size $B --number_of_rounds $R --max_chunk_loss_at_peers 10000 --max_chunk_loss_at_splitter 10000 | grep "CLR" | awk '{match($0,/CLR=[0-9.]+/);A=substr($0,RSTART,RLENGTH);sub(/.*=/,X,A);print A}' >> peers_${P}__buffer_size_${B}__DBS2.txt
    let B=B-$STEP
done
