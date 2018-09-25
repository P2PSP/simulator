"""
@package p2psp-simulator
splitter_dbs module
"""

# DBS (Data Broadcasting Set) layer

# DBS is the most basic layer to provide communication among splitter
# (source of the stream) and peers (destination of the stream), using
# unicast transmissions. The splitter sends a different chunk of
# stream to each peer, using a random round-robin scheduler.

# TODO: In each round peers are selected at random, but all peers are
# sent a chunk, in a round).

import time
import struct
import logging
from .simulator_stuff import Simulator_socket as socket
from .splitter_dbs import Splitter_DBS

class Splitter_DBS_latency(Splitter_DBS):

    def send_chunk(self, chunk_msg, peer):
        msg = struct.pack("islif", *chunk_msg)
        self.team_socket.sendto(msg, peer)
        self.lg.debug("{}: chunk {} sent to {}".format(self.id, chunk_msg[0], peer))

    def compose_message(self, chunk, peer):
        return (self.chunk_number, chunk, socket.ip2int(peer[0]),peer[1], time.time())

