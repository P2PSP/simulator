"""
@package simulator
peer_dbs_simulator module
"""

# Specific simulator behavior.

import sys
import struct
import random
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
#from .simulator_stuff import Simulator_socket as socket
from .socket_wrapper import Socket_wrapper as socket
from .simulator_stuff import hash
from .peer_dbs2 import Peer_DBS2
from .peer_dbs_simulator import Peer_DBS_simulator
import logging
from .chunk_structure import ChunkStructure

class Peer_DBS2_simulator(Peer_DBS2, Peer_DBS_simulator):

    def __init__(self, id, name = "Peer_DBS2_simulator", loglevel=logging.ERROR):
        Peer_DBS2.__init__(self)
        Peer_DBS_simulator.__init__(self, id, name, loglevel)
        self.lg = logging.getLogger(name)
        self.lg.setLevel(loglevel)
        self.name = name
        #colorama.init()
        self.lg.info(f"{name}: DBS2 initialized")

    def request_chunk(self, chunk_number, peer):
        self.lg.info(f"{self.ext_id}: sent [request {chunk_number}] to {peer}")
        super().request_chunk(chunk_number, peer)

    def process_request(self, chunk_number, sender):
        self.lg.info(f"{self.ext_id}: received [request {chunk_number}] from {sender}")
        super().process_request(chunk_number, sender)
        
    def play_chunk__show_buffer(self):
        #sys.stderr.write(f" {len(self.forward)}"); sys.stderr.flush()
        if __debug__:
            buf = ""
            for i in self.buffer:
                if i[ChunkStructure.CHUNK_DATA] != b'L':
                    try:
                        _origin = list(self.team).index(i[ChunkStructure.ORIGIN])
                        buf += hash(_origin)
                    except ValueError:
                        buf += '-' # Peers do not exist in their forwarding table.
                else:
                    buf += " "
            self.lg.debug(f"{self.ext_id}: buffer={buf}")
