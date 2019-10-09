###!/usr/bin/python3

import sys

counter = 0
sum = 0.0
for line in sys.stdin:
    try:
        number = float(line.strip())
    except ValueError:
        sys.stderr.write(f"ValueError exception: line={line}\n")
        number = 0.0
    #print(f"{number}")
    sum += number
    counter += 1
try:
    average = sum/counter
except ZeroDivisionError:
    average = 0.0

sys.stdout.write(f"average={average}\n")
