#! /bin/bash

N=9  # Monitor apart
let P=N+1
R=100
STEP=1

B2=40
B1=20
while [ $B2 -gt 1 ]; do
    echo peers_${P}__buffer_size_${B2}__DBS.txt
    time python3 ../../src/simulator.py run --set_of_rules DBS --number_of_peers $N --buffer_size $B2 --number_of_rounds $R --max_chunk_loss_at_peers 10000 --max_chunk_loss_at_splitter 10000 | grep "CLR" | awk '{match($0,/CLR=[0-9.]+/);A=substr($0,RSTART,RLENGTH);sub(/.*=/,X,A);print A}' >> peers_${P}__buffer_size_${B2}__DBS.txt
    let B2=B2-$STEP
done

B2=40
B1=20
while [ $B2 -gt $B1 ]; do
    echo peers_${P}__buffer_size_${B2}__DBS2.txt
    time python3 ../../src/simulator.py run --set_of_rules DBS2 --number_of_peers $N --buffer_size $B2 --number_of_rounds $R --max_chunk_loss_at_peers 10000 --max_chunk_loss_at_splitter 10000 | grep "CLR" | awk '{match($0,/CLR=[0-9.]+/);A=substr($0,RSTART,RLENGTH);sub(/.*=/,X,A);print A}' >> peers_${P}__buffer_size_${B}__DBS2.txt
    let B2=B2-$STEP
done
