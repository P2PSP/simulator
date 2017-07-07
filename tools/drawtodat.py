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

    print("inputfile", inputfile)
    draw_log_file = open(inputfile, "r")
    dat_log_file = open(outputfile, "w", 1)

    dat_log_file.write("Round\tTPs\tWIPs\tMPs")

    line = draw_log_file.readline()
    while line != "Bye":
        m = line.strip().split(";", 4)
        if m[0] == "R":
            dat_log_file.write('\n' + m[1] + '\t')

        if m[0] == "T" and m[1] == "M":
            dat_log_file.write(m[2] + '\t')

        if m[0] == "T" and m[1] == "P":
            dat_log_file.write(m[2] + '\t')

        if m[0] == "T" and m[1] == "MP":
            dat_log_file.write(m[2])

        line = draw_log_file.readline()


if __name__ == "__main__":
   main(sys.argv[1:])
