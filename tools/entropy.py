#!/usr/bin/env python

#import numpy as np
#import scipy.stats as sc
import math
import sys

#range = int(sys.argv[2])
#x = range*[0]
dict = {}
counter = 0

input = sys.argv[1]
with open(input) as f:
    for line in f:
        value = int(line)
        if value not in dict:
            dict[value] = 1
        else:
            dict[value] += 1
        counter += 1
sys.stderr.write("read " + str(counter) + " values\n")
        
total = 0
for key, value in dict.items():
    sys.stderr.write(str(key) + " " + str(value) + "\n")
    total += value
sys.stderr.write("total=" + str(total) + "\n")
    
for x in dict:
    dict[x] /= 1.*counter

entropy = 0.0
for x in dict:
    entropy += dict[x] * math.log(dict[x])/math.log(2.0)
entropy = -entropy

#print(sc.entropy(x))
print(entropy)


