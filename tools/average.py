#!/usr/bin/env python

import sys

input = sys.argv[1]

counter = 0
total = 0
with open(input) as f:
    for line in f:
        try:
            total += float(line)
            counter += 1
        except:
            sys.stderr.write("unable to convert sample " + str(counter) + "\n")
            continue
        
average = total/counter
print(average)
sys.stderr.write("number of samples = " + str(counter) + "\n")
