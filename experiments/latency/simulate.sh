#! /bin/bash

N=7   # Number of peers (monitor apart)
B=32  # Buffer size
R=100 # Number of rounds

time python3 ../../src/simulator.py run --set_of_rules DBS --number_of_peers $N --buffer_size $B --number_of_rounds $R | grep "time" | awk '{match($0,/time=[0-9.]+/);A=substr($0,RSTART,RLENGTH);sub(/.*=/,X,A);print A}' >> $N_$B_DBS.txt

time python3 ../../src/simulator.py run --set_of_rules DBS2 --number_of_peers $N --buffer_size $B --number_of_rounds $R | grep "time" | awk '{match($0,/time=[0-9.]+/);A=substr($0,RSTART,RLENGTH);sub(/.*=/,X,A);print A}' >> $N_$B_DBS2.txt

time python3 ../../src/simulator.py run --set_of_rules DBS3 --number_of_peers $N --buffer_size $B --number_of_rounds $R | grep "time" | awk '{match($0,/time=[0-9.]+/);A=substr($0,RSTART,RLENGTH);sub(/.*=/,X,A);print A}' >> $N_$B_DBS3.txt

