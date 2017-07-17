#!/usr/bin/python

import sys
import getopt
import os

def main(argv):
    inputfile = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["ifile="])
    except getopt.GetoptError:
        print("drawtodat.py -i <inputfile>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("drawtodat.py -i <inputfile>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg

    filename = os.path.basename(inputfile)

    draw_log_file = open(inputfile, "r")
    team_log_file = open(filename+".team", "w", 1)
    buffer_log_file = open(filename+".buffer", "w", 1)

    team_log_file.write("Round\tTPs\tWIPs\tMPs")
    buffer_log_file.write("Round\tCLR")

    clr = 0
    number_of_peers = 0
    line = draw_log_file.readline()
    while line != "Bye":
        m = line.strip().split(";", 4)
        if m[0] == "R":
            team_log_file.write('\n' + m[1] + '\t')
            if number_of_peers > 0:
                mean_clr = clr/number_of_peers
            else:
                mean_clr = 0
            buffer_log_file.write('\n' + m[1] + '\t' + str(mean_clr))
            clr = 0
            number_of_peers = 0

        if m[0] == "T" and m[1] == "M":
            team_log_file.write(m[2] + '\t')

        if m[0] == "T" and m[1] == "P":
            team_log_file.write(m[2] + '\t')

        if m[0] == "T" and m[1] == "MP":
            team_log_file.write(m[2])

        if m[0] == "CLR":
            if "MP" not in m[1]:
                clr += float(m[2])
                number_of_peers += 1

        line = draw_log_file.readline()


if __name__ == "__main__":
   main(sys.argv[1:])
