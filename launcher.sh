#!/bin/bash


# Useful stuff for debugging:
# ./test.me 2>&1 | grep inserted | grep chunk

#rm -f *udp *tcp #removal trash files
exe="python3 -u src/simulator.py run --set_of_rules $1 --number_of_monitors $2 --number_of_peers $3 --number_of_rounds $4 --drawing_log $HOME/$5"

if [ $6 -eq 1 ]
then
    $exe --gui
else
    $exe
fi

rm -f *udp *tcp #removal trash files
