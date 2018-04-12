#!/usr/bin/python

import sys
import getopt
import random


def pollute(inputfile, outputfile, chunk_size, mps, team_size):
    team = list(range(0, team_size))
    attackers = random.sample(team, mps)
    print("Lost chunks for every round:", attackers)
    i = 0
    with open(inputfile, 'rb') as fi:
        with open(outputfile, 'wb') as fo:
            while True:
                chunk = fi.read(chunk_size)
                if chunk:
                    if team[i] in attackers:
                        fo.write(b'\x00'*chunk_size)
                    else:
                        fo.write(chunk)
                else:
                    break
                i = (i+1) % team_size


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:c:m:n:", ["ifile=", "ofile=", "csize=", "mps=", "tsize="])
    except getopt.GetoptError:
        print("pollute.py -i <inputfile> -o <outputfile> -c <chunk_size> -m <number_of_malicious> -n <team_size>")
        sys.exit(2)
    inputfile = ""
    outputfile = ""
    chunk_size = 1024
    mps = 0
    team_size = 10
    for opt, arg in opts:
        if opt == '-h':
            print("pollute.py -i <inputfile> -o <outputfile> -c <chunk_size> -m <number_of_malicious> -n <team_size>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-c", "--csize"):
            chunk_size = int(arg)
        elif opt in ("-m", "--mps"):
            mps = int(arg)
        elif opt in ("-n", "--tsize"):
            team_size = int(arg)

    pollute(inputfile, outputfile, chunk_size, mps, team_size)


if __name__ == "__main__":
    main()
