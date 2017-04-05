"""
@package simulator
common module
"""
class Common():

    MAX_CHUNK_NUMBER = 65536
    COUNTERS_TIMING = 1
    BUFFER_SIZE = 128
    UDP_SOCKETS= {}
    TCP_SOCKETS = {}

    #shared lists between peers
    SHARED_LIST = {}

    #Communication channel with the simulator
    SIMULATOR_FEEDBACK = {}
