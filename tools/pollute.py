#!/usr/bin/python

import sys
import getopt
import random


HEADER_SIZE = 1024  # In chunks


def pollute(inputfile, outputfile, chunk_size, attackers_number,
            team_size, mode):
    team = list(range(0, team_size))
    attackers = random.sample(team, attackers_number)
    last_valid_chunk = b'\x00'*chunk_size
    number_of_round = -1
    i = 0
    with open(inputfile, 'rb') as fi:
        with open(outputfile, 'wb') as fo:
            while True:
                if i == 0:
                    number_of_round += 1
                chunk = fi.read(chunk_size)
                if chunk:
                    chunk_played = ((number_of_round * team_size) + i)
                    if team[i] in attackers and chunk_played > HEADER_SIZE:
                        if mode == 0:
                            # Writing zeros instead of the chunk
                            fo.write(b'\x00'*chunk_size)
                        elif mode == 1:
                            # Writing the last valid chunk
                            fo.write(last_valid_chunk)
                        else:
                            # Writing nothing
                            pass
                    else:
                        fo.write(chunk)
                        last_valid_chunk = chunk
                else:
                    break
                i = (i+1) % team_size
    # Statistics
    print("Team size: {}".format(team_size))
    print("Number of malicious: {}".format(attackers_number))
    print("Percentage of lost chunks: {} %".format(
        float(attackers_number*100)/team_size)
    )
    print("Malicious peers (lost chunks per round): {}".format(attackers))
    print("Header size (in rounds): {}".format(HEADER_SIZE))
    print("Chunk size: {}".format(chunk_size))
    print("Rounds played:".format(number_of_round))
    print("Chunks played:".format(chunk_played))


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
    mode = 0
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
