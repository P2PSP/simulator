"""
@package simulator
peer_dbs_simulator module
"""

# Specific simulator behavior. In the simulator, peers do not play
# the stream.

import time
import sys
import struct
import random
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
#from .simulator_stuff import Simulator_socket as socket
from .socket_wrapper import Socket_wrapper as socket
from .simulator_stuff import hash
from .peer_dbs import Peer_DBS
import logging
#import colorama
from .chunk_structure import ChunkStructure
from .ip_tools import IP_tools
from .messages import Messages
import core.stderr as stderr

class Peer_DBS_simulator(Peer_DBS):

    def __init__(self, id, name = "Peer_DBS_simulator"):
        super().__init__()
#        self.chunk_packet_format = "!isIii"
        self.lg.debug(f"{name}: DBS simulator initialized")

    def receive_the_chunk_size(self):
        pass

    def packet_format(self):
        self.chunk_packet_format = "!isIiid"

    def clear_entry_in_buffer(self, buffer_box):
        #return [buffer_box[ChunkStructure.CHUNK_NUMBER], b'L', buffer_box[ChunkStructure.ORIGIN_ADDR], buffer_box[ChunkStructure.ORIGIN_PORT], buffer_box[ChunkStructure.HOPS]]
        return self.empty_entry_in_buffer()

    def empty_entry_in_buffer(self):
        return [-1, b'L', None, 0, 0]

    def process_chunk(self, chunk, sender):
        super().process_chunk(chunk, sender)
        transmission_time = time.time() - chunk[ChunkStructure.TIME]
        #stderr.write(f" {transmission_time:.2}")
        self.lg.debug(f"{self.ext_id}: transmission time={transmission_time}")
