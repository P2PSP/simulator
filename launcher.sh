#!/bin/bash

rm -f *udp *tcp #removal trash files
exe="python3 -u src/simulator.py run --set_of_rules $1 --number-of-monitors $2 --number-of-peers $3 --number-of-rounds $4 --drawing-log $HOME/$5"

if [ $6 -eq 1 ]
then
    $exe --gui
else
    $exe
fi

rm -f *udp *tcp #removal trash files