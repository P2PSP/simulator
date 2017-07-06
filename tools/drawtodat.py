#!/usr/bin/python

import sys
import getopt


def main(argv):
    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print("drawtodat.py -i <inputfile> -o <outputfile>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("drawtodat.py -i <inputfile> -o <outputfile>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
            
    drawing_log_file = open(self.drawing_log, "r")
    line = drawing_log_file.readline()
    while line != "Bye":
        m = line.strip().split(";",4)
        if m[0] == "T":
            
            
if __name__ == "__main__":
   main(sys.argv[1:])
