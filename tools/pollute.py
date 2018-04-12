#!/usr/bin/python

import sys
import getopt
import random


def pollute(inputfile, outputfile, chunk_size, attackers_number,
            team_size, mode):
    team = list(range(0, team_size))
    attackers = random.sample(team, attackers_number)
    last_chunk = b'\x00'*chunk_size
    print("Lost chunks for every round:", attackers)
    i = 0
    with open(inputfile, 'rb') as fi:
        with open(outputfile, 'wb') as fo:
            while True:
                chunk = fi.read(chunk_size)
                if chunk:
                    if team[i] in attackers:
                        if mode == 0:
                            # Writing zeros instead of the chunk
                            fo.write(b'\x00'*chunk_size)
                        elif mode == 1:
                            # Writing the last valid chunk
                            fo.write(last_chunk)
                        else:
                            # Writing nothing
                            pass
                    else:
                        fo.write(chunk)
                        last_chunk = chunk
                else:
                    break
                i = (i+1) % team_size


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:c:a:n:m:",
                                   ["ifile=", "ofile=", "csize=",
                                    "attackers_number=", "tsize=", "mode="])
    except getopt.GetoptError:
        print("pollute.py -i <inputfile> -o <outputfile> -c <chunk_size> \
              -a <number_of_attackers> -n <team_size> -m <mode>")
        sys.exit(2)
    inputfile = ""
    outputfile = ""
    chunk_size = 1024
    attackers_number = 0
    team_size = 10
    for opt, arg in opts:
        if opt == '-h':
            print("pollute.py -i <inputfile> -o <outputfile> -c <chunk_size> \
                  -a <number_of_attackers> -n <team_size> -m <mode>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-c", "--csize"):
            chunk_size = int(arg)
        elif opt in ("-a", "--attackers"):
            attackers_number = int(arg)
        elif opt in ("-n", "--tsize"):
            team_size = int(arg)
        elif opt in ("-m", "--mode"):
            mode = int(arg)

    pollute(inputfile, outputfile, chunk_size, attackers_number,
            team_size, mode)


if __name__ == "__main__":
    main()
