import sys

def write(*msg):
    sys.stderr.write(msg[0]); sys.stderr.flush()
