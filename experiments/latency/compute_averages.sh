#! /bin/bash

file=$1
average=`python3 ../average.py < $file | grep "average" | cut -d "=" -f 2`
printf $file
printf "\t"
printf $average
printf "\n"
