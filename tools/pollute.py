#!/usr/bin/python

import sys
import getopt


def pollute(inputfile, outputfile, chunk_size=1024, attackers=0, team_size=10):
    with open(inputfile, 'rb') as fi:
        with open(outputfile, 'wb') as fo:
            while True:
                chunk = fi.read(chunk_size)
                if chunk:
                    fo.write(chunk)
                else:
                    break


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print("pollute.py -i <inputfile> -o <outputfile>")
        sys.exit(2)
    inputfile = ""
    outputfile = ""
    for opt, arg in opts:
        if opt == '-h':
            print("pollute.py -i <inputfile> -o <outputfile>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
    print("Input file is", inputfile)
    print("Output file is", outputfile)

    pollute(inputfile, outputfile)


if __name__ == "__main__":
    main()
