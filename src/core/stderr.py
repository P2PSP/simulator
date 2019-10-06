import sys

def write(*msg):
    sys.stderr.write(msg); sys.stderr.flush()
