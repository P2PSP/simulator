#!/usr/bin/env python

import sys

input = sys.argv[1]

counter = 0
total = 0
with open(input) as f:
    for line in f:
        total += float(line)
        counter += 1
average = total/counter
print(average)
