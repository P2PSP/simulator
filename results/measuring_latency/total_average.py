#!/usr/bin/python

import sys, getopt

points = 100
directory = "flash_crowd/"
basename = "mcast"

try:
    opts, args = getopt.getopt(sys.argv[1:],"p:d:b:h",["points=","directory=","basename="])
except getopt.GetoptError:
    print ('total_average.py -p <points> -d <directory> -b <basename>')
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print ('total_average.py -p <points> -d <directory> -b <basename>')
        print ('<points>      =', points)
        print ('<directory>   =', directory)
        print ('<base name>   =', basename )
        sys.exit()
    elif opt in ("-p", "--points"):
        points = int(arg)
    elif opt in ("-d", "--directory"):
        directory = arg
    elif opt in ("-b", "--basename"):
        basename = arg

# The input file with the average of each number of peer
i = open(directory + "average_" + basename + ".dat", 'r')
o = open(directory + "total_average_" + basename + ".dat", 'w')

sum = 0
for p in range(0, points):
    line = i.readline()
    num_sample, sample = line.split()
    sum += float(sample)
    
average = sum/points

o.write(str("%.3f" % average) + '\n')
o.close()
