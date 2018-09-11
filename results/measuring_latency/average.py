#!/usr/bin/python

import sys, getopt

points = 100
experiments = 10
directory = "flash_crowd/"
basename = "mcast"

try:
    opts, args = getopt.getopt(sys.argv[1:],"p:e:d:b:h",["points=","experiments=","directory=","basename="])
except getopt.GetoptError:
    print ('average.py -p <points> -e <experiments> -d <directory> -b <basename>')
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print ('average.py -p <points> -e <experiments> -d <directory> -b <basename>')
        print ('<points>      =', points)
        print ('<experiments> =', experiments)
        print ('<directory>   =', directory)
        print ('<base name>   =', basename )
        sys.exit()
    elif opt in ("-p", "--points"):
        points = int(arg)
    elif opt in ("-e", "--experiments"):
        experiments = int(arg)
    elif opt in ("-d", "--directory"):
        directory = arg
    elif opt in ("-b", "--basename"):
        basename = arg

f = {} # File descriptors

# Open the input files
for e in range(0, experiments):
    print (e)
    f[e] = open(directory + basename + ("%02d" % e) + ".dat", 'r')

# The output file
o = open(directory + "average_" + basename + ".dat", 'w')

for p in range(0, points):
    sum = 0
    for e in range(0, experiments):
        line = f[e].readline()
        num_sample, sample = line.split()
        sum += float(sample)
    average = sum/experiments

    o.write(str(p+1) + '\t' + str(average) + '\n')

o.close()
